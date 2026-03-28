# AI Resume Screener

AI-powered resume screening system using Worker-Critic architecture with FastAPI and Strands SDK.

## Features

- **Job-based workflow**: Create jobs with unique IDs, then score multiple resumes against them
- Worker-Critic agent architecture for accurate scoring
- Resume scoring across technical skills, experience, education, and cultural fit
- PDF support for both resumes and job descriptions
- RESTful API with FastAPI
- Automatic retry logic
- In-memory job store for production-ready workflows

## Project Structure

```
ai-resume-screener/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── critic.py          # Critic agent implementation
│   │   ├── orchestrator.py    # Orchestrates Worker-Critic workflow
│   │   └── worker.py          # Worker agent implementation
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoint definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── llm.py             # LLM initialization and management
│   │   └── logging.py         # Logging setup
│   ├── services/
│   │   ├── __init__.py
│   │   ├── job_store.py       # In-memory job storage
│   │   └── utils.py           # PDF extraction utilities
│   └── schemas/
│       ├── __init__.py
│       └── models.py          # Pydantic models for request/response
├── myenv/                      # Virtual environment
├── requirements.txt
├── .env                        # Environment variables
├── API_TESTING_GUIDE.md       # Comprehensive API testing guide
└── README.md
```

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/the-asmit/ai-resume-screener.git
   cd ai-resume-screener
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   source myenv/bin/activate  # macOS/Linux
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   LOG_LEVEL=INFO
   MAX_RETRIES=3
   ```

## Running the Application

```bash
python src/main.py
```

Access at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

## API Endpoints

### POST `/api/v1/jobs`

Create a new job posting and receive a unique job ID.

**Request (multipart/form-data):**
- `job_description_text` (optional): Job description as plain text
- `job_description_file` (optional): Job description as PDF file

*At least one must be provided*

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
  "message": "Job created successfully"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "job_description_text=Senior Python Developer with FastAPI experience"
```

### POST `/api/v1/score-resume`

Score a resume against a job using its job_id.

**Request (multipart/form-data):**
- `resume_file` (required): Resume PDF file
- `job_id` (required): Job ID from `/jobs` endpoint

**Response:**
```json
{
  "experience_score": 85.0,
  "skill_match_score": 90.0,
  "projects_score": 80.0,
  "overall_score": 85.0,
  "justification": {
    "experience_reasoning": "...",
    "skill_match_reasoning": "...",
    "projects_reasoning": "...",
    "overall_reasoning": "..."
  }
}
```

**Example:**
```bash
# First, create a job
JOB_ID=$(curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "job_description_text=Senior Python Developer" \
  | jq -r '.job_id')

# Then score a resume
curl -X POST "http://localhost:8000/api/v1/score-resume" \
  -F "resume_file=@resume.pdf" \
  -F "job_id=$JOB_ID"
```

### Legacy Endpoints (Deprecated)

#### POST `/api/v1/score-resume-legacy`

#### POST `/api/v1/score-resume-legacy`

Score resume with inline text (original endpoint).

**Request:**
```json
{
  "resume_text": "Your resume text...",
  "job_description": "Job requirements..."
}
```

**Response:**
```json
{
  "experience_score": 85,
  "skill_match_score": 90,
  "projects_score": 80,
  "overall_score": 85.0,
  "justification": { ... }
}
```

#### POST `/api/v1/upload-resume`

Upload PDF resume with inline job description (original endpoint).

## Workflow Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Step 1: Create a job posting
job_response = requests.post(
    f"{BASE_URL}/jobs",
    data={"job_description_text": "Senior Python Developer with 5+ years experience"}
)
job_id = job_response.json()["job_id"]

# Step 2: Score multiple resumes against the same job
for resume_file in ["candidate1.pdf", "candidate2.pdf", "candidate3.pdf"]:
    with open(resume_file, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/score-resume",
            files={"resume_file": f},
            data={"job_id": job_id}
        )
        score = response.json()["overall_score"]
        print(f"{resume_file}: {score}/100")
```

## Usage Example

### Quick Start

```bash
# Create a job
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "job_description_text=Python Developer with FastAPI experience" \
  > job_response.json

# Extract job_id
JOB_ID=$(cat job_response.json | jq -r '.job_id')

# Score a resume
curl -X POST "http://localhost:8000/api/v1/score-resume" \
  -F "resume_file=@resume.pdf" \
  -F "job_id=$JOB_ID"
```

### Python Client Example

```python
import requests

# Create job with PDF
with open("job_description.pdf", "rb") as f:
    job_response = requests.post(
        "http://localhost:8000/api/v1/jobs",
        files={"job_description_file": f}
    )
job_id = job_response.json()["job_id"]

# Score resume
with open("resume.pdf", "rb") as f:
    score = requests.post(
        "http://localhost:8000/api/v1/score-resume",
        files={"resume_file": f},
        data={"job_id": job_id}
    )
print(score.json())
```

## What's New in v2.0

-- **Job-Based Workflow**: Create jobs once, score multiple resumes
-- **PDF Job Descriptions**: Upload job descriptions as PDF files
-- **Reusable Utilities**: Centralized PDF extraction logic
-- **Better Error Handling**: Detailed validation and error messages
-- **Production Ready**: In-memory job store with proper validation

## License

MIT
