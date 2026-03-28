"""API routes for resume screening endpoints."""

import io
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from PyPDF2 import PdfReader
from src.schemas.models import (
    ResumeRequest, 
    ResumeScoreResponse, 
    ErrorResponse,
    JobCreateRequest,
    JobCreateResponse
)
from src.agents.orchestrator import Orchestrator, OrchestratorException
from src.core.logging import get_logger
from src.services.job_store import get_job_store
from src.services.utils import extract_text_from_pdf


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["resume"])

# Global instances
orchestrator = Orchestrator()
job_store = get_job_store()


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_job(
    job_description_text: Optional[str] = Form(None, description="Job description as text"),
    job_description_file: Optional[UploadFile] = File(None, description="Job description as PDF file")
) -> JobCreateResponse:
    """
    Create a new job posting with a unique ID.
    
    Accepts either:
    - job_description_text: Plain text job description
    - job_description_file: PDF file containing job description
    
    Args:
        job_description_text: Job description as plain text (optional)
        job_description_file: Job description as PDF file (optional)
        
    Returns:
        JobCreateResponse with unique job_id and success message
        
    Raises:
        HTTPException: If neither text nor file provided, or if processing fails
    """
    logger.info("Received job creation request")
    
    try:
        job_description = None
        
        # Validate that at least one input is provided
        if not job_description_text and not job_description_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either job_description_text or job_description_file must be provided"
            )
        
        # Process text input
        if job_description_text:
            if not job_description_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="job_description_text cannot be empty"
                )
            job_description = job_description_text.strip()
            logger.info("Using text job description")
        
        # Process PDF input (takes precedence if both provided)
        if job_description_file:
            # Validate file type
            if not job_description_file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PDF files are supported for job_description_file"
                )
            
            # Read and extract text from PDF
            try:
                pdf_content = await job_description_file.read()
                job_description = extract_text_from_pdf(pdf_content)
                logger.info(f"Extracted job description from PDF: {job_description_file.filename}")
            except Exception as e:
                logger.error(f"Failed to extract text from job description PDF: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse PDF file: {str(e)}"
                )
        
        # Create job in store
        job_id = job_store.create_job(job_description)
        logger.info(f"Job created successfully with ID: {job_id}")
        
        return JobCreateResponse(
            job_id=job_id,
            message="Job created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the job"
        )


@router.post(
    "/score-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def score_resume(
    resume_file: UploadFile = File(..., description="Resume PDF file"),
    job_id: str = Form(..., description="Unique job ID from /jobs endpoint")
) -> ResumeScoreResponse:
    """
    Score a resume against a job description using job_id.
    
    This endpoint uses a Worker-Critic architecture to analyze resumes:
    - Worker generates scores and justifications
    - Critic validates the output
    - Orchestrator retries up to 3 times if needed
    
    Args:
        resume_file: PDF file containing the resume
        job_id: Unique identifier for the job (from POST /jobs)
        
    Returns:
        ResumeScoreResponse with scores and justifications
        
    Raises:
        HTTPException: If job_id not found, PDF parsing fails, or scoring fails
    """
    logger.info(f"Received resume scoring request for job_id: {job_id}")
    
    try:
        # Validate job_id and retrieve job description
        job_description = job_store.get_job(job_id)
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid job_id. Please create a job using /api/v1/jobs first."
            )
        
        # Validate file type
        if not resume_file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for resume_file"
            )
        
        # Extract text from resume PDF
        try:
            pdf_content = await resume_file.read()
            resume_text = extract_text_from_pdf(pdf_content)
            logger.info(f"Extracted resume text from {resume_file.filename}")
        except Exception as e:
            logger.error(f"Failed to extract text from resume PDF: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse resume PDF: {str(e)}"
            )
        
        # Orchestrate scoring
        response = await orchestrator.score_resume(
            resume_text=resume_text,
            job_description=job_description
        )
        
        logger.info("Resume scored successfully")
        return response
        
    except OrchestratorException as e:
        logger.error(f"Orchestration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score resume: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/score-resume-legacy",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    deprecated=True
)
async def score_resume_legacy(request: ResumeRequest) -> ResumeScoreResponse:
    """
    (DEPRECATED) Score a resume against a job description using text inputs.
    
    This endpoint is deprecated. Use POST /jobs to create a job, then POST /score-resume.
    
    This endpoint uses a Worker-Critic architecture to analyze resumes:
    - Worker generates scores and justifications
    - Critic validates the output
    - Orchestrator retries up to 3 times if needed
    
    Args:
        request: ResumeRequest containing resume_text and job_description
        
    Returns:
        ResumeScoreResponse with scores and justifications
        
    Raises:
        HTTPException: If scoring fails after retries
    """
    logger.info("Received legacy resume scoring request")
    
    try:
        # Validate input
        if not request.resume_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_text cannot be empty"
            )
        
        if not request.job_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_description cannot be empty"
            )
        
        # Orchestrate scoring
        response = await orchestrator.score_resume(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        
        logger.info("Resume scored successfully (legacy endpoint)")
        return response
        
    except OrchestratorException as e:
        logger.error(f"Orchestration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score resume: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/upload-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    deprecated=True
)
async def upload_resume(
    resume_pdf: UploadFile = File(..., description="Resume PDF file uploaded by candidate"),
    job_description: str = Form(..., description="Job description provided by company/recruiter")
) -> ResumeScoreResponse:
    """
    (DEPRECATED) Upload a resume PDF for scoring against a job description.
    
    This endpoint is deprecated. Use POST /jobs to create a job, then POST /score-resume.
    
    **Intended Usage:**
    - **Company/Recruiter** uses this endpoint
    - Company has the job description
    - Company receives candidate resumes (PDF)
    - This endpoint scores each resume against the JD
    
    **NOT** for candidate self-upload (candidates don't have access to JD)
    
    This endpoint:
    - Accepts PDF file upload for resume
    - Extracts text from PDF
    - Scores resume against job description using Worker-Critic architecture
    
    Args:
        resume_pdf: PDF file containing the resume
        job_description: Text description of the job requirements
        
    Returns:
        ResumeScoreResponse with scores and justifications
        
    Raises:
        HTTPException: If PDF extraction or scoring fails
    """
    logger.info(f"Received PDF upload (legacy): {resume_pdf.filename}")
    
    try:
        # Validate file type
        if not resume_pdf.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Extract text from PDF using utility function
        try:
            pdf_content = await resume_pdf.read()
            resume_text = extract_text_from_pdf(pdf_content)
            logger.info(f"Extracted resume text from {resume_pdf.filename}")
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
        
        # Validate job description
        if not job_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_description cannot be empty"
            )
        
        # Orchestrate scoring with extracted text
        response = await orchestrator.score_resume(
            resume_text=resume_text,
            job_description=job_description
        )
        
        logger.info("Resume PDF scored successfully (legacy endpoint)")
        return response
        
    except OrchestratorException as e:
        logger.error(f"Orchestration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score resume: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Resume Screener"}
