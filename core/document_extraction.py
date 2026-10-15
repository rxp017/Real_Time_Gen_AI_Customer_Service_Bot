"""Text and raster evidence extraction from files that passed the upload gate."""

import io
import math
from dataclasses import dataclass, field
from threading import RLock

import pypdfium2 as pdfium
from PIL import Image

from core.config import get_config
from core.ocr import TesseractOCR, TextLine, blur_score
from core.security import detect_prompt_injection
from core.upload_gate import GatedFile, UploadRejected, check_pixels

_PDF_LOCK = RLock()


@dataclass
class Extraction:
    lines: list[TextLine] = field(default_factory=list)
    quality: list[dict[str, float | int | str | bool]] = field(default_factory=list)


def check_untrusted(lines: list[TextLine]) -> None:
    text = "\n".join(line.text for line in lines)
    if detect_prompt_injection(text)[0]:
        raise UploadRejected("prompt_injection")


class DocumentExtractor:
    def __init__(self, ocr: TesseractOCR | None = None) -> None:
        self.ocr = ocr or TesseractOCR()

    def _raster(self, image: Image.Image, page: int, language: str, required: bool) -> Extraction:
        check_pixels(image.width, image.height)
        lines, confidence = self.ocr.recognize(image, page, language)
        check_untrusted(lines)
        return Extraction(lines, [{"page": page, "blur_score": blur_score(image),
                                   "ocr_confidence": confidence, "text_characters": sum(len(line.text) for line in lines),
                                   "required": required, "method": "ocr"}])

    def extract(self, data: bytes, gated: GatedFile, language: str) -> Extraction:
        if gated.mime != "application/pdf":
            with Image.open(io.BytesIO(data)) as probe:
                if getattr(probe, "n_frames", 1) != 1:
                    raise UploadRejected("animation_not_supported")
                probe.verify()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                return self._raster(image, 1, language, True)
        cfg = get_config()
        result = Extraction()
        # PDFium is not thread-safe, even across different documents.
        with _PDF_LOCK, pdfium.PdfDocument(data) as document:
            if not 0 < len(document) <= int(cfg.get("uploads.max_pdf_pages")):
                raise UploadRejected("pdf_page_limit")
            characters = 0
            for page_index in range(len(document)):
                page = document[page_index]
                try:
                    scale = float(cfg.get("uploads.pdf_raster_dpi")) / 72
                    width, height = page.get_size()
                    check_pixels(math.ceil(width * scale), math.ceil(height * scale))
                    native = []
                    textpage = page.get_textpage()
                    try:
                        count = textpage.count_chars()
                        characters += count
                        if characters > int(cfg.get("uploads.max_pdf_characters")):
                            raise UploadRejected("pdf_character_limit")
                        text, boxes = "", []
                        for index in range(count):
                            char = chr(pdfium.raw.FPDFText_GetUnicode(textpage, index))
                            if char in "\r\n":
                                if text.strip() and boxes:
                                    native.append(self._native_line(text, boxes, page_index + 1))
                                text, boxes = "", []
                            else:
                                text += char
                                boxes.append(textpage.get_charbox(index))
                        if text.strip() and boxes:
                            native.append(self._native_line(text, boxes, page_index + 1))
                    finally:
                        textpage.close()
                    check_untrusted(native)
                    has_native = sum(len(line.text.strip()) for line in native) >= int(cfg.get("uploads.min_native_characters"))
                    bitmap = page.render(scale=scale)
                    try:
                        image = bitmap.to_pil().copy()
                    finally:
                        bitmap.close()
                    try:
                        raster = self._raster(image, page_index + 1, language, not has_native)
                    finally:
                        image.close()
                    result.lines.extend(native if has_native else raster.lines)
                    # Embedded images can contain fields absent from a native page header.
                    if has_native:
                        result.lines.extend(raster.lines)
                    result.quality.extend(raster.quality)
                finally:
                    page.close()
        return result

    @staticmethod
    def _native_line(text: str, boxes: list[tuple[float, float, float, float]], page: int) -> TextLine:
        return TextLine(text.strip(), 1.0, page, (min(b[0] for b in boxes), min(b[1] for b in boxes),
                                                max(b[2] for b in boxes), max(b[3] for b in boxes)),
                        "points", "bottom_left")
