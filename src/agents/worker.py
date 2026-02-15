"""Worker strand that generates resume scores and justifications."""

from typing import Dict, Any
from src.core.llm import generate_json
from src.core.logging import get_logger
from src.schemas.models import ResumeScoreResponse


logger = get_logger(__name__)


class WorkerStrand:
    """Worker strand that analyzes resumes and generates scores."""
    
    def __init__(self):
        """Initialize the Worker strand."""
        logger.info("WorkerStrand initialized")
    
    async def run(
        self,
        resume_text: str,
        job_description: str,
        critic_feedback: str = None
    ) -> ResumeScoreResponse:
        """
        Execute the Worker strand to analyze a resume.
        
        Args:
            resume_text: The candidate's resume
            job_description: The job requirements
            critic_feedback: Optional feedback from critic for retry attempts
            
        Returns:
            ResumeScoreResponse with scores and justifications
        """
        logger.info("WorkerStrand executing resume analysis")
        
        prompt = f"""You are an expert resume evaluator. Analyze resumes against job descriptions and provide accurate scores.

IMPORTANT: Return ONLY valid JSON. Do not include markdown code blocks, explanations, or any text outside the JSON object.

Required JSON structure:
{{
    "experience_score": <number 0-100>,
    "skill_match_score": <number 0-100>,
    "projects_score": <number 0-100>,
    "overall_score": <number 0-100>,
    "justification": {{
        "experience_reasoning": "<detailed explanation>",
        "skill_match_reasoning": "<detailed explanation>",
        "projects_reasoning": "<detailed explanation>",
        "overall_reasoning": "<detailed explanation>"
    }}
}}

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Evaluate based on:
1. Experience Score (0-100): Relevance and depth of work experience
2. Skill Match Score (0-100): Alignment of technical/professional skills
3. Projects Score (0-100): Quality and relevance of projects/achievements
4. Overall Score (0-100): Weighted average considering all factors

Provide detailed justification for each score."""

        if critic_feedback:
            prompt += f"\n\nCRITIC FEEDBACK (address these concerns):\n{critic_feedback}"
        
        prompt += "\n\nRemember: Return ONLY the JSON object, no markdown or additional text."
        
        try:
            # Use generate_json to get response without response_schema
            response = generate_json(prompt, ResumeScoreResponse)
            
            logger.info(f"WorkerStrand generated scores - Overall: {response.overall_score:.1f}")
            return response
            
        except Exception as e:
            logger.error(f"WorkerStrand analysis failed: {str(e)}")
            raise Exception(f"WorkerStrand failed to analyze resume: {str(e)}")
