"""
Generate a QA scorecard PDF matching the Brighterly human QA format.
"""

import json
import sys
import os
from fpdf import FPDF


# Colors
HEADER_BG = (74, 134, 232)      # Blue header
SECTION_BG = (255, 229, 153)    # Yellow section header
BELOW_BG = (252, 228, 214)      # Light red/orange for 1-2
TARGET_BG = (255, 255, 204)     # Light yellow for 3-4
EXCEEDED_BG = (198, 239, 206)   # Light green for 5
NA_BG = (242, 242, 242)         # Gray for N/A
WHITE = (255, 255, 255)


SECTION_TITLES = {
    "1_preparatory_work": "1. Preparatory work before the lesson",
    "2_workplace_settings": "2. Workplace settings",
    "3_teaching_materials": "3. Teaching materials application",
    "4_tech_issues": "4. Tech issues",
    "5_time_management": "5. Time management",
    "6_pedagogical_aspects": "6. Pedagogical aspects",
    "7_soft_skills": "7. Soft skills",
}

SUBSECTION_TITLES = {
    "building_initial_contact": "Building initial contact",
    "engagement": "Engagement",
    "material_explanation": "Material explanation",
    "guided_practice": "Guided practice",
    "english": "English",
    "emotionality_empathy": "Emotionality & Empathy",
    "communication": "Communication",
}


class ScoreCardPDF(FPDF):
    def __init__(self, report, video_name):
        super().__init__(orientation="L", format="A4")
        self.report = report
        self.video_name = video_name
        self.set_auto_page_break(auto=True, margin=15)

        # Column widths for landscape A4 (~277mm usable)
        self.col_criterion = 95
        self.col_below = 35
        self.col_target = 35
        self.col_exceeded = 35
        self.col_comment = 77
        self.left_margin_x = 10

    def header_row(self):
        """Draw the table header row."""
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*HEADER_BG)
        self.set_text_color(255, 255, 255)
        x = self.left_margin_x
        self.set_xy(x, self.get_y())

        headers = [
            (self.col_criterion, "Criterion"),
            (self.col_below, "Below expectations\n(1-2 pts)"),
            (self.col_target, "Target\n(3-4 pts)"),
            (self.col_exceeded, "Exceeded expectations\n(5 pts)"),
            (self.col_comment, "Comments"),
        ]
        y_start = self.get_y()
        h = 12
        for w, text in headers:
            self.set_xy(x, y_start)
            self.multi_cell(w, h / 2, text, border=1, align="C", fill=True)
            x += w
        self.set_y(y_start + h)
        self.set_text_color(0, 0, 0)

    def section_row(self, title):
        """Draw a yellow section header row."""
        self.check_page_break(10)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*SECTION_BG)
        self.set_text_color(0, 0, 0)
        total_w = self.col_criterion + self.col_below + self.col_target + self.col_exceeded + self.col_comment
        self.set_x(self.left_margin_x)
        self.cell(total_w, 8, f"  {title}", border=1, fill=True, align="L")
        self.ln()

    def subsection_row(self, title):
        """Draw a lighter subsection header."""
        self.check_page_break(8)
        self.set_font("Helvetica", "BI", 8)
        self.set_fill_color(255, 242, 204)
        self.set_text_color(0, 0, 0)
        total_w = self.col_criterion + self.col_below + self.col_target + self.col_exceeded + self.col_comment
        self.set_x(self.left_margin_x)
        self.cell(total_w, 7, f"    {title}", border=1, fill=True, align="L")
        self.ln()

    def check_page_break(self, h):
        if self.get_y() + h > self.h - 15:
            self.add_page()
            self.header_row()

    def criterion_row(self, criterion_text, score, comment):
        """Draw a single criterion row with score in the appropriate column."""
        self.set_font("Helvetica", "", 7)
        self.set_text_color(0, 0, 0)

        # Calculate row height based on content
        criterion_lines = self._count_lines(criterion_text, self.col_criterion - 2)
        comment_lines = self._count_lines(comment or "", self.col_comment - 2)
        line_h = 4
        row_h = max(criterion_lines, comment_lines, 2) * line_h

        self.check_page_break(row_h)

        y_start = self.get_y()
        x = self.left_margin_x

        # Criterion cell
        self.set_xy(x, y_start)
        self.set_fill_color(*WHITE)
        self.multi_cell(self.col_criterion, line_h, criterion_text, border=1, fill=True)
        cell_bottom = self.get_y()
        x += self.col_criterion

        # Score columns — place score number in the right column
        for col_w, score_range, bg in [
            (self.col_below, (1, 2), BELOW_BG),
            (self.col_target, (3, 4), TARGET_BG),
            (self.col_exceeded, (5, 5), EXCEEDED_BG),
        ]:
            self.set_xy(x, y_start)
            if score is not None and score_range[0] <= score <= score_range[1]:
                self.set_fill_color(*bg)
                self.set_font("Helvetica", "B", 10)
                self.cell(col_w, row_h, str(score), border=1, fill=True, align="C")
                self.set_font("Helvetica", "", 7)
            elif score is None:
                self.set_fill_color(*NA_BG)
                self.cell(col_w, row_h, "", border=1, fill=True, align="C")
            else:
                self.set_fill_color(*WHITE)
                self.cell(col_w, row_h, "", border=1, fill=True, align="C")
            x += col_w

        # Comment cell
        self.set_xy(x, y_start)
        self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "", 7)
        self.multi_cell(self.col_comment, line_h, comment or "", border=1, fill=True)
        comment_bottom = self.get_y()

        # Move to the bottom of the tallest cell
        self.set_y(max(cell_bottom, y_start + row_h, comment_bottom))

    def _count_lines(self, text, width):
        """Estimate number of lines for text in given width."""
        if not text:
            return 1
        self.set_font("Helvetica", "", 7)
        words = text.split()
        line = ""
        count = 1
        for word in words:
            test = f"{line} {word}".strip()
            if self.get_string_width(test) > width:
                count += 1
                line = word
            else:
                line = test
        return max(count, 1)

    def final_score_row(self, score):
        """Draw the final score row."""
        self.check_page_break(10)
        self.set_font("Helvetica", "B", 11)
        total_w = self.col_criterion + self.col_below + self.col_target + self.col_exceeded
        self.set_x(self.left_margin_x)
        self.set_fill_color(*SECTION_BG)
        self.cell(total_w, 10, "Final Score", border=1, fill=True, align="R")
        self.set_fill_color(*EXCEEDED_BG if score >= 4 else (*(TARGET_BG if score >= 3 else BELOW_BG),))
        self.cell(self.col_comment, 10, f"{score}", border=1, fill=True, align="C")
        self.ln()


def extract_criteria(data):
    """Recursively extract all criteria items from nested structure."""
    items = []
    if isinstance(data, dict):
        if "criterion" in data and "score" in data:
            items.append(data)
        else:
            for v in data.values():
                items.extend(extract_criteria(v))
    return items


def has_subsections(data):
    """Check if a section has nested subsections (like pedagogical_aspects)."""
    for k, v in data.items():
        if isinstance(v, dict) and "criterion" not in v:
            # Check if it contains criteria inside
            if any(isinstance(vv, dict) and "criterion" in vv for vv in v.values()):
                return True
    return False


def sanitize_text(text):
    """Replace unicode characters that latin-1 can't encode."""
    replacements = {
        "\u2192": "->",   # →
        "\u2013": "-",    # –
        "\u2014": "-",    # —
        "\u2018": "'",    # '
        "\u2019": "'",    # '
        "\u201c": '"',    # "
        "\u201d": '"',    # "
        "\u2026": "...",  # …
        "\u2022": "-",    # •
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Fallback: replace any remaining non-latin-1 chars
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(report, video_name, output_path):
    pdf = ScoreCardPDF(report, video_name)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Brighterly Lesson QA Scorecard", align="C")
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Video: {video_name}  |  Subject: {report.get('lesson_subject', 'N/A')}  |  Duration: {report.get('lesson_duration_observed_minutes', 'N/A')} min  |  Analyzed by: AI (Gemini Pro)", align="C")
    pdf.ln(8)

    # Table header
    pdf.header_row()

    # Process each section
    for section_key, section_title in SECTION_TITLES.items():
        section_data = report.get(section_key, {})
        if not section_data:
            continue

        pdf.section_row(section_title)

        # Check if section has subsections (pedagogical_aspects, soft_skills)
        for item_key, item_val in section_data.items():
            if isinstance(item_val, dict) and "criterion" in item_val:
                # Direct criterion
                pdf.criterion_row(
                    sanitize_text(item_val["criterion"]),
                    item_val.get("score"),
                    sanitize_text(item_val.get("comment", ""))
                )
            elif isinstance(item_val, dict):
                # Subsection
                sub_title = SUBSECTION_TITLES.get(item_key, item_key.replace("_", " ").title())
                pdf.subsection_row(sub_title)
                for sub_key, sub_val in item_val.items():
                    if isinstance(sub_val, dict) and "criterion" in sub_val:
                        pdf.criterion_row(
                            sanitize_text(sub_val["criterion"]),
                            sub_val.get("score"),
                            sanitize_text(sub_val.get("comment", ""))
                        )

    # Final score
    pdf.final_score_row(report.get("final_score", 0))

    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf.py <qa_report.json> [output.pdf]")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path) as f:
        report = json.load(f)

    video_name = os.path.basename(json_path).replace("_qa_report.json", ".mp4")
    output_path = sys.argv[2] if len(sys.argv) > 2 else json_path.replace(".json", ".pdf")

    generate_pdf(report, video_name, output_path)
