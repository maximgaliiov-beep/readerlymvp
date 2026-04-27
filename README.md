# Writerly MVP

This repository contains two AI-powered tools for Brighterly's online tutoring platform:

1. **Writerly** — AI Reading Tutor for kids (K-8th grade)
2. **Lesson QA** — AI-powered tutor quality assurance from lesson recordings

---

## 1. Writerly — AI Reading Tutor

A browser-based reading practice tool that listens to a child reading aloud and provides real-time pronunciation assessment, scores, and personalized feedback.

### How It Works

```
Child selects reading level (K-1st, 2nd-3rd, 4th-5th, 6th-8th)
        |
        v
Passage displayed, split into sentences
        |
        v
Child clicks "Start Reading" -> microphone activates
        |
        v
Sentence-by-sentence assessment:
  - Active sentence is highlighted
  - Azure Speech SDK evaluates pronunciation per sentence
  - Completed sentences turn green, next sentence highlights
  - Auto-advances when enough words are heard
        |
        v
Results displayed:
  - Scores (accuracy, fluency, completeness, prosody, WER)
  - Color-coded word highlights (hover for per-word details)
  - Transcript comparison (expected vs heard)
  - AI tutor feedback with tips
  - Practice words for struggling areas
  - Session progress history
```

### Tech Stack

- **Frontend**: Single-file HTML/CSS/JS (`index.html`)
- **Speech Recognition**: Azure Speech SDK — Pronunciation Assessment API
- **Storage**: localStorage for session history

### Speech Recognition Features

- **Sentence-by-sentence assessment**: Each sentence gets its own `PronunciationAssessmentConfig` for better alignment accuracy (vs evaluating the whole passage at once)
- **Child speech optimization**: Azure child speech flag enabled for better recognition of higher-pitched voices
- **Noise suppression**: Browser-level noise suppression, echo cancellation, and auto gain control
- **Extended silence timeouts**: 3s segmentation / 5s end silence — kids pause more than adults
- **Weighted scoring**: Longer recognized segments contribute proportionally more to final scores
- **WER calculation**: Word Error Rate computed via edit-distance alignment with detailed diff view

### Scoring Metrics

| Metric | What It Measures |
|--------|-----------------|
| Overall | Combined pronunciation quality (0-100) |
| Accuracy | How correctly each word is pronounced |
| Fluency | Smoothness and natural rhythm of reading |
| Completeness | Percentage of expected words that were spoken |
| Prosody | Expression, intonation, stress patterns |
| WER | Word Error Rate — substitutions, deletions, insertions |

### Live URL

**https://writerly-729002273999.us-central1.run.app**

Deployed on Google Cloud Run (`brighterly-rnd` project, `us-central1`). Scales to zero when idle.

To redeploy after changes:
```bash
gcloud run deploy writerly --project=brighterly-rnd --region=us-central1 --source=.
```

### Setup (local)

1. Get an Azure Speech Services key from the Azure Portal
2. Replace `YOUR_AZURE_SPEECH_KEY_HERE` in `index.html` with your key
3. Set the `AZURE_REGION` (default: `eastus`)
4. Open `index.html` in a browser (or serve via any HTTP server)

### File

| File | Purpose |
|------|---------|
| `index.html` | Complete app — UI, speech recognition, scoring, feedback |

---

## 2. Lesson QA — AI-Powered Tutor Quality Analysis

Automates quality assurance for Brighterly's online tutoring lessons using Gemini 2.5 Pro to watch full lesson recordings and generate structured QA scorecards.

See [lesson-qa/README.md](lesson-qa/README.md) for full documentation.

### Quick Summary

- Upload a 45-min lesson recording -> AI scores 35 criteria across 7 categories
- Generates PDF scorecards matching the human QA team's format
- Human-in-the-loop calibration: QA reviewers correct AI scores -> system learns scoring rules
- Deployed on Streamlit Community Cloud

### Files

| File | Purpose |
|------|---------|
| `lesson-qa/app.py` | Streamlit web UI (3 pages: Analyze, History, Review) |
| `lesson-qa/qa_analyze.py` | Gemini API integration + QA rubric prompt |
| `lesson-qa/generate_pdf.py` | JSON report -> PDF scorecard |
| `lesson-qa/requirements.txt` | Python dependencies |
| `lesson-qa/README.md` | Technical documentation |
| `lesson-qa/USER_GUIDE.md` | QA team user guide |
| `packages.txt` | System deps for Streamlit Cloud (ffmpeg) |

---

## Other Docs

| File | Purpose |
|------|---------|
| `SKILL.md` | Implementation guide / reusable skill doc for the Lesson QA pattern |
| `docs/knowledge-base-proposal.md` | Proposal for structured Brighterly knowledge base in Notion |
