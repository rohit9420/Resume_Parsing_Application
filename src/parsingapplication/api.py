from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from .resume_parser import AIResponseError, AnalysisResult, analyze_resume

MAX_RESUME_SIZE = 10 * 1024 * 1024

app = FastAPI(title="Resume Matcher API", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
) -> AnalysisResult:
    filename = resume.filename or ""
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=415,
            detail="Unsupported resume format. Upload a PDF or DOCX file.",
        )

    contents = resume.file.read(MAX_RESUME_SIZE + 1)
    if len(contents) > MAX_RESUME_SIZE:
        raise HTTPException(status_code=413, detail="Resume must be 10 MB or smaller.")
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="Job description cannot be empty.")

    try:
        return analyze_resume(filename, contents, job_description)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (AIResponseError, ValidationError) as error:
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned data that could not be processed.",
        ) from error
