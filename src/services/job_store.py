"""In-memory job description store for managing job postings."""

import uuid
from typing import Dict, Optional
from src.core.logging import get_logger


logger = get_logger(__name__)


class JobStore:
    """
    In-memory store for job descriptions.
    
    Stores job descriptions with unique identifiers and provides
    methods for creating and retrieving jobs.
    """
    
    def __init__(self):
        """Initialize the job store with an empty dictionary."""
        self._store: Dict[str, str] = {}
        logger.info("JobStore initialized")
    
    def create_job(self, job_description: str) -> str:
        """
        Create a new job entry and return its unique ID.
        
        Args:
            job_description: The text content of the job description
            
        Returns:
            job_id: A unique identifier for the job
        """
        job_id = str(uuid.uuid4())
        self._store[job_id] = job_description
        logger.info(f"Created job with ID: {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[str]:
        """
        Retrieve a job description by its ID.
        
        Args:
            job_id: The unique identifier of the job
            
        Returns:
            The job description text, or None if not found
        """
        job_description = self._store.get(job_id)
        if job_description:
            logger.debug(f"Retrieved job with ID: {job_id}")
        else:
            logger.warning(f"Job not found with ID: {job_id}")
        return job_description
    
    def job_exists(self, job_id: str) -> bool:
        """
        Check if a job exists in the store.
        
        Args:
            job_id: The unique identifier of the job
            
        Returns:
            True if job exists, False otherwise
        """
        return job_id in self._store
    
    def count(self) -> int:
        """
        Get the total number of jobs in the store.
        
        Returns:
            The count of stored jobs
        """
        return len(self._store)


# Global singleton instance
_job_store: Optional[JobStore] = None


def get_job_store() -> JobStore:
    """
    Get or create the global JobStore instance.
    
    Returns:
        The singleton JobStore instance
    """
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store
