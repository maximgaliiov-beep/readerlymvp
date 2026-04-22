# Lesson QA Tool — User Guide for QA Team

## What Is This Tool?

This is an AI-powered assistant that watches lesson recordings and generates quality scorecards — the same format you use for manual QA reviews. It evaluates 35 criteria across all 7 sections of the scorecard, gives each a score from 1-5, and writes specific comments with timestamps.

**It does NOT replace you.** It's a first pass that saves you time. You review the AI's output, correct mistakes, and your feedback makes the AI more accurate over time.

---

## Getting Started

1. Open the app link shared by your manager (it's a web page — no installation needed)
2. You'll see a sidebar on the left with navigation:
   - **Analyze Lesson** — run a new analysis
   - **History** — view past analyses
   - **Review & Calibrate** — review and correct AI scores

---

## How to Analyze a Lesson

1. Click **"Analyze Lesson"** in the sidebar
2. Select the model:
   - **gemini-2.5-pro** (recommended) — watches the full lesson, most accurate
   - **gemini-2.5-flash** — faster and cheaper, but may miss parts of longer lessons
3. Fill in **Booking ID** and **Tutor Name** (optional but helpful for tracking)
4. Click **"Browse files"** and upload the lesson recording (.mp4 file)
5. Click **"Analyze Lesson"**
6. Wait 3-5 minutes — the AI is watching the entire video
7. The scorecard appears on screen with all 35 criteria scored
8. Click **"Download PDF Report"** to save the scorecard as a PDF

### Tips
- Video files can be up to a few hundred MB — upload may take a minute on slower connections
- If the analysis fails, try again — sometimes the AI service has temporary issues
- Pro model is slower but much more thorough. Use Flash only for quick checks

---

## How to Read the Scorecard

Each criterion shows:
- **Color-coded card**: green (5), orange (3-4), red (1-2), gray (N/A)
- **Score badge**: colored number in the top right
- **Comment**: specific observation from the AI, often with timestamps

**N/A items** mean the criterion couldn't be evaluated (e.g., NearPod criteria when the lesson doesn't use NearPod, or tech issue criteria when there were no tech issues). These don't affect the final score.

The **Final Score** at the top is the average of all scored criteria.

---

## How to Review & Correct the AI

This is the most important part — your corrections make the AI better.

1. Go to **"Review & Calibrate"** in the sidebar
2. Click the **"Review Lessons"** tab
3. Open a lesson that needs review
4. For each criterion where the AI was wrong:
   - Change the score in the dropdown
   - Add a note explaining why (e.g., "Student was clearly distracted at 15:00, not engaged")
5. Set your **overall score** with the slider
6. Add any **general feedback** about the analysis
7. Click **"Save Review"**

### What Makes Good Feedback?

**Good feedback:**
- "AI gave engagement 5/5 but student had camera off from 20:00-35:00 — should be 2"
- "Silence at 12:30-14:00 was the student thinking, not dead air — should be 4 not 2"
- "Teacher was yawning at 8:00 and 22:00 — appearance should be 2 not 5"

**Less helpful:**
- "Score is wrong" (no specifics)
- "Too high" (which criterion? why?)

---

## Scoring Rules

Over time, your corrections create **scoring rules** — automatic instructions that change how the AI scores future lessons.

### How to View and Manage Rules

1. Go to **"Review & Calibrate"** → **"Scoring Rules"** tab
2. You'll see:
   - **Active rules** — currently applied to every analysis
   - **Add new rule** — create a rule manually
   - **Suggested rules** — patterns detected from your reviews

### How to Add a Rule Manually

1. Go to the "Scoring Rules" tab
2. Type your rule in the text box, e.g.:
   - "If the student's camera is off for more than 5 minutes, engagement score must be 2 or lower"
   - "If the teacher gives away answers more than twice, guided practice score must be 1 or 2"
   - "Water breaks should not count as dead air"
3. Select a category (engagement, communication, etc.)
4. Click "Add Rule"

### How Rules Get Suggested Automatically

When you review lessons, the system tracks patterns. For example:
- If you correct "engagement" from 4 to 2 three times for similar reasons, it suggests a rule
- You can approve the suggestion with one click, or ignore it

### How to Remove a Rule

Click "Remove" next to any active rule if it's no longer accurate.

---

## Review History

The **"Review History"** tab shows:
- How many lessons have been reviewed
- Average difference between AI and human scores
- Accuracy percentage
- Per-lesson comparison (green = close match, yellow = small diff, red = big diff)

This helps you and your manager track whether the AI is getting better over time.

---

## FAQ

**Q: How long does analysis take?**
A: 3-5 minutes per lesson with Gemini Pro. Most of that time is uploading and processing the video.

**Q: Can it analyze DEMO lessons?**
A: Yes, upload any lesson recording. The criteria are the same.

**Q: What if the AI gives a very wrong score?**
A: Review it and add specific feedback. If it's a pattern, create a scoring rule. The AI will learn from your rules.

**Q: Can I re-analyze the same lesson?**
A: Yes, just upload it again. Both results will appear in History.

**Q: Does it work with NearPod and non-NearPod lessons?**
A: Yes. For non-NearPod lessons, NearPod-specific criteria are automatically marked N/A.

**Q: What languages does it support?**
A: Currently English lessons only. The AI evaluates English fluency as part of the scorecard.

**Q: Who can see my reviews?**
A: Anyone with access to the app can see lesson history and reviews. There are no individual accounts.

**Q: What if the video won't upload?**
A: Make sure it's an .mp4, .webm, or .mov file. If it's very large (>500MB), try compressing it first. If the upload keeps failing, check your internet connection and try again.

---

## Quick Reference

| Action | Where |
|--------|-------|
| Analyze a new lesson | Sidebar → Analyze Lesson |
| Download PDF report | After analysis → "Download PDF Report" button |
| View past analyses | Sidebar → History |
| Correct AI scores | Sidebar → Review & Calibrate → Review Lessons |
| Add a scoring rule | Sidebar → Review & Calibrate → Scoring Rules → Add New Rule |
| Check AI accuracy | Sidebar → Review & Calibrate → Review History |
