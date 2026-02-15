"""Orchestrator that coordinates Worker and Critic strands."""

from src.agents.worker import WorkerStrand
from src.agents.critic import CriticStrand
from src.core.config import get_settings
from src.core.logging import get_logger
from src.schemas.models import ResumeScoreResponse


logger = get_logger(__name__)


class OrchestratorException(Exception):
    """Custom exception for orchestration failures."""
    pass


class Orchestrator:
    """
    Orchestrator that coordinates Worker-Critic workflow with retry logic using Strands SDK.
    """
    
    def __init__(self):
        """Initialize the orchestrator with worker and critic strands."""
        self.worker_strand = WorkerStrand()
        self.critic_strand = CriticStrand()
        self.settings = get_settings()
        logger.info("Orchestrator initialized with Strands SDK")
    
    async def score_resume(
        self,
        resume_text: str,
        job_description: str
    ) -> ResumeScoreResponse:
        """
        Orchestrate the resume scoring process with Worker-Critic loop using Strands.
        
        Args:
            resume_text: The candidate's resume
            job_description: The job requirements
            
        Returns:
            ResumeScoreResponse with final approved scores
            
        Raises:
            OrchestratorException: If max retries exceeded or critical failure
        """
        logger.info("Starting resume scoring orchestration with Strands")
        
        max_retries = self.settings.max_retries
        critic_feedback = None
        
        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempt {attempt}/{max_retries}")
            
            try:
                # Execute WorkerStrand to generate scores
                worker_output = await self.worker_strand.run(
                    resume_text=resume_text,
                    job_description=job_description,
                    critic_feedback=critic_feedback
                )
                
                # Execute CriticStrand to validate output
                validation = await self.critic_strand.run(
                    worker_output=worker_output,
                    resume_text=resume_text,
                    job_description=job_description
                )
                
                if validation.approved:
                    logger.info(f"Orchestration completed successfully on attempt {attempt}")
                    return worker_output
                else:
                    # Prepare feedback for next iteration
                    critic_feedback = validation.feedback
                    logger.warning(f"Attempt {attempt} rejected: {critic_feedback}")
                    
                    if attempt == max_retries:
                        logger.error("Max retries exceeded, returning last output")
                        # Return last output even if not approved
                        return worker_output
                    
            except Exception as e:
                logger.error(f"Attempt {attempt} failed with error: {str(e)}")
                if attempt == max_retries:
                    raise OrchestratorException(
                        f"Failed to score resume after {max_retries} attempts: {str(e)}"
                    )
                # Continue to next attempt
                continue
        
        raise OrchestratorException(
            f"Failed to score resume after {max_retries} attempts"
        )
