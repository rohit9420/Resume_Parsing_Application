"""Compatibility imports for the resume parsing service."""

from parsingapplication.resume_parser import (
    AnalysisResult,
    Experience,
    JobDescription,
    MatchResult,
    Resume,
    analyze_resume,
    extract_resume_text,
    parse_job_description,
    parse_resume,
    score_resume,
)

__all__ = [
    "AnalysisResult",
    "Experience",
    "JobDescription",
    "MatchResult",
    "Resume",
    "analyze_resume",
    "extract_resume_text",
    "parse_job_description",
    "parse_resume",
    "score_resume",
]
