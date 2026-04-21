"""
Lesson QA Analyzer — PoC
Uploads a lesson recording to Gemini and generates a QA scorecard
matching the Brighterly human QA format.
"""

import os
import sys
import json
import time
import subprocess
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: Set GEMINI_API_KEY environment variable")
    sys.exit(1)

QA_RUBRIC = """
You are a Quality Assurance analyst for Brighterly, an online math and reading tutoring platform for K-12 students (ages 5-14).

You are reviewing a recorded video of a PAID tutoring lesson.
The scheduled lesson duration is {duration_minutes} minutes.

CRITICAL: You MUST watch and analyze the ENTIRE video from start to finish — all {duration_minutes} minutes.
Do NOT stop early or skip sections. Pay attention to what happens throughout the full recording.

Score each criterion on a 1-5 scale:
- 1-2 = Below expectations
- 3-4 = Target
- 5 = Exceeded expectations

If a criterion cannot be evaluated from the video (e.g. NearPod-specific items when NearPod is not used), set score to null and comment "not evaluated".

Return your analysis as JSON with this EXACT structure:

{
  "lesson_subject": "MATH or READING/ELA or UNKNOWN",
  "lesson_duration_observed_minutes": <number>,
  "final_score": <average of all scored criteria, rounded to 2 decimals>,

  "1_preparatory_work": {
    "topic_familiarity": {
      "criterion": "Teacher does not display unfamiliarity with the topic & lesson content and appears to have studied lesson & script prior to the lesson",
      "score": <1-5>,
      "comment": "<specific observation>"
    }
  },

  "2_workplace_settings": {
    "lighting": {
      "criterion": "Workplace is well-lit & not dim",
      "score": <1-5>,
      "comment": "<specific observation>"
    },
    "camera_position": {
      "criterion": "Teacher is at an appropriate distance & in central position from the camera",
      "score": <1-5>,
      "comment": "<specific observation about distance, posture, visibility of upper torso and hand gestures>"
    },
    "background_noise": {
      "criterion": "Teacher has no background noises",
      "score": <1-5>,
      "comment": "<specific observation>"
    },
    "no_virtual_background": {
      "criterion": "Teacher does not use virtual background",
      "score": <1-5>,
      "comment": "<specific observation>"
    },
    "physical_background": {
      "criterion": "Teacher has a creative, colorful physical background",
      "score": <1-5>,
      "comment": "<specific observation about background quality, empty spaces, professionalism>"
    },
    "appearance": {
      "criterion": "Teacher has appropriate appearance and looks professional for a teacher",
      "score": <1-5>,
      "comment": "<specific observation about grooming, attentiveness, yawning, looking down, leaving student unattended>"
    }
  },

  "3_teaching_materials": {
    "nearpod_usage": {
      "criterion": "Teacher is thoroughly aware of how to use NearPod",
      "score": <1-5 or null>,
      "comment": "<observation or 'not evaluated - not NearPod'>"
    },
    "activity_reminders": {
      "criterion": "Teacher always reminds the student how to work in every type of activity",
      "score": <1-5 or null>,
      "comment": "<observation or 'not evaluated - not NearPod'>"
    },
    "no_skipped_slides": {
      "criterion": "The teacher does not skip any slides for no evident reasons",
      "score": <1-5 or null>,
      "comment": "<observation or 'not evaluated - not NearPod'>"
    },
    "lesson_structure_knowledge": {
      "criterion": "Teacher knows from the script what is expected to be done at each slide. Lesson structure: greetings → screen sharing → plan for today → theory explanation → activities → brain break → activities → recap",
      "score": <1-5>,
      "comment": "<specific observation about lesson flow and structure>"
    }
  },

  "4_tech_issues": {
    "composure": {
      "criterion": "Teacher does not get lost in case of tech issues",
      "score": <1-5 or null>,
      "comment": "<observation or 'no tech issues'>"
    },
    "expertise": {
      "criterion": "Teacher confidently and with apparent expertise handles cases of technical issues",
      "score": <1-5 or null>,
      "comment": "<observation or 'no tech issues'>"
    },
    "learning_time_priority": {
      "criterion": "Teacher prioritizes learning time in case of tech issues and shares screen if they cannot sort out tech issue",
      "score": <1-5 or null>,
      "comment": "<observation or 'no tech issues'>"
    }
  },

  "5_time_management": {
    "lesson_duration": {
      "criterion": "Teacher delivers a lesson that is no shorter than 45 minutes and does not exceed 60 min; target time is 45 mins",
      "score": <1-5>,
      "comment": "<exact observed duration>"
    },
    "time_distribution": {
      "criterion": "Teacher does not deviate from time prescribed in the script & does not spend too much time on certain parts and barely touching on others without reasonable reasons",
      "score": <1-5 or null>,
      "comment": "<observation about pacing across lesson sections>"
    }
  },

  "6_pedagogical_aspects": {
    "building_initial_contact": {
      "small_talk": {
        "criterion": "Teacher shows natural interest and emotionality in first contact, initiates small talk, utilizes knowledge of the kid gained from previous lessons, and creates a comfortable atmosphere",
        "score": <1-5>,
        "comment": "<specific observation about first 2-3 minutes, warmth, questions about student's day>"
      }
    },
    "engagement": {
      "no_long_monologues": {
        "criterion": "Teacher never speaks for long periods of time (>30s) without any engagement questions",
        "score": <1-5>,
        "comment": "<observation about teacher-student speaking ratio>"
      },
      "checks_understanding": {
        "criterion": "Teacher frequently confirms with the kid if they understand everything with emotions",
        "score": <1-5>,
        "comment": "<observation about comprehension checks and letting student reason through responses>"
      },
      "diverse_engagement": {
        "criterion": "Teacher's engagement is always diverse and emotional",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "praise": {
        "criterion": "Teacher frequently praises the kid in various formats",
        "score": <1-5>,
        "comment": "<observation about verbal praise, clapping, thumbs-up, variety of reinforcement>"
      },
      "props_usage": {
        "criterion": "Teacher uses props for engagement, entertainment, and praising purposes",
        "score": <1-5>,
        "comment": "<observation about physical props or rewards>"
      }
    },
    "material_explanation": {
      "topic_understanding": {
        "criterion": "Teacher shows good understanding of the lesson topic and presents the material with confidence and without errors",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "simple_terms": {
        "criterion": "Teacher always explains the topic in simple terms that would be understandable to a kid and adjusts to the kid's knowledge level",
        "score": <1-5>,
        "comment": "<observation about age-appropriate language and providing theory before activities>"
      },
      "reacts_to_confusion": {
        "criterion": "Teacher always reacts to a kid's verbal or non-verbal signs of misunderstanding of the material and goes back to explain the material again",
        "score": <1-5>,
        "comment": "<observation about attentiveness to student confusion>"
      },
      "visualization": {
        "criterion": "Teacher frequently visualizes the material with props or whiteboard",
        "score": <1-5 or null>,
        "comment": "<observation or 'not evaluated - not NearPod'>"
      }
    },
    "guided_practice": {
      "activity_instructions": {
        "criterion": "Teacher always guides the student how to start an activity and gives instructions throughout activities",
        "score": <1-5>,
        "comment": "<observation about clarity of instructions before and during tasks>"
      },
      "no_giving_answers": {
        "criterion": "Teacher never gives away answers to the kid instead of giving hints, unless the student is struggling",
        "score": <1-5>,
        "comment": "<observation about using prompts and guiding questions vs giving answers>"
      },
      "knowledge_level_adjustment": {
        "criterion": "Teacher shows consideration of the kid's knowledge level to adjust guided practice",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "theory_to_practice": {
        "criterion": "Teacher frequently ties theory to practice",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "recap": {
        "criterion": "Teacher always includes recap after theory and practice",
        "score": <1-5>,
        "comment": "<observation about end-of-lesson summary and reinforcement of key points>"
      }
    }
  },

  "7_soft_skills": {
    "english": {
      "fluency": {
        "criterion": "Teacher operates fluent English with strong confidence",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "accent": {
        "criterion": "Accent is insignificant and hardly audible",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "word_choice": {
        "criterion": "There are no cases of poor word choice when explaining information",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "word_fillers": {
        "criterion": "Word-fillers like 'ugh' are absent",
        "score": <1-5>,
        "comment": "<note any specific fillers observed>"
      }
    },
    "emotionality_empathy": {
      "emotional_display": {
        "criterion": "Teacher displays strong emotions with great variation of emotions, including facial expressions, voice variations, and body language",
        "score": <1-5>,
        "comment": "<observation about energy, expressiveness, dynamism>"
      },
      "authenticity": {
        "criterion": "Emotions and their variability do not appear limited or artificial",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "confidence": {
        "criterion": "Nervousness and unconfidence are excluded",
        "score": <1-5>,
        "comment": "<observation>"
      }
    },
    "communication": {
      "active_communication": {
        "criterion": "Teacher communicates very actively and frequently and does not allow silence pauses (of >20s)",
        "score": <1-5>,
        "comment": "<observation about silence periods, their duration and timestamps>"
      },
      "natural_interest": {
        "criterion": "Interest in communication is natural and vivid",
        "score": <1-5>,
        "comment": "<observation>"
      },
      "reacts_to_student": {
        "criterion": "Teacher actively and always reacts to kid's responses or interests",
        "score": <1-5>,
        "comment": "<observation>"
      }
    }
  }
}

IMPORTANT RULES:
- Be specific with timestamps in comments where relevant.
- Comments should be actionable — explain what was good or what needs improvement.
- If NearPod is not used, mark NearPod-specific criteria as null with "not evaluated - not NearPod".
- If no tech issues occurred, mark tech criteria as null with "no tech issues".
- Calculate final_score as the average of ALL non-null scores.
- Return ONLY valid JSON, no markdown fences.
"""


def get_video_duration_minutes(video_path: str) -> int:
    """Get video duration in minutes. Tries ffprobe, then macOS mdls, then defaults to 45."""
    # Try ffprobe first (works on Linux / Streamlit Cloud)
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            seconds = float(result.stdout.strip())
            return round(seconds / 60)
    except FileNotFoundError:
        pass

    # Try macOS mdls
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemDurationSeconds", video_path],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if "kMDItemDurationSeconds" in line and "(null)" not in line:
                seconds = float(line.split("=")[1].strip())
                return round(seconds / 60)
    except FileNotFoundError:
        pass

    return 45  # default assumption


def analyze_lesson(video_path: str, model: str = "gemini-2.5-pro") -> dict:
    """Upload video to Gemini and get QA analysis."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    duration_minutes = get_video_duration_minutes(video_path)
    print(f"Detected video duration: {duration_minutes} minutes")

    print(f"Uploading {video_path} to Gemini...")
    video_file = client.files.upload(file=video_path)

    while video_file.state.name == "PROCESSING":
        print("  Processing video...")
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise RuntimeError(f"Video processing failed: {video_file.state}")

    print(f"  Video ready ({video_file.state.name})")
    print(f"Analyzing lesson with {model}...")

    rubric = QA_RUBRIC.replace("{duration_minutes}", str(duration_minutes))

    response = client.models.generate_content(
        model=model,
        contents=[video_file, rubric],
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    report = json.loads(text)

    try:
        client.files.delete(name=video_file.name)
    except Exception:
        pass

    return report


def collect_scores(obj):
    """Recursively collect all scores from the nested report."""
    scores = []
    if isinstance(obj, dict):
        if "score" in obj and obj["score"] is not None:
            scores.append(obj["score"])
        for v in obj.values():
            scores.extend(collect_scores(v))
    return scores


def print_section(title, data, indent=0):
    """Print a section of the scorecard."""
    prefix = "  " * indent
    if isinstance(data, dict) and "score" in data:
        score = data.get("score")
        score_str = f"{score}/5" if score is not None else "N/A"
        label = "⬇️" if score and score <= 2 else ("✅" if score and score >= 4 else "➡️")
        if score is None:
            label = "⬜"
        print(f"{prefix}{label} {data.get('criterion', title)}")
        print(f"{prefix}   Score: {score_str}")
        comment = data.get("comment", "")
        if comment:
            print(f"{prefix}   Comment: {comment}")
        print()
    else:
        print(f"\n{prefix}{'=' * 50}")
        print(f"{prefix}  {title.upper()}")
        print(f"{prefix}{'=' * 50}")
        if isinstance(data, dict):
            for key, val in data.items():
                if key in ("criterion", "score", "comment"):
                    continue
                nice_key = key.replace("_", " ").title()
                print_section(nice_key, val, indent + 1)


def print_report(report: dict, video_path: str):
    """Pretty-print QA scorecard."""
    print("\n" + "=" * 60)
    print("  BRIGHTERLY LESSON QA SCORECARD")
    print("=" * 60)
    print(f"  Video: {os.path.basename(video_path)}")
    print(f"  Subject: {report.get('lesson_subject', 'N/A')}")
    print(f"  Duration observed: {report.get('lesson_duration_observed_minutes', 'N/A')} min")

    scores = collect_scores(report)
    calculated_avg = round(sum(scores) / len(scores), 2) if scores else 0
    final = report.get("final_score", calculated_avg)

    print(f"  Final Score: {final}/5 ({len(scores)} criteria scored)")
    print("=" * 60)

    section_names = {
        "1_preparatory_work": "1. Preparatory Work Before the Lesson",
        "2_workplace_settings": "2. Workplace Settings",
        "3_teaching_materials": "3. Teaching Materials Application",
        "4_tech_issues": "4. Tech Issues",
        "5_time_management": "5. Time Management",
        "6_pedagogical_aspects": "6. Pedagogical Aspects",
        "7_soft_skills": "7. Soft Skills",
    }

    for key, title in section_names.items():
        if key in report:
            print_section(title, report[key])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: GEMINI_API_KEY=xxx python qa_analyze.py <video_path> [model]")
        print("  model: gemini-2.5-pro (default) or gemini-2.5-flash")
        sys.exit(1)

    video_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "gemini-2.5-pro"

    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        sys.exit(1)

    report = analyze_lesson(video_path, model)

    output_path = video_path.rsplit(".", 1)[0] + "_qa_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nJSON report saved to: {output_path}")

    print_report(report, video_path)
