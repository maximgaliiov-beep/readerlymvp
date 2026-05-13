# Reading Fluency Prompt — Test Runner

Automated eval for `docs/reading_fluency_generation_prompt_v4.md` against the cases in `docs/reading_fluency_test_cases.json`.

## Setup

```bash
cd ~/Desktop/Readerly_MVP/prompt-tests
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=...
```

## Run

```bash
python run_tests.py                       # all categories, all cases
python run_tests.py coverage              # one category
python run_tests.py --case C-01           # one case
python run_tests.py coverage --limit 3    # first 3 of one category (smoke)
```

Output: `results.md` in this folder.

## What it checks

Automatic (per case):
- No preamble in output
- Word count or line count inside grade-band range
- Average sentence length inside band ±20%
- T2/T3 tag counts inside per-cell caps
- Role-specific structural checks declared in `cases[].checks` (third_person, has_dialogue_tag, no_passive_in_core_args, etc.)

Manual (marked `?` in report):
- Anything declared in `cases[].checks` that isn't in `NAMED_CHECKS` in `run_tests.py`
- All `[J]`-tagged criteria in the test plan markdown

## Cost / time

Each case = 1 Gemini Flash call. ~50 cases ≈ 50 calls × ~3s = ~3 minutes. Default `--sleep 1` between calls to stay under rate limits.

## Extending

To add a new automated check, decorate a function with `@named_check("check_name")` and add the name to a case's `checks` array in the JSON.
