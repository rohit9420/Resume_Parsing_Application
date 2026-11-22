import os
import re

import requests
import streamlit as st

API_URL = os.getenv("RESUME_API_URL", "http://127.0.0.1:8000")


def _normalise_key(key: str) -> str:
    """Make result field names consistent for matching against known categories."""
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _format_value(value: object) -> str:
    """Render structured result values as readable text rather than raw JSON."""
    if value is None:
        return "Not specified"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        return " · ".join(
            f"{_format_label(str(key))}: {_format_value(item)}"
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return " · ".join(_format_value(item) for item in value) or "None listed"
    return str(value)


def _format_label(value: str) -> str:
    """Turn a field name into a human-readable table label."""
    return re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip().title()


def _status_for(key: str, value: object) -> str:
    """Choose a match symbol when the result explicitly indicates pass or fail."""
    normalized_key = _normalise_key(key)
    if any(term in normalized_key for term in ("missing", "unmatched", "notmet", "mismatch")):
        return "❌ No match"
    if isinstance(value, bool):
        return "✅ Match" if value else "❌ No match"

    text = _format_value(value).lower()
    negative = (
        "not met",
        "not satisfied",
        "does not meet",
        "does not match",
        "not matching",
        "not a match",
        "not a good match",
        "not a strong match",
        "unmet",
        "false",
        "no match",
        "mismatch",
        "poor fit",
        "weak fit",
    )
    positive = ("met", "satisfied", "meets", "true", "yes", "match", "qualified", "pass")
    if any(term in text for term in negative):
        return "❌ No match"
    if any(term in text for term in positive):
        return "✅ Match"
    return "➖ Not assessed"


def _as_items(value: object) -> list[str]:
    """Convert a skill field into individual displayable items."""
    if isinstance(value, (list, tuple)):
        return [_format_value(item) for item in value if item is not None]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _comparison_rows(details: object) -> list[dict[str, str]]:
    """Build match-status table rows from the AI's recruiter feedback."""
    if not isinstance(details, dict):
        return [{"Assessment": "Recruiter feedback", "Details": _format_value(details), "Match": "➖ Not assessed"}]

    rows = []
    for key, value in details.items():
        label = str(key)
        normalized_key = _normalise_key(label)
        if "candidate" in normalized_key and "name" in normalized_key:
            continue
        if "verdict" in normalized_key:
            continue

        is_skill_match = "skill" in normalized_key and any(
            term in normalized_key for term in ("matching", "matched")
        )
        is_skill_missing = "skill" in normalized_key and any(
            term in normalized_key for term in ("missing", "unmatched")
        )
        if is_skill_match or is_skill_missing:
            items = _as_items(value)
            if items:
                status = "✅ Match" if is_skill_match else "❌ No match"
                rows.extend(
                    {
                        "Assessment": "Matching skill" if is_skill_match else "Missing skill",
                        "Details": item,
                        "Match": status,
                    }
                    for item in items
                )
            else:
                rows.append({
                    "Assessment": _format_label(label),
                    "Details": "None identified",
                    "Match": "❌ No match" if is_skill_match else "✅ Match",
                })
            continue

        rows.append({
            "Assessment": _format_label(label),
            "Details": _format_value(value),
            "Match": _status_for(label, value),
        })

    return rows or [{
        "Assessment": "Recruiter feedback",
        "Details": "No comparison details were returned.",
        "Match": "➖ Not assessed",
    }]


def _detail_value(details: object, *search_terms: str) -> str | None:
    """Find a named recruiter detail without depending on its exact key spelling."""
    if not isinstance(details, dict):
        return None
    for key, value in details.items():
        normalized_key = _normalise_key(str(key))
        if all(term in normalized_key for term in search_terms) and value:
            return _format_value(value)
    return None


def _record_rows(record: object) -> list[dict[str, str]]:
    """Convert a parsed resume or job description into readable field/value rows."""
    if not isinstance(record, dict):
        return [{"Field": "Details", "Information": _format_value(record)}]
    return [
        {"Field": _format_label(str(key)), "Information": _format_value(value)}
        for key, value in record.items()
        if value is not None and value != [] and value != ""
    ]


st.set_page_config(page_title="Resume Matcher", layout="wide")
st.title("Resume Match Analysis")
st.caption("Compare a candidate's experience and skills with the job requirements.")

resume_file = st.file_uploader("Upload a resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area(
    "Job description",
    height=260,
    placeholder="Paste the job description here...",
)

if st.button("Analyze resume", type="primary"):
    if resume_file is None:
        st.error("Upload a PDF or DOCX resume to continue.")
    elif not job_description.strip():
        st.error("Enter a job description to continue.")
    else:
        with st.spinner("Analyzing resume..."):
            try:
                response = requests.post(
                    f"{API_URL.rstrip('/')}/analyze",
                    files={
                        "resume": (
                            resume_file.name,
                            resume_file.getvalue(),
                            resume_file.type or "application/octet-stream",
                        )
                    },
                    data={"job_description": job_description},
                    timeout=180,
                )
            except requests.RequestException as error:
                st.error(f"Could not reach the API at {API_URL}: {error}")
            else:
                if not response.ok:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    st.error(f"Analysis failed ({response.status_code}): {detail}")
                else:
                    result = response.json()
                    match = result["match"]
                    details = match.get("details", {})
                    candidate_name = _detail_value(details, "candidate", "name")
                    verdict = _detail_value(details, "verdict")

                    st.divider()
                    heading = f"Results for {candidate_name}" if candidate_name else "Analysis results"
                    st.subheader(heading)
                    st.metric("Overall match", f"{match['score']:.0f}%")
                    st.progress(max(0.0, min(float(match["score"]) / 100, 1.0)))
                    if verdict:
                        st.info(verdict)

                    st.subheader("Skills and requirements")
                    st.dataframe(
                        _comparison_rows(details),
                        hide_index=True,
                        width="stretch",
                    )

                    with st.expander("Parsed resume details"):
                        st.dataframe(
                            _record_rows(result.get("resume", {})),
                            hide_index=True,
                            width="stretch",
                        )
                    with st.expander("Parsed job description"):
                        st.dataframe(
                            _record_rows(result.get("job_description", {})),
                            hide_index=True,
                            width="stretch",
                        )
