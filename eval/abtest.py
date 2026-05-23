"""A/B eval harness — does the workspace brain actually help?

For each held-out question, asks Claude twice:
    A) with the brain injected into the system prompt
    B) without the brain (control)
Then asks a judge model (also given the brain as ground truth) to score
both answers blind on accuracy / specificity / usefulness (0-10 each).

Reports mean delta + 95% CI over all (question x run) pairs.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    python -m eval.abtest                       # default: 1 run per question
    python -m eval.abtest --runs 3              # 3 runs per question (15 pairs)
    python -m eval.abtest --brain ./WORKSPACE_BRAIN.md
    python -m eval.abtest --dry-run             # print prompts, no API calls
    python -m eval.abtest --output results.json

Cost: ~$0.02-0.05 per run with default (Haiku for answers, Sonnet for judge).
Prompt caching cuts the brain content cost by ~90% across runs in a session.

Requires: pip install anthropic>=0.40.0
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BRAIN = Path.cwd() / "WORKSPACE_BRAIN.md"
FALLBACK_BRAIN = REPO_ROOT / "eval" / "fixtures" / "sample_brain.md"
QUESTIONS_PATH = REPO_ROOT / "eval" / "questions.json"

# Cheap model for the A/B answers, smarter model for the judge.
ANSWER_MODEL = os.environ.get("ABTEST_ANSWER_MODEL", "claude-haiku-4-5-20251001")
JUDGE_MODEL = os.environ.get("ABTEST_JUDGE_MODEL", "claude-sonnet-4-6")

SYSTEM_WITH_BRAIN = (
    "You are answering a question about an active software project. The current "
    "state of the project is captured in the WORKSPACE_BRAIN.md below. Treat it "
    "as the source of truth. Be specific - cite dates, names, file paths, ticket "
    "numbers when relevant. If the brain doesn't contain the answer, say so "
    "directly rather than guessing.\n\n"
    "=== WORKSPACE_BRAIN.md ===\n{brain}\n=== END BRAIN ==="
)

SYSTEM_WITHOUT_BRAIN = (
    "You are answering a question about an active software project. Be specific "
    "if you can. If you don't know the answer, say so directly rather than guessing."
)

JUDGE_SYSTEM = (
    "You are an impartial judge scoring two candidate answers to a question about "
    "a software project. The actual project state is given to you as ground truth. "
    "Both candidates were asked the same question; one had access to the project "
    "state, the other did not - you must score them blind, without knowing which "
    "is which.\n\n"
    "=== GROUND TRUTH (WORKSPACE_BRAIN.md) ===\n{brain}\n=== END GROUND TRUTH ===\n\n"
    "For each candidate, score 0-10 on three axes:\n"
    "- accuracy: how well does the answer match the ground truth?\n"
    "- specificity: how concrete is it (names, dates, identifiers vs generalities)?\n"
    "- usefulness: would acting on this answer move work forward?\n\n"
    "Return STRICT JSON only, no prose:\n"
    "{{\"a\": {{\"accuracy\": <0-10>, \"specificity\": <0-10>, \"usefulness\": <0-10>}}, "
    "\"b\": {{\"accuracy\": <0-10>, \"specificity\": <0-10>, \"usefulness\": <0-10>}}, "
    "\"reasoning\": \"<one sentence>\"}}"
)


@dataclass
class Scores:
    accuracy: float
    specificity: float
    usefulness: float

    @property
    def total(self) -> float:
        return self.accuracy + self.specificity + self.usefulness


@dataclass
class RunResult:
    question_id: str
    question: str
    answer_with_brain: str
    answer_without_brain: str
    scores_with: Scores
    scores_without: Scores
    delta_total: float
    reasoning: str


def load_brain(path: Path | None) -> tuple[str, str]:
    if path and path.exists():
        return path.read_text(encoding="utf-8"), str(path)
    if DEFAULT_BRAIN.exists():
        return DEFAULT_BRAIN.read_text(encoding="utf-8"), str(DEFAULT_BRAIN)
    if FALLBACK_BRAIN.exists():
        print(f"(no WORKSPACE_BRAIN.md found, using fixture {FALLBACK_BRAIN.name})")
        return FALLBACK_BRAIN.read_text(encoding="utf-8"), str(FALLBACK_BRAIN)
    raise FileNotFoundError("No brain file found. Pass --brain PATH.")


def load_questions(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["questions"]


def get_client():
    try:
        import anthropic
    except ImportError:
        print("ERROR: `pip install anthropic` first.")
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set ANTHROPIC_API_KEY env var.")
        sys.exit(1)
    return anthropic.Anthropic()


def answer_question(client, system: str, question: str, model: str) -> str:
    """One API call, prompt-caches the system block (brain is reused across calls)."""
    resp = client.messages.create(
        model=model,
        max_tokens=400,
        system=[
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ],
        messages=[{"role": "user", "content": question}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def judge(client, brain: str, question: str, ans_a: str, ans_b: str) -> tuple[Scores, Scores, str]:
    """Score both blind. Randomize a/b internally to remove order bias."""
    import random
    swap = random.random() < 0.5
    first, second = (ans_b, ans_a) if swap else (ans_a, ans_b)
    user = (
        f"QUESTION: {question}\n\n"
        f"CANDIDATE A:\n{first}\n\n"
        f"CANDIDATE B:\n{second}\n"
    )
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=400,
        system=[
            {"type": "text", "text": JUDGE_SYSTEM.format(brain=brain),
             "cache_control": {"type": "ephemeral"}}
        ],
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Strip markdown fences if model wrapped JSON in them
        text = text.strip("`").lstrip("json\n").strip("`").strip()
        parsed = json.loads(text)
    s_first = Scores(**parsed["a"])
    s_second = Scores(**parsed["b"])
    # Un-swap so returned (with_brain, without_brain) order matches input
    if swap:
        return s_second, s_first, parsed.get("reasoning", "")
    return s_first, s_second, parsed.get("reasoning", "")


def run_one(client, brain: str, q: dict[str, str]) -> RunResult:
    ans_with = answer_question(client, SYSTEM_WITH_BRAIN.format(brain=brain), q["prompt"], ANSWER_MODEL)
    ans_without = answer_question(client, SYSTEM_WITHOUT_BRAIN, q["prompt"], ANSWER_MODEL)
    s_with, s_without, reasoning = judge(client, brain, q["prompt"], ans_with, ans_without)
    return RunResult(
        question_id=q["id"],
        question=q["prompt"],
        answer_with_brain=ans_with,
        answer_without_brain=ans_without,
        scores_with=s_with,
        scores_without=s_without,
        delta_total=s_with.total - s_without.total,
        reasoning=reasoning,
    )


def confidence_interval_95(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return values[0] if values else 0.0, values[0] if values else 0.0
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / (len(values) ** 0.5)
    # z=1.96 for 95% normal approximation; fine for N>=5
    margin = 1.96 * se
    return mean - margin, mean + margin


def main() -> int:
    p = argparse.ArgumentParser(description="A/B eval: does the brain actually help?")
    p.add_argument("--brain", type=Path, default=None, help="Path to WORKSPACE_BRAIN.md")
    p.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    p.add_argument("--runs", type=int, default=1, help="Runs per question (default: 1)")
    p.add_argument("--dry-run", action="store_true", help="Print prompts, no API calls")
    p.add_argument("--output", type=Path, default=None, help="Save JSON results to file")
    args = p.parse_args()

    brain, brain_path = load_brain(args.brain)
    questions = load_questions(args.questions)

    print(f"abtest v1.0")
    print(f"  brain:        {brain_path} ({len(brain.encode('utf-8'))/1024:.1f} KB)")
    print(f"  questions:    {len(questions)} held-out, {args.runs} run(s) each = {len(questions)*args.runs} pairs")
    print(f"  answer model: {ANSWER_MODEL}")
    print(f"  judge model:  {JUDGE_MODEL}")
    print()

    if args.dry_run:
        print("=== DRY RUN: showing prompts for question 0 ===\n")
        print("SYSTEM (with brain) [first 400 chars]:")
        print(SYSTEM_WITH_BRAIN.format(brain=brain)[:400] + "...\n")
        print("SYSTEM (without brain):")
        print(SYSTEM_WITHOUT_BRAIN + "\n")
        print(f"USER: {questions[0]['prompt']}\n")
        print("(no API calls made; pass without --dry-run to run for real)")
        return 0

    client = get_client()
    results: list[RunResult] = []
    t0 = time.time()
    for r in range(args.runs):
        for q in questions:
            print(f"  [{len(results)+1}/{len(questions)*args.runs}] {q['id']:<20}", end=" ", flush=True)
            try:
                res = run_one(client, brain, q)
                results.append(res)
                marker = "+" if res.delta_total > 0 else ("=" if res.delta_total == 0 else "-")
                print(f"{marker} delta={res.delta_total:+.1f}  (with={res.scores_with.total:.0f}, without={res.scores_without.total:.0f})")
            except Exception as e:
                print(f"FAILED: {e}")

    elapsed = time.time() - t0
    print()
    print(f"Done in {elapsed:.1f}s.")
    print()

    if not results:
        print("No successful runs. Bailing.")
        return 1

    deltas = [r.delta_total for r in results]
    mean_delta = statistics.mean(deltas)
    lo, hi = confidence_interval_95(deltas)
    wins = sum(1 for d in deltas if d > 0)
    ties = sum(1 for d in deltas if d == 0)
    losses = sum(1 for d in deltas if d < 0)
    with_mean = statistics.mean([r.scores_with.total for r in results])
    without_mean = statistics.mean([r.scores_without.total for r in results])

    print("=" * 60)
    print(f"Results over {len(results)} pairs")
    print("=" * 60)
    print(f"  Mean delta (with - without):  {mean_delta:+.2f} / 30 pts")
    print(f"  95% CI:                       [{lo:+.2f}, {hi:+.2f}]")
    print(f"  Wins / ties / losses:         {wins} / {ties} / {losses}")
    print(f"  Mean score WITH brain:        {with_mean:.1f} / 30")
    print(f"  Mean score WITHOUT brain:     {without_mean:.1f} / 30")
    if mean_delta > 0 and lo > 0:
        print(f"  Verdict:                      Brain helps (significant at 95% CI).")
    elif mean_delta > 0:
        print(f"  Verdict:                      Brain helps on average (not significant at 95% CI - more runs needed).")
    elif mean_delta < 0 and hi < 0:
        print(f"  Verdict:                      Brain HURTS (significant at 95% CI). Check the brain for noise.")
    else:
        print(f"  Verdict:                      No clear effect. Try more runs or a brain-dependent question set.")

    if args.output:
        args.output.write_text(
            json.dumps(
                {
                    "summary": {
                        "n_pairs": len(results),
                        "mean_delta": mean_delta,
                        "ci95_low": lo,
                        "ci95_high": hi,
                        "wins": wins, "ties": ties, "losses": losses,
                        "with_mean": with_mean, "without_mean": without_mean,
                    },
                    "runs": [
                        {**asdict(r), "scores_with": asdict(r.scores_with), "scores_without": asdict(r.scores_without)}
                        for r in results
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  Results saved to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
