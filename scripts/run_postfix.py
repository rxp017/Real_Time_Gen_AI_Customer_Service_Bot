"""Run one registered frozen evaluation; refuse overwrites and unauthorized reruns."""

import argparse
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clock import FakeClock, set_global_clock  # noqa: E402
from core.embeddings import document_text  # noqa: E402
from core.llm import ProviderBlockedError  # noqa: E402
from core.retrieval import PolicyRetrievalEngine, retrieval_view  # noqa: E402
from core.store import DocumentRepository  # noqa: E402
from scripts.check_holdouts import FROZEN  # noqa: E402
from scripts.evaluate_sentiment_development import measure  # noqa: E402
from scripts.evaluation_support import EvaluationVectors, PacedProvider, wilson  # noqa: E402
from scripts.postfix_protocol import authorize_run, register, validity, verify  # noqa: E402


def corpus(task: str) -> dict:
    name = next(name for name in FROZEN if f"task{task[-1]}/" in name)
    raw = Path(name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError("Frozen evaluation hash changed")
    return json.loads(raw)


def retrieval_run(data: dict, output: Path) -> dict:
    set_global_clock(FakeClock(data["clock"]))
    provider = PacedProvider()
    vectors = EvaluationVectors(provider, Path(".verification/postfix-vectors.json"))
    engine = PolicyRetrievalEngine(DocumentRepository(), provider)
    engine.load_fixture_directory("data/sample_docs")
    views = [view for d in engine.repo.list_all() if (view := retrieval_view(d)) is not None]
    vectors.warm([document_text(d) for d in views], "RETRIEVAL_DOCUMENT")
    vectors.warm([case["question"] for case in data["cases"]], "RETRIEVAL_QUERY")
    engine.embedder = vectors
    engine.reindex()
    engine.repo.load_vector = lru_cache(maxsize=None)(engine.repo.load_vector)
    outcomes = []
    for case in data["cases"]:
        try:
            result = engine.query(case["question"], case["role"])
            answered = not result.refusal and not result.clarification_needed
            correct = answered and result.verified and any(c["doc_id"] == case["expected_doc_id"] for c in result.citations)
            item = {"id": case["id"], "expected_refusal": case["expected_refusal"], "answered": answered,
                    "correct_cited": correct, "false_answer": answered and (case["expected_refusal"] or not correct),
                    "answer": result.answer, "citations": result.citations, "trace": result.trace,
                    "infrastructure_failure": bool(result.trace.get("embedding_fallback"))}
        except (RuntimeError, ValueError, OSError) as exc:
            item = {"id": case["id"], "expected_refusal": case["expected_refusal"], "answered": False,
                    "correct_cited": False, "false_answer": False, "error": type(exc).__name__,
                    "trace": engine.diagnostic_trace, "infrastructure_failure": not isinstance(exc, ProviderBlockedError)}
        outcomes.append(item)
        print(f"STATUS T4 case {len(outcomes)}/{len(data['cases'])}: {item['trace'].get('decision')}", flush=True)
        output.write_text(json.dumps({"progress": len(outcomes), "outcomes": outcomes}, ensure_ascii=False), encoding="utf-8")
    positive = [o for o in outcomes if not o["expected_refusal"]]
    negative = [o for o in outcomes if o["expected_refusal"]]
    return {"scope": "Post-fix re-evaluation of previously exposed frozen data; actual provider, no tuning on outcomes",
            **validity(sum(o["infrastructure_failure"] for o in outcomes), len(outcomes)),
            "answer_rate": wilson(sum(o["answered"] for o in positive), len(positive)),
            "correct_cited_rate": wilson(sum(o["correct_cited"] for o in positive), len(positive)),
            "false_answer_rate": wilson(sum(o["false_answer"] for o in negative), len(negative)),
            "wrong_supported_answers": sum(o["false_answer"] for o in positive),
            "embedding_batch_errors": vectors.errors, "outcomes": outcomes}


def run(task: str, number: int) -> dict:
    digest = verify()
    output = Path(f"docs/verification/revision-{task}-postfix-run{number}.json")
    previous_path = Path(f"docs/verification/revision-{task}-postfix-run1.json")
    previous = json.loads(previous_path.read_text()) if number == 2 and previous_path.exists() else None
    authorize_run(number, digest, previous)
    if output.exists() or output.with_suffix(".started").exists():
        raise ValueError("This run index already exists; results must not be overwritten")
    output.with_suffix(".started").write_text(json.dumps({"config_hash": digest, "run": number}))
    data = corpus(task)
    if task == "t4":
        report = retrieval_run(data, output)
    else:
        measure(data["examples"], True, output, FROZEN["tests/fixtures/task5/heldout_sentiment.json"], f"frozen-run-{number}")
        report = json.loads(output.read_text(encoding="utf-8"))
        statuses = {"quota", "infrastructure", "provider_error", "unconfigured", "authentication"}
        report.update(validity(sum(o["provider_status"] in statuses for o in report["outcomes"]), len(report["outcomes"])))
    report.update(config_hash=digest, run=number, task=task, prior_exposure=True)
    if verify() != digest:
        raise ValueError("Evaluation identity changed during the run")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {k: v for k, v in report.items() if k != "outcomes"}
    print(json.dumps(summary, indent=2), flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--task", choices=["t4", "t5"])
    parser.add_argument("--run", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv()
    if args.register:
        print(json.dumps(register(), indent=2))
    elif args.task:
        run(args.task, args.run)
    else:
        parser.error("Provide --register or --task")
