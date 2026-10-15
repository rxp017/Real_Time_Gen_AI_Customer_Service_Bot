"""Bounded structural preflight before any image/PDF decoder, OCR, or model."""

import math
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import PurePath

from core.audit import AuditLogger
from core.config import get_config
from core.security import detect_prompt_injection


class UploadRejected(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class GatedFile:
    mime: str
    width: int | None = None
    height: int | None = None


def bounded_inflate(data: bytes, limit: int) -> bytes:
    decoder = zlib.decompressobj()
    value = decoder.decompress(data, limit + 1)
    if len(value) > limit or decoder.unconsumed_tail:
        raise UploadRejected("decompression_limit")
    if not decoder.eof or decoder.unused_data:
        raise UploadRejected("malformed_compression")
    return value


def check_pixels(width: int, height: int) -> None:
    if width <= 0 or height <= 0 or width * height > int(get_config().get("uploads.max_pixels")):
        raise UploadRejected("pixel_limit")


def check_instruction_bytes(data: bytes) -> None:
    if detect_prompt_injection(data.decode("utf-8", errors="ignore"))[0]:
        raise UploadRejected("prompt_injection")


class UploadGate:
    def __init__(self, audit: AuditLogger) -> None:
        self.audit = audit

    def validate(self, data: bytes, filename: str, declared_mime: str) -> GatedFile:
        cfg = get_config()
        try:
            if not data or len(data) > int(cfg.get("uploads.max_bytes")):
                raise UploadRejected("empty_or_oversize")
            mime = ("image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else
                    "image/jpeg" if data.startswith(b"\xff\xd8\xff") else
                    "application/pdf" if re.match(rb"%PDF-1\.[0-7][\r\n]", data) else "")
            extensions = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}, "application/pdf": {".pdf"}}
            if mime not in cfg.get("uploads.allowed_types") or declared_mime != mime or PurePath(filename).suffix.casefold() not in extensions.get(mime, set()):
                raise UploadRejected("type_or_magic_mismatch")
            if mime == "image/png":
                width, height = self._png(data)
            elif mime == "image/jpeg":
                width, height = self._jpeg(data)
            else:
                self._pdf(data)
                width, height = None, None
        except UploadRejected as exc:
            self.audit.log_security("upload_rejected", "caller", "Upload rejected before content decoding", reason=exc.reason)
            raise
        except (ValueError, struct.error, zlib.error, OverflowError) as exc:
            self.audit.log_security("upload_rejected", "caller", "Malformed file framing", reason="malformed")
            raise UploadRejected("malformed") from exc
        self.audit.log_info("upload_gate_passed", "caller", "Structural preflight passed", mime=mime, size=len(data))
        return GatedFile(mime, width, height)

    def _png(self, data: bytes) -> tuple[int, int]:
        position, compressed = 8, bytearray()
        width = height = expected = 0
        ended = False
        while position < len(data):
            length = struct.unpack_from(">I", data, position)[0]
            kind = data[position + 4:position + 8]
            end = position + 12 + length
            if end > len(data):
                raise UploadRejected("malformed_png")
            chunk = data[position + 8:end - 4]
            if zlib.crc32(kind + chunk) & 0xFFFFFFFF != struct.unpack_from(">I", data, end - 4)[0]:
                raise UploadRejected("png_checksum")
            if position == 8:
                if kind != b"IHDR" or length != 13:
                    raise UploadRejected("malformed_png")
                width, height = struct.unpack_from(">II", chunk)
                check_pixels(width, height)
                bits, color = chunk[8], chunk[9]
                channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
                if channels is None or bits not in (1, 2, 4, 8, 16) or chunk[10:] != b"\x00\x00\x00":
                    raise UploadRejected("unsupported_png_encoding")
                if (color in {2, 4, 6} and bits not in {8, 16}) or (color == 3 and bits == 16):
                    raise UploadRejected("unsupported_png_encoding")
                expected = height * (1 + (width * channels * bits + 7) // 8)
            elif kind == b"IHDR":
                raise UploadRejected("malformed_png")
            if kind not in {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND", b"pHYs", b"sRGB", b"gAMA", b"cHRM", b"sBIT", b"tIME", b"tEXt"}:
                raise UploadRejected("unsupported_png_metadata_or_animation")
            if kind == b"IDAT":
                compressed.extend(chunk)
            elif kind == b"tEXt":
                check_instruction_bytes(chunk)
            elif kind == b"IEND":
                if length != 0 or end != len(data):
                    raise UploadRejected("trailing_png_data")
                ended = True
            position = end
        if not ended or not compressed:
            raise UploadRejected("malformed_png")
        decoded = bounded_inflate(bytes(compressed), min(expected, int(get_config().get("uploads.max_expanded_bytes"))))
        if len(decoded) != expected:
            raise UploadRejected("png_pixel_data_length")
        return width, height

    def _jpeg(self, data: bytes) -> tuple[int, int]:
        if not data.endswith(b"\xff\xd9"):
            raise UploadRejected("malformed_jpeg")
        pos, dimensions = 2, None
        while pos + 4 <= len(data):
            if data[pos] != 255:
                raise UploadRejected("malformed_jpeg")
            while data[pos] == 255:
                pos += 1
            marker = data[pos]
            pos += 1
            if marker == 0xDA:
                break
            length = struct.unpack_from(">H", data, pos)[0]
            if length < 2 or pos + length > len(data):
                raise UploadRejected("malformed_jpeg")
            if marker in {0xC0, 0xC1, 0xC2}:
                height, width = struct.unpack_from(">HH", data, pos + 3)
                check_pixels(width, height)
                dimensions = width, height
            elif 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC}:
                raise UploadRejected("unsupported_jpeg_encoding")
            if 0xE0 <= marker <= 0xEF or marker == 0xFE:
                check_instruction_bytes(data[pos:pos + length])
            pos += length
        if dimensions is None:
            raise UploadRejected("malformed_jpeg")
        return dimensions

    def _pdf_names(self, value: bytes) -> bytes:
        value = re.sub(rb"#([0-9a-fA-F]{2})", lambda m: bytes([int(m[1], 16)]), value)
        value = value.replace(b"\x00", b" ")
        names = set(re.findall(rb"/([^\s/<>\[\](){}%]+)", value))
        forbidden = {name.encode("ascii") for name in get_config().get("uploads.pdf_forbidden_names")}
        if names & forbidden:
            raise UploadRejected("pdf_active_or_unsupported_content")
        for match in re.finditer(rb"/Filter\s*(\[[^\]]*\]|/[^\s<>\[\]()]+)", value):
            filters = re.findall(rb"/([^\s/\[\]]+)", match[1])
            if len(filters) != 1 or filters[0].decode("ascii", "ignore") not in get_config().get("uploads.pdf_allowed_filters"):
                raise UploadRejected("unsupported_pdf_filter")
        return value

    def _pdf(self, data: bytes) -> None:
        cfg = get_config()
        if not data.rstrip().endswith(b"%%EOF") or b"\nxref" not in data or b"trailer" not in data:
            raise UploadRejected("malformed_or_unsupported_pdf")
        metadata = self._pdf_names(data)
        for media in re.findall(rb"/MediaBox\s*\[([^\]]+)\]", metadata):
            box = [float(v) for v in media.split()]
            if len(box) != 4:
                raise UploadRejected("malformed_pdf_page_box")
            scale = float(cfg.get("uploads.pdf_raster_dpi")) / 72
            check_pixels(math.ceil((box[2] - box[0]) * scale), math.ceil((box[3] - box[1]) * scale))
        if len(re.findall(rb"\b\d+\s+\d+\s+obj\b", data)) > int(cfg.get("uploads.max_pdf_objects")):
            raise UploadRejected("pdf_object_limit")
        counts = [int(c) for c in re.findall(rb"/Count\s+(\d+)", metadata)]
        if counts and max(counts) > int(cfg.get("uploads.max_pdf_pages")):
            raise UploadRejected("pdf_page_limit")
        limit, expanded, position = int(cfg.get("uploads.max_expanded_bytes")), 0, 0
        while match := re.search(rb"\bstream\r?\n", data[position:]):
            start = position + match.start()
            body_start = position + match.end()
            header_start = data.rfind(b" obj", 0, start)
            header = data[header_start:start]
            header = re.sub(rb"%[^\r\n]*", b" ", header)
            header = self._pdf_names(header)
            length = re.search(rb"/Length\s+(\d+)(?!\d)(?!\s+\d+\s+R)", header)
            if length is None:
                raise UploadRejected("unsupported_pdf_stream_length")
            end = body_start + int(length[1])
            if not re.match(rb"\s*endstream\b", data[end:end + 32]):
                raise UploadRejected("malformed_pdf_stream")
            body = data[body_start:end]
            if re.search(rb"/Filter\s*(?:\[\s*)?/FlateDecode\b", header):
                body = bounded_inflate(body, limit - expanded)
                self._pdf_names(body)
                check_instruction_bytes(body)
            elif b"/DCTDecode" in header:
                width, height = self._jpeg(body)
                # JPEG stream bytes are compressed; conservatively budget decoded RGBA pixels.
                expanded += width * height * 4
                if expanded > limit:
                    raise UploadRejected("decompression_limit")
            else:
                check_instruction_bytes(body)
            if b"/DCTDecode" not in header:
                expanded += len(body)
            if expanded > limit:
                raise UploadRejected("decompression_limit")
            position = end + len(re.match(rb"\s*endstream\b", data[end:end + 32])[0])
        widths = [int(x) for x in re.findall(rb"/Width\s+(\d+)", metadata)]
        heights = [int(x) for x in re.findall(rb"/Height\s+(\d+)", metadata)]
        if widths and heights:
            check_pixels(max(widths), max(heights))
