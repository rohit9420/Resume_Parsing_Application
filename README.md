# Resume Matcher

Resume Matcher is a Streamlit frontend backed by a FastAPI service. Upload one
PDF or DOCX resume, paste a job description, and get parsed resume/job details
with an AI-generated match score and feedback.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- A Groq API key

## Setup

From the `ParsingApplication` directory:

```powershell
uv sync
$env:GROQ_API_KEY = "your-groq-api-key"
```

Keep the API key in the environment; do not commit it to source control.

## Run

Set the Groq key, then start both the API and Streamlit together:

```powershell
$env:GROQ_API_KEY = "your-groq-api-key"
.\.venv\Scripts\python.exe launch_app.py
```

The launcher waits for the API health check before opening Streamlit. Press
`Ctrl+C` to stop the frontend and API together. It uses
`http://127.0.0.1:8000` for the API.

Alternatively, start each service separately for development:

```powershell
.\.venv\Scripts\python.exe -m uvicorn parsingapplication.api:app --reload
```

In a second terminal, start Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open the Streamlit URL printed in the terminal. To use a different API URL
with separate services, set `RESUME_API_URL` before starting Streamlit. API
documentation is available at `http://127.0.0.1:8000/docs`, and `GET /health`
checks API availability.

The `POST /analyze` endpoint accepts multipart fields named `resume` and
`job_description`. Resume files are limited to 10 MB.