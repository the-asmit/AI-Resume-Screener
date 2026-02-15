# AI Resume Screener

AI-powered resume screening system using Worker-Critic architecture with FastAPI and Strands SDK.

## Features

- Worker-Critic agent architecture
- Resume scoring across technical skills, experience, education, and cultural fit
- PDF and text input support
- RESTful API with FastAPI
- Automatic retry logic

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
│   └── schemas/
│       ├── __init__.py
│       └── models.py          # Pydantic models for request/response
├── myenv/                      # Virtual environment
├── requirements.txt
├── .env                        # Environment variables
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

### POST `/api/v1/score-resume`

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
  "technical_skills_score": 85,
  "experience_score": 90,
  "education_score": 80,
  "cultural_fit_score": 75,
  "overall_score": 82.5
}
```

### POST `/api/v1/upload-resume`

Upload PDF resume with job description (multipart/form-data).

## Usage Example

```bash
curl -X POST "http://localhost:8000/api/v1/score-resume" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Your resume...",
    "job_description": "Job description..."
  }'
```

## License

MIT
