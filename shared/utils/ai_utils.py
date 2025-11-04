from bs4 import BeautifulSoup
from openai import OpenAI
import json
import os
import re
from datetime import datetime

def sanitize_activity_config(config: dict) -> dict:
    def format_ts(ts):
        try:
            return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M') if ts else None
        except Exception:
            return None

    clean = {}
    field_map = {
        "maxattempts": "Max Attempts",
        "duedate": "Due Date",
        "allowsubmissionsfromdate": "Submission Opens",
        "cutoffdate": "Cutoff Date",
        "gradingduedate": "Grading Due",
        "grade": "Grade",
        "teamsubmission": "Team Submission",
        "submissiondrafts": "Allow Drafts",
        "requiresubmissionstatement": "Submission Statement Required",
        "blindmarking": "Blind Marking"
    }

    for key, label in field_map.items():
        value = config.get(key)
        if isinstance(value, (int, float)) and value == 0:
            continue
        if 'date' in key or 'time' in key:
            value = format_ts(value)
        if value is not None:
            clean[label] = value

    if 'start_date' in config:
        clean["Start Date"] = format_ts(config['start_date'])
    if 'end_date' in config:
        clean["End Date"] = format_ts(config['end_date'])

    # Add summarized plugin data
    if 'assignsubmission_file' in config and config['assignsubmission_file'].get('enabled'):
        f = config['assignsubmission_file']
        files = f.get("maxfilesubmissions", 0)
        size = f.get("maxsubmissionsizebytes", 0)
        clean["File Uploads"] = f"{files} files, size: {size / 1024**2:.1f} MB" if size else f"{files} files"

    if 'assignsubmission_onlinetext' in config and config['assignsubmission_onlinetext'].get('enabled'):
        t = config['assignsubmission_onlinetext']
        wl = t.get("wordlimitenabled", 0)
        clean["Online Text"] = "enabled" + (f", limit: {t.get('wordlimit')}" if wl else "")

    return clean

async def generate_ai_response(
        course_name: str,
        course_summary: str,
        course_start_date: str,
        course_end_date: str,
        activities: list,
        max_tags: int = 10
    ) -> dict:
    """
    Use OpenAI to generate a list of relevant tags for a Moodle course.
    """
    # TODO connect gdws models.
    activity_descriptions = []
    for a in activities:
        if isinstance(a, dict):
            name = a.get("module_name", "")
            type_ = a.get("type", "")
            intro = a.get("intro", "")
            activity_config = a.get("activity_config", {})
        else:
            name = getattr(a, "module_name", "")
            type_ = getattr(a, "type", "")
            intro = getattr(a, "intro", "")
            activity_config = getattr(a, "activity_config", {})

        # Simplify enum-looking types
        type_str = str(type_).split(":")[-1].strip(" >'")  # from <LearningResourceType.XYZ: 'xyz'> to xyz
        intro_snippet = BeautifulSoup(intro or "", "html.parser").get_text().strip()[:100]  # Shortened and cleaned

        config_summary = sanitize_activity_config(activity_config)
        config_str = "; ".join(f"{k}: {v}" for k, v in config_summary.items()) if config_summary else ""

        activity_descriptions.append(f"{name} ({type_str}) - {intro_snippet}" + (f"\n  Config: {config_str}" if config_str else ""))

    activities_text = "\n".join(activity_descriptions)

    prompt = f"""
    You are an expert in educational technology.

    Given the following Moodle course details:

    Course Title: {course_name}
    Course Summary: {course_summary}
    Course Start Date: {course_start_date}
    Course End Date: {course_end_date}

    Activities:
    {activities_text}

    Perform four tasks and clearly label each section:

    **Tags:**
    Generate up to {max_tags} descriptive, relevant tags (JSON array). Each tag should be 1–3 words long and useful for search/metadata.

    **Didactical Evaluation:**
    Evaluate the didactical structure of the course. Consider the variety and appropriateness of activity types, flow, assessment opportunities, and potential improvements.

    **Restructuring Suggestions:**
    If necessary, suggest a better ordering or restructuring of the activities to improve didactical flow and clarity. Clearly explain your reasoning and list a recommended new order or grouping of activities.

    **User Flow Timeline:**
    Based on the available start and end dates of the activities (if provided), determine a recommended order in which students should complete the activities. For each activity,
    estimate an approximate duration (in weeks, days, or hours — choose the most appropriate unit) and include an uncertainty margin (e.g., "± 1 day").
    Do **not** include absolute start or end dates. Assume that students progress **linearly**, completing one activity at a time. For each activity, give me one estimation duration.

    Output a JSON array with this format:

    [
    {{
        "name": "Activity Title",
        "estimated_duration": "x weeks/days/hours ± y weeks/days/hours",
        "notes": "Brief rationale or purpose"
    }},
    ...
    ]
    """

    client = OpenAI(
        api_key = os.getenv("OPENAI_API_KEY"),
        base_url = os.getenv("OPENAI_BASE_URL")
    )


    # return {
    #     "tags": ['German Language', 'Language Course', 'Online Learning', 'Moodle Course', 'Announcements', 'Resource Files', 'Assignments', 'Interactive Lessons', 'Course Booking', 'Choice Activities'],
    #     "didactical_evaluation": 'The course "Deutscher Kurs" presents a variety of activity types, which is beneficial for maintaining student engagement and catering to different learning styles. The use of forums for announcements helps to foster a sense of community and keep students informed. The availability of resource files, presumably related to the course content, provides a self-study element that can be accessed at the student\'s convenience.\n\nAssignments and interactive lessons are crucial for active learning and for assessing the students\' understanding of the course material. The booking activity could be a useful tool if it is used for scheduling tutoring sessions or group discussions, for example. However, without more context, its purpose is unclear.\n\nThe choice activity could be used for formative assessment, depending on how it\'s implemented. It could be used for quizzes, for instance, or for gathering student feedback.\n\nHowever, the course could benefit from more detailed descriptions of the activities. This would help students understand what is expected of them and how each activity contributes to their learning. Additionally, the course seems to lack explicit opportunities for interaction between students, such as discussion forums or group assignments. Incorporating such activities could enhance the learning experience by promoting peer learning and collaboration.'
    #     "restructuring_suggestions": 'The order of the activities seems to be random. It would be better if they were ordered in a way that logically builds on the knowledge from the previous activity. For instance, it might be more beneficial to start with 'Deutscher Kurs' (Booking) as an introductory session, followed by 'Testin Images' (Activity) to visually explain the course flow.'
    # }
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating educational metadata."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1100
        )

        content = response.choices[0].message.content.strip()

        tags = []
        didactical_eval = ""
        restructure = ""
        user_timeline = []
        try:
            # Split the response using the labels
            if all(x in content for x in ["**Tags:**", "**Didactical Evaluation:**", "**Restructuring Suggestions:**", "**User Flow Timeline:**"]):
                parts = content.split("**Didactical Evaluation:**", 1)
                tags_section = parts[0].replace("**Tags:**", "").strip()

                eval_and_rest = parts[1].split("**Restructuring Suggestions:**", 1)
                didactical_eval = eval_and_rest[0].strip()

                restructure_and_timeline = eval_and_rest[1].split("**User Flow Timeline:**", 1)
                restructure = restructure_and_timeline[0].strip()

                timeline_section = restructure_and_timeline[1].strip()
                timeline_section_clean = re.sub(r"```(?:json)?\s*", "", timeline_section).strip()
                timeline_section_clean = re.sub(r"\s*```$", "", timeline_section_clean).strip()

                # Try to parse the last JSON-like structure in tags_section
                json_start = tags_section.find("[")
                json_end = tags_section.rfind("]") + 1
                if json_start != -1 and json_end != -1:
                    tags_json = tags_section[json_start:json_end]
                    tags = json.loads(tags_json)

                json_start = timeline_section.find("[")
                json_end = timeline_section.rfind("]") + 1
                if json_start != -1 and json_end != -1:
                    user_timeline = json.loads(timeline_section[json_start:json_end])

        except Exception as e:
            print(f"Parsing error: {e}")

        return {
            "tags": tags,
            "didactical_evaluation": didactical_eval,
            "restructuring_suggestions": restructure,
            "user_timeline": user_timeline
        }
    except Exception as e:
        print(f"OpenAI error: {e}")
        return []