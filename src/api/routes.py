"""API routes for resume screening endpoints."""

import io
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from PyPDF2 import PdfReader
from src.schemas.models import ResumeRequest, ResumeScoreResponse, ErrorResponse
from src.agents.orchestrator import Orchestrator, OrchestratorException
from src.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["resume"])

# Global orchestrator instance
orchestrator = Orchestrator()


@router.post(
    "/score-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def score_resume(request: ResumeRequest) -> ResumeScoreResponse:
    """
    Score a resume against a job description.
    
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
    logger.info("Received resume scoring request")
    
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
    "/upload-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def upload_resume(
    resume_pdf: UploadFile = File(..., description="Resume PDF file uploaded by candidate"),
    job_description: str = Form(..., description="Job description provided by company/recruiter")
) -> ResumeScoreResponse:
    """
    Upload a resume PDF for scoring against a job description.
    
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
    logger.info(f"Received PDF upload: {resume_pdf.filename}")
    
    try:
        # Validate file type
        if not resume_pdf.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Read PDF content
        pdf_content = await resume_pdf.read()
        
        # Extract text from PDF
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            resume_text = ""
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text + "\n"
            
            if not resume_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not extract text from PDF. The file may be empty or corrupted."
                )
                
            logger.info(f"Extracted {len(resume_text)} characters from PDF")
            
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
        
        logger.info("Resume PDF scored successfully")
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
