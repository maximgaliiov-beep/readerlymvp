#!/usr/bin/env python3
"""
Reading Fluency prompt v4 — automated test runner.

Usage:
    python run_tests.py                       # all categories
    python run_tests.py coverage              # one category
    python run_tests.py --case C-01           # one case
    python run_tests.py --limit 3             # cap per category
"""

import os
import sys
import json
import re
import argparse
import time
from pathlib import Path
from datetime import datetime
from google import genai

ROOT = Path(__file__).parent.parent
PROMPT_PATH = ROOT / "docs" / "reading_fluency_generation_prompt_v4.md"
CASES_PATH = ROOT / "docs" / "reading_fluency_test_cases.json"

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: set GEMINI_API_KEY")
    sys.exit(1)

MODEL = "gemini-2.5-flash"

GRADE_BANDS = {
    "K-2":  {"words": (40, 60),   "avg_sent": (5, 8),    "lines": (6, 10)},
    "3-5":  {"words": (80, 120),  "avg_sent": (10, 14),  "lines": (10, 16)},
    "6-8":  {"words": (120, 180), "avg_sent": (14, 20)},
    "9-12": {"words": (180, 250), "avg_sent": (18, 25)},
}

TAG_T2 = re.compile(r"\[T2:\s*([^\]]+)\]")
TAG_T3 = re.compile(r"\[T3:\s*([^\]]+)\]")
PREAMBLE = re.compile(r"^(here'?s?\b|sure\b|okay\b|let me\b|i'll\b|certainly\b|of course\b|title:|\*\*title)", re.IGNORECASE)
DIALOGUE_TAG = re.compile(r'"[^"]+",?\s+\w+\s+(said|asked|whispered|called|shouted|murmured|replied|cried|answered)', re.IGNORECASE)
PASSIVE = re.compile(r"\b(is|are|was|were|been|being|be)\s+\w+ed\b", re.IGNORECASE)
FIRST_PERSON = re.compile(r"\b(I|I'm|I've|I'll|my|me|mine)\b")


def strip_tags(text):
    # [T2: word] / [T3: word] -> word
    text = re.sub(r"\[T[23]:\s*([^\]]+)\]", r"\1", text)
    # phonetic guides like " [pho-NEH-tik]" -> removed
    text = re.sub(r"\s*\[[a-zA-Z][a-zA-Z\-]*\]", "", text)
    return text


def outside_quotes(text):
    return re.sub(r'"[^"]*"', '', text)


def word_count(text):
    return len(re.findall(r"\b\w+\b", strip_tags(text)))


def line_count(text):
    return len([l for l in text.strip().split("\n") if l.strip()])


def avg_sentence_length(text):
    clean = strip_tags(text)
    sentences = [s for s in re.split(r"[.!?]+", clean) if s.strip()]
    if not sentences:
        return 0.0
    return sum(len(re.findall(r"\b\w+\b", s)) for s in sentences) / len(sentences)


def is_poem_case(case):
    return case["grade"] in ("K-2", "3-5") and case["role"] == "Perform a scene"


def check_universal(case, output):
    """Returns [(name, pass|None, detail)]. None = needs manual review."""
    results = []
    first_line = output.strip().split("\n", 1)[0]
    results.append(("no_preamble", not PREAMBLE.match(first_line), first_line[:60]))

    band = GRADE_BANDS.get(case["grade"], {})

    if is_poem_case(case):
        lc = line_count(output)
        lo, hi = band["lines"]
        results.append((f"line_count[{lo}-{hi}]", lo <= lc <= hi, f"got {lc}"))
    else:
        wc = word_count(output)
        lo, hi = band["words"]
        results.append((f"word_count[{lo}-{hi}]", lo <= wc <= hi, f"got {wc}"))
        avg = avg_sentence_length(output)
        slo, shi = band["avg_sent"]
        tol_lo, tol_hi = slo * 0.8, shi * 1.2
        results.append(
            (f"avg_sent[{slo}-{shi} ±20%]", tol_lo <= avg <= tol_hi, f"got {avg:.1f}")
        )

    # Tag caps
    t2 = len(TAG_T2.findall(output))
    t3 = len(TAG_T3.findall(output))
    grade, role = case["grade"], case["role"]
    if grade == "K-2":
        if role == "Perform a scene":
            results.append(("t2_cap[0]", t2 == 0, f"got {t2}"))
        else:
            results.append(("t2_cap[≤2]", t2 <= 2, f"got {t2}"))
        results.append(("no_t3", t3 == 0, f"got {t3}"))
    elif grade == "3-5":
        if role == "Perform a scene":
            results.append(("t2_cap[≤3]", t2 <= 3, f"got {t2}"))
            results.append(("no_t3", t3 == 0, f"got {t3}"))
        else:
            results.append(("t2_range[3-5]", 3 <= t2 <= 5, f"got {t2}"))
    elif grade == "6-8":
        if role == "Perform a scene":
            results.append(("t2_range[4-6]", 4 <= t2 <= 6, f"got t2={t2}"))
        else:
            combined = t2 + t3
            results.append(("combined_tags[5-8]", 5 <= combined <= 8, f"got {combined}"))

    return results


NAMED_CHECKS = {}


def named_check(name):
    def decorator(fn):
        NAMED_CHECKS[name] = fn
        return fn
    return decorator


@named_check("third_person")
def _third_person(output):
    clean = outside_quotes(strip_tags(output))
    return not FIRST_PERSON.search(clean), "found first-person outside quotes"


@named_check("first_person")
def _first_person(output):
    clean = outside_quotes(strip_tags(output))
    return bool(FIRST_PERSON.search(clean)), "no first-person markers"


@named_check("second_person")
def _second_person(output):
    clean = strip_tags(output).lower()
    return bool(re.search(r"\byou\b", clean)), "no 'you' found"


@named_check("has_dialogue_tag")
def _dialogue(output):
    return bool(DIALOGUE_TAG.search(strip_tags(output))), "no quoted+tagged dialogue"


@named_check("min_2_you")
def _min_2_you(output):
    n = len(re.findall(r"\byou\b", strip_tags(output), re.IGNORECASE))
    return n >= 2, f"got {n}"


@named_check("no_passive_in_core_args")
def _no_passive(output):
    sents = [s for s in re.split(r"[.!?]+", strip_tags(output)) if s.strip()]
    sample = " ".join(sents[1:4])  # skip opener, check next three
    return not PASSIVE.search(sample), "passive found"


@named_check("6_to_10_lines")
def _6_to_10(output):
    lc = line_count(output)
    return 6 <= lc <= 10, f"got {lc}"


@named_check("10_to_16_lines")
def _10_to_16(output):
    lc = line_count(output)
    return 10 <= lc <= 16, f"got {lc}"


@named_check("no_tier_tags")
def _no_tags(output):
    n = len(TAG_T2.findall(output)) + len(TAG_T3.findall(output))
    return n == 0, f"got {n} tags"


@named_check("self_interruption")
def _self_interrupt(output):
    return bool(re.search(r"—|\.\.\.|…", output)), "no em-dash or ellipsis"


def run_named(case, output):
    results = []
    for c in case.get("checks", []):
        fn = NAMED_CHECKS.get(c)
        if fn is None:
            results.append((f"{c}[manual]", None, "judge required"))
            continue
        ok, detail = fn(output)
        results.append((c, ok, detail if not ok else ""))
    return results


def call_model(client, prompt, case):
    user_input = (
        f"INPUTS:\n"
        f"grade band: {case['grade']}\n"
        f"activity: {case['role']}\n"
        f"situation: {case['situation']}"
    )
    contents = f"{prompt}\n\n---\n\n{user_input}"
    response = client.models.generate_content(model=MODEL, contents=contents)
    return response.text or ""


def render_check(name, ok, detail):
    if ok is True:
        return f"- ✓ `{name}` {detail}".rstrip()
    if ok is None:
        return f"- ? `{name}` {detail}".rstrip()
    return f"- ✗ `{name}` {detail}".rstrip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("category", nargs="?", default=None)
    parser.add_argument("--case", default=None)
    parser.add_argument("--out", default="results.md")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()

    prompt = PROMPT_PATH.read_text()
    cases_data = json.loads(CASES_PATH.read_text())
    client = genai.Client(api_key=API_KEY)

    lines = [f"# Reading Fluency v4 — test run", f"_{datetime.now().isoformat(timespec='seconds')}_  ", f"_model: {MODEL}_", ""]
    summary_placeholder_idx = len(lines)
    lines.append("")  # filled at end

    total = passed = manual = failed = 0

    for cat_name, cat in cases_data["categories"].items():
        if args.category and cat_name != args.category:
            continue
        lines += [f"## {cat_name}", ""]
        cases = cat["cases"]
        if args.limit:
            cases = cases[:args.limit]
        for case in cases:
            if args.case and case["id"] != args.case:
                continue
            lines.append(f"### {case['id']} — {case['grade']} / {case['role']}")
            lines.append(f"**Situation:** {case['situation'] or '_(empty)_'}\n")
            try:
                output = call_model(client, prompt, case)
            except Exception as e:
                lines.append(f"_API error: {e}_\n")
                continue
            lines.append("**Output:**\n")
            lines.append("```")
            lines.append(output.strip())
            lines.append("```\n")
            lines.append("**Checks:**\n")
            for name, ok, detail in check_universal(case, output) + run_named(case, output):
                total += 1
                if ok is True:
                    passed += 1
                elif ok is None:
                    manual += 1
                else:
                    failed += 1
                lines.append(render_check(name, ok, detail))
            lines.append("")
            time.sleep(args.sleep)

    auto_total = total - manual
    rate = (passed / auto_total * 100) if auto_total else 0
    lines[summary_placeholder_idx] = (
        f"**Summary:** {passed}/{auto_total} auto-checks passed ({rate:.0f}%); "
        f"{failed} failed; {manual} need manual review.\n"
    )

    out_path = Path(__file__).parent / args.out
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")
    print(f"Auto: {passed}/{auto_total} passed ({rate:.0f}%) · {failed} fail · {manual} manual")


if __name__ == "__main__":
    main()
