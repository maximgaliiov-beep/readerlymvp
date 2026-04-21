"""
Brighterly Lesson QA — Streamlit App
Upload a lesson video, get an AI-generated QA scorecard.
"""

import os
import json
import time
import tempfile
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from qa_analyze import analyze_lesson, get_video_duration_minutes
from generate_pdf import generate_pdf

# --- Config ---
DB_PATH = Path(__file__).parent / "qa_history.db"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# --- Database ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_name TEXT NOT NULL,
            booking_id TEXT,
            tutor_name TEXT,
            subject TEXT,
            duration_minutes INTEGER,
            final_score REAL,
            model_used TEXT,
            report_json TEXT,
            pdf_path TEXT,
            human_score REAL,
            human_feedback TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def save_lesson(conn, data: dict):
    conn.execute("""
        INSERT INTO lessons (video_name, booking_id, tutor_name, subject,
                           duration_minutes, final_score, model_used,
                           report_json, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["video_name"], data.get("booking_id"), data.get("tutor_name"),
        data["subject"], data["duration"], data["final_score"],
        data["model"], data["report_json"], data["pdf_path"]
    ))
    conn.commit()


def update_human_feedback(conn, lesson_id: int, human_score: float, feedback: str):
    conn.execute("""
        UPDATE lessons SET human_score = ?, human_feedback = ? WHERE id = ?
    """, (human_score, feedback, lesson_id))
    conn.commit()


def get_all_lessons(conn):
    cursor = conn.execute("""
        SELECT id, video_name, booking_id, tutor_name, subject,
               duration_minutes, final_score, human_score, model_used, analyzed_at
        FROM lessons ORDER BY analyzed_at DESC
    """)
    return cursor.fetchall()


def get_lesson_report(conn, lesson_id: int):
    cursor = conn.execute("""
        SELECT report_json, pdf_path, human_score, human_feedback
        FROM lessons WHERE id = ?
    """, (lesson_id,))
    return cursor.fetchone()


# --- Helpers ---
def collect_scores(obj):
    scores = []
    if isinstance(obj, dict):
        if "score" in obj and obj["score"] is not None:
            scores.append(obj["score"])
        for v in obj.values():
            scores.extend(collect_scores(v))
    return scores


def render_criterion(data, key=""):
    """Render a single criterion as a styled row."""
    if not isinstance(data, dict) or "criterion" not in data:
        return

    score = data.get("score")
    comment = data.get("comment", "")

    if score is None:
        color = "#f0f0f0"
        label = "N/A"
    elif score >= 5:
        color = "#c6efce"
        label = f"**{score}**/5"
    elif score >= 3:
        color = "#ffffcc"
        label = f"**{score}**/5"
    else:
        color = "#fce4d6"
        label = f"**{score}**/5"

    st.markdown(f"""
    <div style="background-color: {color}; padding: 8px 12px; border-radius: 4px; margin-bottom: 4px; border: 1px solid #ddd;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 3; font-size: 0.85em;">{data['criterion']}</div>
            <div style="flex: 0.3; text-align: center; font-weight: bold; font-size: 1.1em;">{score if score else 'N/A'}</div>
        </div>
        <div style="font-size: 0.8em; color: #555; margin-top: 4px;">{comment}</div>
    </div>
    """, unsafe_allow_html=True)


SECTION_TITLES = {
    "1_preparatory_work": "1. Preparatory Work",
    "2_workplace_settings": "2. Workplace Settings",
    "3_teaching_materials": "3. Teaching Materials",
    "4_tech_issues": "4. Tech Issues",
    "5_time_management": "5. Time Management",
    "6_pedagogical_aspects": "6. Pedagogical Aspects",
    "7_soft_skills": "7. Soft Skills",
}

SUBSECTION_TITLES = {
    "building_initial_contact": "Building Initial Contact",
    "engagement": "Engagement",
    "material_explanation": "Material Explanation",
    "guided_practice": "Guided Practice",
    "english": "English",
    "emotionality_empathy": "Emotionality & Empathy",
    "communication": "Communication",
}


def render_report(report: dict):
    """Render the full scorecard in Streamlit."""
    scores = collect_scores(report)
    avg = round(sum(scores) / len(scores), 2) if scores else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Final Score", f"{report.get('final_score', avg)}/5")
    col2.metric("Subject", report.get("lesson_subject", "N/A"))
    col3.metric("Duration", f"{report.get('lesson_duration_observed_minutes', 'N/A')} min")

    for section_key, section_title in SECTION_TITLES.items():
        section_data = report.get(section_key, {})
        if not section_data:
            continue

        with st.expander(section_title, expanded=True):
            for item_key, item_val in section_data.items():
                if isinstance(item_val, dict) and "criterion" in item_val:
                    render_criterion(item_val)
                elif isinstance(item_val, dict):
                    sub_title = SUBSECTION_TITLES.get(item_key, item_key.replace("_", " ").title())
                    st.markdown(f"**{sub_title}**")
                    for sub_key, sub_val in item_val.items():
                        if isinstance(sub_val, dict) and "criterion" in sub_val:
                            render_criterion(sub_val)


# --- Pages ---
def page_analyze():
    st.header("Analyze Lesson")

    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        st.warning("Set your Gemini API key in the sidebar first.")
        return

    model = st.selectbox("Model", ["gemini-2.5-pro", "gemini-2.5-flash"], index=0)
    booking_id = st.text_input("Booking ID (optional)", placeholder="e.g. 2957277")
    tutor_name = st.text_input("Tutor Name (optional)", placeholder="e.g. John Smith")

    uploaded_file = st.file_uploader("Upload lesson video", type=["mp4", "webm", "mov"])

    if uploaded_file and st.button("Analyze Lesson", type="primary"):
        with st.spinner("Uploading and analyzing video... This takes 2-5 minutes."):
            # Save uploaded file to temp
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            try:
                os.environ["GEMINI_API_KEY"] = api_key
                report = analyze_lesson(tmp_path, model)

                # Save JSON report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_stem = uploaded_file.name.rsplit(".", 1)[0]
                json_path = REPORTS_DIR / f"{video_stem}_{timestamp}.json"
                pdf_path = REPORTS_DIR / f"{video_stem}_{timestamp}.pdf"

                with open(json_path, "w") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                generate_pdf(report, uploaded_file.name, str(pdf_path))

                # Save to DB
                conn = init_db()
                save_lesson(conn, {
                    "video_name": uploaded_file.name,
                    "booking_id": booking_id or None,
                    "tutor_name": tutor_name or None,
                    "subject": report.get("lesson_subject", "UNKNOWN"),
                    "duration": report.get("lesson_duration_observed_minutes", 0),
                    "final_score": report.get("final_score", 0),
                    "model": model,
                    "report_json": json.dumps(report, ensure_ascii=False),
                    "pdf_path": str(pdf_path),
                })
                conn.close()

                st.success(f"Analysis complete! Score: **{report.get('final_score', 0)}/5**")

                # Show report
                render_report(report)

                # Download PDF
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF Report",
                        data=f.read(),
                        file_name=pdf_path.name,
                        mime="application/pdf",
                    )

            finally:
                os.unlink(tmp_path)


def page_history():
    st.header("Lesson History")

    conn = init_db()
    lessons = get_all_lessons(conn)

    if not lessons:
        st.info("No lessons analyzed yet. Go to 'Analyze Lesson' to get started.")
        return

    # Summary metrics
    scores = [l[6] for l in lessons if l[6]]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Lessons", len(lessons))
    col2.metric("Avg AI Score", f"{sum(scores) / len(scores):.2f}/5" if scores else "N/A")
    human_scores = [l[7] for l in lessons if l[7]]
    col3.metric("Avg Human Score", f"{sum(human_scores) / len(human_scores):.2f}/5" if human_scores else "N/A")

    # Table
    st.markdown("---")
    for lesson in lessons:
        lid, name, bid, tutor, subject, dur, ai_score, human_score, model, analyzed = lesson
        score_color = "🟢" if ai_score and ai_score >= 4 else ("🟡" if ai_score and ai_score >= 3 else "🔴")

        with st.expander(f"{score_color} **{ai_score}/5** — {name} ({subject or 'N/A'}, {dur}min) — {analyzed[:16]}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Tutor:** {tutor or 'N/A'}")
            col1.write(f"**Booking ID:** {bid or 'N/A'}")
            col2.write(f"**Model:** {model}")
            col2.write(f"**Human Score:** {human_score or 'Not reviewed'}")

            # Load full report
            result = get_lesson_report(conn, lid)
            if result:
                report_json, pdf_path, h_score, h_feedback = result
                report = json.loads(report_json)
                render_report(report)

                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "Download PDF",
                            data=f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"pdf_{lid}",
                        )

    conn.close()


def page_feedback():
    st.header("Review & Calibrate")
    st.write("Adjust AI scores to help calibrate the model. Your feedback is saved for future prompt improvements.")

    conn = init_db()
    lessons = get_all_lessons(conn)

    if not lessons:
        st.info("No lessons to review yet.")
        return

    # Filter to unreviewed
    unreviewed = [l for l in lessons if l[7] is None]
    reviewed = [l for l in lessons if l[7] is not None]

    tab1, tab2 = st.tabs([f"Needs Review ({len(unreviewed)})", f"Reviewed ({len(reviewed)})"])

    with tab1:
        for lesson in unreviewed:
            lid, name, bid, tutor, subject, dur, ai_score, _, model, analyzed = lesson
            with st.expander(f"**{name}** — AI Score: {ai_score}/5"):
                result = get_lesson_report(conn, lid)
                if result:
                    report = json.loads(result[0])
                    render_report(report)

                    st.markdown("---")
                    st.subheader("Your Review")
                    human_score = st.slider(
                        "Your overall score",
                        1.0, 5.0, float(ai_score or 3.0), 0.1,
                        key=f"score_{lid}"
                    )
                    feedback = st.text_area(
                        "What did the AI get wrong?",
                        placeholder="e.g. 'AI scored engagement too high — student was clearly distracted at 15:00'",
                        key=f"feedback_{lid}"
                    )
                    if st.button("Save Review", key=f"save_{lid}"):
                        update_human_feedback(conn, lid, human_score, feedback)
                        st.success("Review saved!")
                        st.rerun()

    with tab2:
        if reviewed:
            for lesson in reviewed:
                lid, name, bid, tutor, subject, dur, ai_score, human_score, model, analyzed = lesson
                diff = round(ai_score - human_score, 2) if ai_score and human_score else 0
                direction = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
                st.write(f"**{name}** — AI: {ai_score} | Human: {human_score} | Diff: {direction} {abs(diff)}")
        else:
            st.info("No reviewed lessons yet.")

    conn.close()


# --- Main ---
def main():
    st.set_page_config(
        page_title="Brighterly Lesson QA",
        page_icon="📋",
        layout="wide",
    )

    st.sidebar.title("📋 Lesson QA")
    st.sidebar.markdown("---")

    # API Key — prefer Streamlit secrets, fallback to manual input
    default_key = ""
    try:
        default_key = st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass

    if default_key:
        st.session_state["gemini_api_key"] = default_key
        st.sidebar.success("API key loaded from secrets")
    else:
        api_key = st.sidebar.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.get("gemini_api_key", ""),
        )
        if api_key:
            st.session_state["gemini_api_key"] = api_key

    st.sidebar.markdown("---")

    page = st.sidebar.radio("Navigation", ["Analyze Lesson", "History", "Review & Calibrate"])

    if page == "Analyze Lesson":
        page_analyze()
    elif page == "History":
        page_history()
    elif page == "Review & Calibrate":
        page_feedback()


if __name__ == "__main__":
    main()
