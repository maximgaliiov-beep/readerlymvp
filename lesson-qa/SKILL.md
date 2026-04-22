# SKILL.MD — Lessons QA AI Agent

## Skill Name
Lessons QA AI Agent

## Description
Build an AI-powered quality assurance tool that watches online tutoring lesson recordings (video + audio) and generates structured QA scorecards. Uses Google Gemini 2.5 Pro for multimodal video analysis and Streamlit for the web UI. Includes a human-in-the-loop calibration system where QA reviewer corrections create scoring rules that improve future AI analyses.

## When to Use
- Building AI-powered video analysis tools for quality assurance
- Creating lesson/meeting/call review systems from recordings
- Implementing human-in-the-loop calibration for AI scoring
- Deploying Streamlit apps with Gemini API integration
- Generating structured PDF reports from AI analysis

---

## Architecture

```
Video Upload → Gemini 2.5 Pro API → Structured JSON Scorecard → PDF Report
                    ↑                                              ↓
            Scoring Rules                                    SQLite DB
            (from human QA                                  (history +
             corrections)                                    feedback)
                    ↑                                           ↓
            Human QA Reviews ← Streamlit Web UI ← Scorecard Display
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Video Analysis | Gemini 2.5 Pro API | Multimodal analysis of full 45-min video + audio |
| Web UI | Streamlit | Upload, view scorecards, review & calibrate |
| PDF Generation | fpdf2 | Structured scorecard matching human QA format |
| Storage | SQLite | Lesson history, feedback, scoring rules |
| Deployment | Streamlit Community Cloud | Free hosting, no installation for users |
| Video Duration | ffprobe (Linux) / mdls (macOS) | Cross-platform duration detection |

---

## Implementation Guide

### Step 1: QA Rubric as a Prompt

Define your entire QA rubric in a prompt variable. Structure it as:
- Role description for the AI
- Scoring scale definition (1-5)
- Each criterion with name, description, and expected JSON output structure
- Rules for N/A handling
- Instructions for timestamps and specific observations

```python
QA_RUBRIC = """
You are a Quality Assurance analyst for [Company]...
Score each criterion on a 1-5 scale:
- 1-2 = Below expectations
- 3-4 = Target
- 5 = Exceeded expectations

Return your analysis as JSON with this EXACT structure:
{
  "section_name": {
    "criterion_name": {
      "criterion": "Description of what to evaluate",
      "score": <1-5 or null>,
      "comment": "<specific observation with timestamps>"
    }
  }
}
"""
```

### Step 2: Video Analysis with Gemini

```python
from google import genai

client = genai.Client(api_key=API_KEY)

# Upload video (Gemini processes full video natively)
video_file = client.files.upload(file=video_path)

# Wait for processing
while video_file.state.name == "PROCESSING":
    time.sleep(5)
    video_file = client.files.get(name=video_file.name)

# Analyze with rubric + any active scoring rules
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=[video_file, rubric_prompt + scoring_rules],
)

# Parse JSON response
report = json.loads(response.text.strip())

# Clean up uploaded file
client.files.delete(name=video_file.name)
```

### Step 3: Scoring Rules Calibration System

The calibration loop:
1. AI generates scorecard
2. Human QA reviewer corrects individual criterion scores with notes
3. System stores per-criterion feedback in `criterion_feedback` table
4. System detects patterns (e.g., same criterion corrected 3+ times for similar reasons)
5. System suggests a scoring rule
6. QA manager approves the rule
7. Approved rules are stored in `scoring_rules` table
8. Before each analysis, active rules are fetched and appended to the prompt as "MANDATORY SCORING RULES"

```python
def get_rules_for_prompt(conn):
    rules = conn.execute(
        "SELECT rule_text, category FROM scoring_rules WHERE status='active'"
    ).fetchall()
    if not rules:
        return ""
    block = "\n\nMANDATORY SCORING RULES (override your default judgment):\n"
    for rule_text, category in rules:
        block += f"- [{category}] {rule_text}\n"
    return block
```

### Step 4: PDF Report Generation

Use fpdf2 for structured PDF scorecards:
- Landscape A4 format
- Table with columns: Criterion | Below (1-2) | Target (3-4) | Exceeded (5) | Comments
- Color-coded score placement in appropriate column
- Section headers with distinct background color
- Unicode sanitization for latin-1 compatibility

### Step 5: Streamlit Web UI

Three main pages:
1. **Analyze Lesson** — file upload, model selection, scorecard display, PDF download
2. **History** — browsable list of past analyses with metrics
3. **Review & Calibrate** — per-criterion score adjustment, scoring rules management, accuracy tracking

---

## Critical Lessons Learned

### Model Selection
- **Gemini 2.5 Pro**: Processes full 45-min videos reliably. ~$0.92/lesson.
- **Gemini 2.5 Flash**: Only processes ~18-24 min of 45-min videos. NOT suitable for full lesson analysis. Use only for quick screening.
- Adding duration hints to the prompt does NOT fix Flash's truncation — it's a model-level limitation.

### Video Duration Detection
- Use ffprobe on Linux (Streamlit Cloud) — requires `ffmpeg` in `packages.txt`
- Use macOS `mdls` as fallback for local development
- Default to expected duration (45 min) if both fail
- Pass detected duration to the prompt so the AI knows the expected length

### PDF Unicode Issues
- fpdf2 uses latin-1 encoding by default
- Characters like →, —, ', " cause `FPDFUnicodeEncodingException`
- Solution: sanitize text before PDF generation, replacing unicode with ASCII equivalents

### Streamlit Cloud Deployment
- `packages.txt` in repo root installs system packages (e.g., `ffmpeg`)
- Secrets set via Streamlit Cloud dashboard (not committed to repo)
- SQLite works but resets on each deployment — consider external DB for production
- Video upload size limited by Streamlit's default settings

### Scoring Rules > Fine-Tuning
For well-defined rubrics, explicit scoring rules injected into the prompt are more effective than model fine-tuning because:
- Transparent: QA team can read and understand every rule
- Immediate: rules apply to the next analysis, no retraining needed
- Reversible: remove a rule if it's wrong
- Auditable: clear connection between human correction → rule → AI behavior change

---

## Cost Optimization Strategies

| Strategy | Description | Cost for 600/mo |
|----------|-------------|-----------------|
| Pro on all | Most accurate, highest cost | $552/mo |
| Flash screening | Flash first, Pro only for flagged lessons | $222/mo |
| Smart sampling | Analyze 20% of lessons randomly | $110/mo |
| Flash only | Cheapest but misses half of each lesson | $84/mo |

Recommended: Start with Pro on a sample (e.g., 600/mo), use scoring rules to calibrate, then expand coverage.

---

## Database Schema

```sql
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_name TEXT, booking_id TEXT, tutor_name TEXT,
    subject TEXT, duration INTEGER, model TEXT,
    ai_score REAL, human_score REAL,
    report_json TEXT, pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE criterion_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER, criterion_key TEXT,
    ai_score INTEGER, human_score INTEGER,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scoring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_text TEXT, category TEXT,
    status TEXT DEFAULT 'active',  -- active, suggested, removed
    source TEXT DEFAULT 'manual',  -- manual, auto-suggested
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## File Structure

```
lesson-qa/
  app.py              # Streamlit web UI (3 pages)
  qa_analyze.py       # Gemini API integration + QA rubric prompt
  generate_pdf.py     # JSON report → PDF scorecard
  qa_history.db       # SQLite database (auto-created)
  reports/            # Generated PDF and JSON files
  requirements.txt    # Python deps: streamlit, google-genai, fpdf2
  README.md           # Technical documentation
  USER_GUIDE.md       # QA team user guide
  SKILL.md            # This file — implementation guide
  .gitignore          # Excludes videos, DB, reports
packages.txt          # Repo root — system deps for Streamlit Cloud (ffmpeg)
```

---

## Dependencies

```
streamlit>=1.30.0
google-genai>=1.0.0
fpdf2>=2.8.0
```

System: `ffmpeg` (for video duration detection on Linux)

---

## Adapting This Skill

To adapt this pattern for a different QA use case:

1. **Replace the rubric**: Edit `QA_RUBRIC` with your evaluation criteria, scoring scale, and expected JSON structure
2. **Adjust the PDF template**: Modify `generate_pdf.py` to match your report format
3. **Update the UI**: Adjust section names, card layouts, and review interface in `app.py`
4. **Keep the calibration system**: The scoring rules pattern works for any structured evaluation — human corrections → rules → better AI scoring

The core pattern (multimodal AI + structured prompt + human calibration loop) applies to:
- Call center QA
- Medical consultation reviews
- Sales call scoring
- Training session evaluation
- Content moderation review
