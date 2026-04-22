# Brighterly Lesson QA — AI-Powered Tutor Quality Analysis

## Overview

This tool automates quality assurance for Brighterly's online tutoring lessons. It uses Google's Gemini 2.5 Pro model to watch full lesson recordings (video + audio) and generate detailed QA scorecards that match the format used by the human QA team.

Instead of manually reviewing lessons, QA managers upload a recording and receive a structured scorecard within 3-5 minutes — covering 35 criteria across 7 categories, each scored 1-5 with specific comments and timestamps.

---

## How It Works

### 1. Video Upload & Analysis

```
QA Manager uploads video (.mp4)
        |
        v
Video uploaded to Gemini API (Google AI)
        |
        v
Gemini watches the FULL recording (video + audio)
        |
        v
AI evaluates 35 criteria from the QA rubric
        |
        v
Returns structured JSON scorecard
        |
        v
PDF report generated + saved to history
```

The AI receives the video alongside a detailed QA rubric prompt that defines every criterion, scoring standards, and any active scoring rules. It processes both visual (camera, background, screen sharing) and audio (speech, silence, tone) signals.

### 2. QA Scorecard

The scorecard matches the human QA team's format with 7 sections:

| # | Section | Criteria | What It Evaluates |
|---|---------|----------|-------------------|
| 1 | Preparatory Work | 1 | Did the tutor study the lesson content beforehand? |
| 2 | Workplace Settings | 6 | Lighting, camera position, background noise, virtual background, physical background, appearance |
| 3 | Teaching Materials | 4 | NearPod proficiency, activity reminders, slide management, lesson structure |
| 4 | Tech Issues | 3 | Composure, expertise, and learning time priority during technical problems |
| 5 | Time Management | 2 | Lesson duration (target: 45 min) and time distribution across topics |
| 6 | Pedagogical Aspects | 17 | Initial contact, engagement (5), material explanation (4), guided practice (5) |
| 7 | Soft Skills | 10 | English fluency (4), emotionality & empathy (3), communication (3) |

**Scoring scale:**
- 1-2 = Below expectations
- 3-4 = Target
- 5 = Exceeded expectations

Each criterion includes a specific comment explaining the score with timestamps where relevant. The final score is the average of all scored criteria.

Criteria that cannot be evaluated (e.g., NearPod-specific items when NearPod is not used, or tech issue criteria when no issues occurred) are marked as N/A and excluded from the average.

### 3. Scoring Rules (Calibration System)

The AI's scoring behavior can be fine-tuned through **scoring rules** — explicit instructions that override the AI's default judgment.

**How rules work:**
1. A QA reviewer analyzes a report and finds the AI scored something incorrectly
2. They adjust the score and explain why (e.g., "Student camera was off for 15 min — engagement should be 1, not 4")
3. The system detects recurring patterns from multiple reviews
4. It suggests a rule (e.g., "If student camera is off for >5 minutes, engagement score must be 2 or lower")
5. A QA manager approves the rule
6. The rule is automatically injected into every future analysis prompt

Rules are stored in the database and can be:
- **Added manually** — QA managers write rules based on team standards
- **Suggested automatically** — system detects when the AI consistently gets the same type of criterion wrong
- **Removed** — if a rule becomes outdated or incorrect

**Example rules:**
- "If silence pauses >20 seconds occur more than 3 times, communication score must be 1 or 2"
- "If the lesson is shorter than 40 minutes, time management score must be 1"
- "If the tutor gives away answers instead of guiding, guided practice score must be 2 or lower"

### 4. PDF Reports

Each analysis generates a PDF scorecard matching the human QA format:
- Table layout with criterion, score column (color-coded), and comments
- Yellow section headers
- Score placed in the appropriate column (Below/Target/Exceeded)
- Final score at the bottom
- Header with video name, subject, duration, and model used

---

## App Pages

### Analyze Lesson
Upload a video, optionally enter booking ID and tutor name, select the AI model, and click Analyze. The analysis takes 3-5 minutes. Results are displayed as an interactive scorecard with a downloadable PDF.

### History
Browse all previously analyzed lessons with summary metrics (total count, average AI score, average human score). Each entry expands to show the full scorecard and PDF download.

### Review & Calibrate
Three tabs:
- **Review Lessons** — per-criterion score adjustment. Change any score the AI got wrong and add notes. The system suggests rules from your corrections.
- **Scoring Rules** — view, add, and remove active rules. See auto-generated suggestions from review patterns.
- **Review History** — accuracy tracking showing AI vs human score differences over time.

---

## Technical Details

### AI Model

| Model | Coverage | Cost | Use Case |
|-------|----------|------|----------|
| Gemini 2.5 Pro | Full 45-min video | ~$0.92/lesson | Default — reliable full analysis |
| Gemini 2.5 Flash | Partial (~18-24 min) | ~$0.14/lesson | Quick screening only |

**Important:** Gemini Flash only processes roughly half of a 45-minute video. Gemini Pro is required for reliable full-lesson analysis.

### Data Flow

```
lesson-qa/
  app.py              # Streamlit web UI
  qa_analyze.py       # Gemini API integration + QA rubric prompt
  generate_pdf.py     # JSON report -> PDF scorecard
  qa_history.db       # SQLite — lesson history, feedback, scoring rules
  reports/            # Generated PDF and JSON files
  requirements.txt    # Python dependencies
  .gitignore          # Excludes videos, DB, reports from git
```

### Lesson Recordings Source

Recordings are stored in Google Cloud Storage (`brighterly-prod-recordings` bucket) and referenced in BigQuery:

- **Table:** `brighterly-gcp.main_app_prod.bookings`
- **Column:** `recording_file_path` (e.g., `beam/<room_id>/<date>/Rec-<id>-<timestamp>.mp4`)
- **Related columns:** `recording_started_at`, `tutor_id`, `discipline_id`, `type`, `status`, `duration`
- **Filter:** `type = 'PAID'` for paid lessons only
- **Volume:** ~422 PAID lessons/day with recordings, 46 min average duration

### Cost Estimates

| Approach | 600/month | All (~12,600/mo) |
|----------|-----------|-------------------|
| Gemini Pro on all | $552 | $11,650 |
| Gemini Flash on all | $84 | $1,750 |
| Two-pass (Flash screen + Pro flagged) | $222 | $3,500-4,500 |
| Smart sampling (20%) | $110 | $2,300 |

### Deployment

The app is deployed on **Streamlit Community Cloud** and accessible via a web link — no installation required for QA team members.

**Setup:**
1. Connect GitHub repo to Streamlit Cloud
2. Set `GEMINI_API_KEY` in Streamlit secrets
3. Point to `lesson-qa/app.py` as the main file

The `packages.txt` in the repo root installs `ffmpeg` on the Linux server for video duration detection.

---

## Configuration

### Gemini API Key
Set as a Streamlit Cloud secret (`GEMINI_API_KEY`) or enter manually in the sidebar. Get a key at https://aistudio.google.com/apikey.

### QA Rubric
The full QA rubric is defined in `qa_analyze.py` in the `QA_RUBRIC` variable. To modify criteria, scoring definitions, or add new evaluation areas, edit this prompt directly.

### Scoring Rules
Managed through the app's "Scoring Rules" tab. Rules are stored in SQLite and automatically injected into the Gemini prompt for every analysis.
