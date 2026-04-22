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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scoring_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_text TEXT NOT NULL,
            category TEXT,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS criterion_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER,
            criterion_key TEXT,
            ai_score INTEGER,
            human_score INTEGER,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_id) REFERENCES lessons(id)
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


# --- Rules ---
def get_active_rules(conn):
    cursor = conn.execute("""
        SELECT id, rule_text, category, source, created_at
        FROM scoring_rules WHERE status = 'active' ORDER BY created_at DESC
    """)
    return cursor.fetchall()


def add_rule(conn, rule_text: str, category: str = "general", source: str = "manual"):
    conn.execute("""
        INSERT INTO scoring_rules (rule_text, category, source) VALUES (?, ?, ?)
    """, (rule_text, category, source))
    conn.commit()


def delete_rule(conn, rule_id: int):
    conn.execute("UPDATE scoring_rules SET status = 'disabled' WHERE id = ?", (rule_id,))
    conn.commit()


def save_criterion_feedback(conn, lesson_id: int, criterion_key: str,
                            ai_score: int, human_score: int, feedback: str):
    conn.execute("""
        INSERT INTO criterion_feedback (lesson_id, criterion_key, ai_score, human_score, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (lesson_id, criterion_key, ai_score, human_score, feedback))
    conn.commit()


def get_rules_for_prompt(conn) -> str:
    """Build a rules string to inject into the QA rubric prompt."""
    rules = get_active_rules(conn)
    if not rules:
        return ""
    lines = ["## MANDATORY SCORING RULES", "Apply these rules strictly when scoring. They override general guidelines.", ""]
    for _, text, category, _, _ in rules:
        lines.append(f"- [{category.upper()}] {text}")
    return "\n".join(lines)


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
        bg_color = "#e0e0e0"
        text_color = "#666"
        score_bg = "#ccc"
    elif score >= 5:
        bg_color = "#d4edda"
        text_color = "#1a1a1a"
        score_bg = "#28a745"
    elif score >= 3:
        bg_color = "#fff3e0"
        text_color = "#1a1a1a"
        score_bg = "#f57c00"
    else:
        bg_color = "#fde0dc"
        text_color = "#1a1a1a"
        score_bg = "#d32f2f"

    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 10px 14px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #ccc;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 3; font-size: 0.85em; color: {text_color};">{data['criterion']}</div>
            <div style="flex: 0; min-width: 36px; text-align: center; font-weight: bold; font-size: 1.0em; color: #fff; background-color: {score_bg}; border-radius: 4px; padding: 2px 8px;">{score if score else 'N/A'}</div>
        </div>
        <div style="font-size: 0.8em; color: #333; margin-top: 6px;">{comment}</div>
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
                conn = init_db()
                rules_text = get_rules_for_prompt(conn)
                conn.close()
                report = analyze_lesson(tmp_path, model, extra_rules=rules_text)

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


def extract_criteria_flat(report, prefix=""):
    """Extract all criteria as flat list with keys for per-criterion feedback."""
    items = []
    if isinstance(report, dict):
        if "criterion" in report and "score" in report:
            items.append((prefix, report))
        else:
            for k, v in report.items():
                if k in ("lesson_subject", "lesson_duration_observed_minutes", "final_score"):
                    continue
                items.extend(extract_criteria_flat(v, f"{prefix}.{k}" if prefix else k))
    return items


def page_feedback():
    st.header("Review & Calibrate")

    conn = init_db()

    tab_review, tab_rules, tab_history = st.tabs(["Review Lessons", "Scoring Rules", "Review History"])

    # --- TAB 1: Review lessons with per-criterion feedback ---
    with tab_review:
        lessons = get_all_lessons(conn)
        unreviewed = [l for l in lessons if l[7] is None]

        if not unreviewed:
            st.info("No lessons to review. Analyze some lessons first!")
        else:
            st.write(f"**{len(unreviewed)} lessons** waiting for review")

            for lesson in unreviewed:
                lid, name, bid, tutor, subject, dur, ai_score, _, model, analyzed = lesson
                with st.expander(f"**{name}** — AI: {ai_score}/5 — {subject or 'N/A'} — {analyzed[:16]}"):
                    result = get_lesson_report(conn, lid)
                    if not result:
                        continue

                    report = json.loads(result[0])

                    # Overall score adjustment
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        human_score = st.slider(
                            "Your overall score",
                            1.0, 5.0, float(ai_score or 3.0), 0.1,
                            key=f"score_{lid}"
                        )
                    with col2:
                        overall_feedback = st.text_area(
                            "Overall feedback",
                            placeholder="General notes about AI accuracy...",
                            key=f"overall_{lid}"
                        )

                    # Per-criterion review
                    st.markdown("---")
                    st.markdown("**Per-criterion adjustments** (only fill in where AI was wrong)")

                    criteria = extract_criteria_flat(report)
                    corrections = []

                    for crit_key, crit_data in criteria:
                        ai_s = crit_data.get("score")
                        if ai_s is None:
                            continue

                        short_name = crit_key.split(".")[-1].replace("_", " ").title()
                        with st.container():
                            cols = st.columns([3, 1, 1, 3])
                            cols[0].markdown(f"<small>{crit_data['criterion'][:80]}...</small>" if len(crit_data['criterion']) > 80 else f"<small>{crit_data['criterion']}</small>", unsafe_allow_html=True)
                            cols[1].markdown(f"AI: **{ai_s}**")
                            new_score = cols[2].selectbox(
                                "Your score",
                                [None, 1, 2, 3, 4, 5],
                                index=0,
                                key=f"crit_{lid}_{crit_key}",
                                format_func=lambda x: "-" if x is None else str(x)
                            )
                            crit_note = cols[3].text_input(
                                "Note",
                                placeholder="Why is AI wrong here?",
                                key=f"note_{lid}_{crit_key}",
                                label_visibility="collapsed"
                            )
                            if new_score is not None:
                                corrections.append((crit_key, ai_s, new_score, crit_note))

                    # Suggest rule from corrections
                    if corrections:
                        st.markdown("---")
                        st.markdown("**Suggested rules from your corrections:**")
                        for crit_key, ai_s, human_s, note in corrections:
                            short = crit_key.split(".")[-1].replace("_", " ")
                            direction = "too high" if ai_s > human_s else "too low"
                            suggestion = f"For '{short}': AI scored {ai_s}, should be {human_s}."
                            if note:
                                suggestion += f" Reason: {note}"
                            st.info(f"Rule suggestion: {suggestion}")

                    st.markdown("---")
                    if st.button("Save Review", key=f"save_{lid}", type="primary"):
                        # Save overall
                        update_human_feedback(conn, lid, human_score, overall_feedback)
                        # Save per-criterion
                        for crit_key, ai_s, human_s, note in corrections:
                            save_criterion_feedback(conn, lid, crit_key, ai_s, human_s, note)
                        st.success("Review saved! Check 'Scoring Rules' tab to create rules from your feedback.")
                        st.rerun()

    # --- TAB 2: Scoring rules management ---
    with tab_rules:
        st.subheader("Active Scoring Rules")
        st.write("These rules are injected into every analysis prompt. They override the AI's default scoring behavior.")

        rules = get_active_rules(conn)

        if rules:
            for rid, text, category, source, created in rules:
                cols = st.columns([1, 5, 1])
                cols[0].markdown(f"`{category}`")
                cols[1].write(text)
                if cols[2].button("Remove", key=f"del_rule_{rid}"):
                    delete_rule(conn, rid)
                    st.rerun()
        else:
            st.info("No active rules yet. Add rules below or they'll be suggested from reviews.")

        # Add new rule manually
        st.markdown("---")
        st.subheader("Add New Rule")

        CATEGORIES = [
            "engagement", "communication", "time_management", "workplace",
            "teaching_materials", "pedagogical", "soft_skills", "tech_issues", "general"
        ]

        col1, col2 = st.columns([3, 1])
        new_rule = col1.text_area(
            "Rule",
            placeholder="e.g. 'If silence pauses >20 seconds occur more than 3 times, communication score must be 1 or 2'",
            key="new_rule_text"
        )
        new_category = col2.selectbox("Category", CATEGORIES, key="new_rule_cat")

        if st.button("Add Rule", type="primary") and new_rule.strip():
            add_rule(conn, new_rule.strip(), new_category)
            st.success("Rule added! It will be applied to all future analyses.")
            st.rerun()

        # Show suggestions from past criterion feedback
        st.markdown("---")
        st.subheader("Suggested Rules from Reviews")

        cursor = conn.execute("""
            SELECT criterion_key, ai_score, human_score, feedback,
                   COUNT(*) as occurrences
            FROM criterion_feedback
            WHERE ai_score != human_score
            GROUP BY criterion_key,
                     CASE WHEN ai_score > human_score THEN 'over' ELSE 'under' END
            HAVING occurrences >= 1
            ORDER BY occurrences DESC
            LIMIT 10
        """)
        suggestions = cursor.fetchall()

        if suggestions:
            for crit_key, ai_s, human_s, feedback, count in suggestions:
                short = crit_key.split(".")[-1].replace("_", " ")
                direction = "overscores" if ai_s > human_s else "underscores"
                suggestion = f"AI {direction} '{short}' (AI gave {ai_s}, human gave {human_s})"
                if feedback:
                    suggestion += f" — {feedback}"

                cols = st.columns([5, 1])
                cols[0].write(f"({count}x) {suggestion}")
                if cols[1].button("Add as Rule", key=f"suggest_{crit_key}_{ai_s}_{human_s}"):
                    rule_text = f"For '{short}': {feedback}" if feedback else suggestion
                    add_rule(conn, rule_text, crit_key.split(".")[0] if "." in crit_key else "general", "auto")
                    st.success("Rule created from suggestion!")
                    st.rerun()
        else:
            st.info("No suggestions yet. Review some lessons first — patterns will appear here.")

    # --- TAB 3: Review history ---
    with tab_history:
        lessons = get_all_lessons(conn)
        reviewed = [l for l in lessons if l[7] is not None]

        if not reviewed:
            st.info("No reviewed lessons yet.")
        else:
            st.subheader("Accuracy Overview")
            diffs = []
            for l in reviewed:
                ai_s, human_s = l[6], l[7]
                if ai_s and human_s:
                    diffs.append(ai_s - human_s)

            if diffs:
                avg_diff = sum(diffs) / len(diffs)
                col1, col2, col3 = st.columns(3)
                col1.metric("Reviewed Lessons", len(reviewed))
                col2.metric("Avg AI-Human Diff", f"{avg_diff:+.2f}")
                col3.metric("Accuracy", f"{100 - abs(avg_diff) / 5 * 100:.0f}%")

            st.markdown("---")
            for lesson in reviewed:
                lid, name, bid, tutor, subject, dur, ai_score, human_score, model, analyzed = lesson
                diff = round(ai_score - human_score, 2) if ai_score and human_score else 0
                icon = "🔴" if abs(diff) > 1 else ("🟡" if abs(diff) > 0.5 else "🟢")
                st.write(f"{icon} **{name}** — AI: {ai_score} | Human: {human_score} | Diff: {diff:+.2f}")

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
