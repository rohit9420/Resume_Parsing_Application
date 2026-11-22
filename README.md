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

## Run with Docker

Build the image from the `ParsingApplication` directory:

```powershell
docker build -t resume-matcher:local .
```

The `.env` file is excluded from the image. If it is in the parent
`Resume_Parser_Application` directory, pass it to the container at runtime:

```powershell
docker run --rm -p 8501:8501 --env-file ..\.env resume-matcher:local
```

Open `http://localhost:8501`. The container exposes Streamlit on port 8501;
FastAPI stays on the container's loopback interface. Stop it with `Ctrl+C`.
Do not copy API keys or resume documents into the image.

## Automatically publish images to Amazon ECR

The GitHub Actions workflow at `.github/workflows/publish-ecr.yml` builds and
pushes the Docker image whenever code is pushed to `main`. It publishes both
the commit-SHA tag and the `latest` tag. The workflow only publishes an image;
it does not deploy or run the application.

### AWS setup (one time)

1. In Amazon ECR, create a **private** repository named `resume-matcher`.
   Choose a region and use that same region in the next steps.
2. In AWS IAM, add the GitHub Actions OIDC identity provider if your account
   does not already have one:
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
3. Create an IAM role for GitHub Actions. Configure its trust relationship to
   allow only this repository's `main` branch. Replace `<AWS_ACCOUNT_ID>` with
   your AWS account ID:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
             "token.actions.githubusercontent.com:sub": "repo:rohit9420/Resume_Parsing_Application:ref:refs/heads/main"
           }
         }
       }
     ]
   }
   ```

4. Attach an IAM permission policy to the role. Allow
   `ecr:GetAuthorizationToken` on `*`, and allow these actions only on the
   `resume-matcher` repository ARN:
   `ecr:BatchCheckLayerAvailability`, `ecr:CompleteLayerUpload`,
   `ecr:InitiateLayerUpload`, `ecr:PutImage`, and `ecr:UploadLayerPart`.
   Replace `<AWS_REGION>` and `<AWS_ACCOUNT_ID>` in this policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "ecr:GetAuthorizationToken",
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "ecr:BatchCheckLayerAvailability",
           "ecr:CompleteLayerUpload",
           "ecr:InitiateLayerUpload",
           "ecr:PutImage",
           "ecr:UploadLayerPart"
         ],
         "Resource": "arn:aws:ecr:<AWS_REGION>:<AWS_ACCOUNT_ID>:repository/resume-matcher"
       }
     ]
   }
   ```

### GitHub setup

In the GitHub repository, open **Settings → Secrets and variables → Actions**:

- Add the secret `AWS_ROLE_ARN` with the ARN of the IAM role you created.
- Add the variable `AWS_REGION` with the region where the ECR repository lives.
- Add the variable `ECR_REPOSITORY` with the value `resume-matcher`.

Commit and push the workflow to `main`. In the repository's **Actions** tab,
check the workflow run. After it succeeds, the ECR repository will contain
images tagged with the commit SHA and `latest`. The Groq API key is not needed
to build the image and must not be added to GitHub Actions for this workflow.