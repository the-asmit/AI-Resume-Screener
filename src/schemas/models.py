"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ResumeRequest(BaseModel):
    """Request model for resume scoring."""
    
    resume_text: str = Field(..., description="Full text of the resume")
    job_description: str = Field(..., description="Job description to match against")


class JobCreateRequest(BaseModel):
    """Request model for creating a job posting."""
    
    job_description_text: Optional[str] = Field(None, description="Job description as text")


class JobCreateResponse(BaseModel):
    """Response model for job creation."""
    
    job_id: str = Field(..., description="Unique identifier for the job")
    message: str = Field(..., description="Success message")


class ScoreJustification(BaseModel):
    """Justification details for each score component."""
    
    experience_reasoning: str
    skill_match_reasoning: str
    projects_reasoning: str
    overall_reasoning: str


class ResumeScoreResponse(BaseModel):
    """Response model containing resume scores and justification."""
    
    experience_score: float = Field(..., ge=0, le=100, description="Experience relevance score (0-100)")
    skill_match_score: float = Field(..., ge=0, le=100, description="Skills alignment score (0-100)")
    projects_score: float = Field(..., ge=0, le=100, description="Projects quality score (0-100)")
    overall_score: float = Field(..., ge=0, le=100, description="Weighted overall score (0-100)")
    justification: ScoreJustification


class CriticFeedback(BaseModel):
    """Feedback from the Critic agent."""
    
    approved: bool
    feedback: Optional[str] = None
    suggested_changes: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    detail: Optional[str] = None
