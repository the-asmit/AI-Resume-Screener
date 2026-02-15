"""Critic strand that validates Worker output."""

from typing import Dict, Any
from src.core.llm import generate_json
from src.core.logging import get_logger
from src.schemas.models import ResumeScoreResponse, CriticFeedback


logger = get_logger(__name__)


class CriticStrand:
    """Critic strand that validates Worker's resume scores."""
    
    def __init__(self):
        """Initialize the Critic strand."""
        logger.info("CriticStrand initialized")
    
    async def run(
        self,
        worker_output: ResumeScoreResponse,
        resume_text: str,
        job_description: str
    ) -> CriticFeedback:
        """
        Execute the Critic strand to validate Worker's output.
        
        Args:
            worker_output: The scores and justifications from Worker
            resume_text: The original resume
            job_description: The original job description
            
        Returns:
            CriticFeedback indicating approval or requesting changes
        """
        logger.info("CriticStrand validating worker output")
        
        prompt = f"""You are a critical evaluator of resume scoring systems. Your job is to validate scores for accuracy, consistency, and proper justification.

IMPORTANT: Return ONLY valid JSON. Do not include markdown code blocks, explanations, or any text outside the JSON object.

Required JSON structure:
{{
    "approved": true or false,
    "feedback": "<explanation if not approved, null if approved>",
    "suggested_changes": {{<specific changes needed, null if approved>}}
}}

Validation criteria:
1. Scores are reasonable (0-100 range)
2. Justifications are specific and evidence-based
3. Overall score aligns with component scores
4. No obvious mismatches between scores and content

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

WORKER'S SCORES:
Experience Score: {worker_output.experience_score}
Skill Match Score: {worker_output.skill_match_score}
Projects Score: {worker_output.projects_score}
Overall Score: {worker_output.overall_score}

JUSTIFICATIONS:
Experience: {worker_output.justification.experience_reasoning}
Skills: {worker_output.justification.skill_match_reasoning}
Projects: {worker_output.justification.projects_reasoning}
Overall: {worker_output.justification.overall_reasoning}

Check for:
- Are scores justified by the resume content?
- Is the overall score reasonable given component scores?
- Are justifications specific and evidence-based?
- Any obvious errors or inconsistencies?

If valid, approve. If issues found, reject with specific feedback.

Remember: Return ONLY the JSON object, no markdown or additional text."""
        
        try:
            # Use generate_json to get response without response_schema
            feedback = generate_json(prompt, CriticFeedback)
            
            if feedback.approved:
                logger.info("CriticStrand approved worker output")
            else:
                logger.warning(f"CriticStrand rejected output: {feedback.feedback}")
            
            return feedback
            
        except Exception as e:
            logger.error(f"CriticStrand validation failed: {str(e)}")
            raise Exception(f"CriticStrand failed to validate output: {str(e)}")
