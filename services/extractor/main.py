#!/usr/bin/env python3
"""
FastAPI Extractor Service

Microservice für MBZ-Datei-Extraktion und Metadaten-Verarbeitung.
Bietet asynchrone Job-Verarbeitung mit Status-Tracking und erweiterte Medienintegration.
"""

import sys
import uuid
import tempfile
import asyncio
import time
import subprocess
import shlex
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import structlog

# Import our extraction pipeline
from shared.utils.mbz_extractor import MBZExtractor
from shared.utils.xml_parser import parse_moodle_backup_complete, XMLParser
from shared.utils.metadata_mapper import create_complete_extracted_data
from shared.utils.file_utils import validate_mbz_file
from shared.models.dublin_core import FileMetadata, MediaCollection, MediaType

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Pydantic Models
class ExtractionJobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    message: str = Field(..., description="Status message")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Job creation timestamp")

class ExtractionResult(BaseModel):
    """Response model for completed extraction"""
    job_id: str
    status: str
    file_name: str
    file_size: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    job_id: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float
    service: str = "extractor"

class MediaFileResponse(BaseModel):
    """Response model for media file information"""
    file_id: str
    original_filename: str
    filepath: str
    mimetype: str
    filesize: int
    media_type: str
    file_extension: str
    is_image: bool
    is_video: bool
    is_document: bool
    is_audio: bool
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    timecreated: Optional[datetime] = None
    timemodified: Optional[datetime] = None

class MediaCollectionResponse(BaseModel):
    """Response model for media collection"""
    collection_id: str
    name: str
    description: Optional[str] = None
    total_files: int
    total_size: int
    images_count: int
    videos_count: int
    documents_count: int
    audio_count: int
    other_count: int

class FileStatisticsResponse(BaseModel):
    """Response model for file statistics"""
    total_files: int
    total_size: int
    by_type: Dict[str, Dict[str, Any]]
    by_extension: Dict[str, Dict[str, Any]]
    largest_files: List[Dict[str, Any]]

# Global job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

# FastAPI App
app = FastAPI(
    title="OERSync-AI Extractor Service",
    description="Microservice für MBZ-Datei-Extraktion und Metadaten-Verarbeitung mit erweiterter Medienintegration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service start time for uptime calculation
service_start_time = time.time()

def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    return jobs.get(job_id)

def update_job_status(job_id: str, status: str, message: str, **kwargs):
    """Update job status"""
    if job_id in jobs:
        jobs[job_id].update({
            "status": status,
            "message": message,
            **kwargs
        })
        logger.info("Job status updated", job_id=job_id, status=status, message=message)

async def process_mbz_extraction(job_id: str, file_path: Path, original_filename: str):
    """Background task for MBZ extraction and processing with enhanced media integration"""
    logger.info("Starting MBZ extraction", job_id=job_id, filename=original_filename)
    
    start_time = time.time()
    extractor = None
    
    try:
        # Update to processing
        update_job_status(job_id, "processing", "Extracting MBZ file...")
        
        # Create temporary directory for extraction
        temp_dir = Path(tempfile.mkdtemp(prefix=f"mbz_extract_{job_id}_"))
        extractor = MBZExtractor(temp_dir)
        
        # Step 1: Extract MBZ file
        extraction_result = extractor.extract_mbz(file_path)
        logger.info("MBZ extraction completed", job_id=job_id, 
                   archive_type=extraction_result.archive_type)
        
        update_job_status(job_id, "processing", "Parsing XML structures and media files...")
        
        # Step 2: Parse XML structures with enhanced media integration
        try:
            extracted_data = parse_moodle_backup_complete(
                backup_xml_path=extraction_result.moodle_backup_xml,
                course_xml_path=extraction_result.course_xml,
                sections_path=temp_dir / "extracted" / "sections" if (temp_dir / "extracted" / "sections").exists() else None,
                activities_path=temp_dir / "extracted" / "activities" if (temp_dir / "extracted" / "activities").exists() else None,
                files_xml_path=extraction_result.files_xml  # NEUE FUNKTIONALITÄT
            )
            logger.info("XML parsing completed with media integration", job_id=job_id, 
                       course_name=extracted_data.course_name,
                       files_count=len(extracted_data.files))
        except Exception as e:
            logger.warning("XML parsing failed, using minimal data", job_id=job_id, error=str(e))
            # Fallback: Aktivitäten trotzdem extrahieren
            parser = XMLParser()
            backup_info = parser.parse_moodle_backup_xml(extraction_result.moodle_backup_xml)
            activities = []
            activities_dir = temp_dir / "extracted" / "activities"
            if activities_dir.exists() and activities_dir.is_dir():
                for activity_dir in activities_dir.iterdir():
                    if activity_dir.is_dir():
                        # Parse activity type from folder name (e.g., "page_34" -> "page")
                        activity_type = activity_dir.name.split('_')[0]
                        activity_xml = activity_dir / f"{activity_type}.xml"
                        if activity_xml.exists():
                            try:
                                activity_metadata = parser.parse_activity_xml(activity_xml)
                                activities.append(activity_metadata)
                            except Exception as e2:
                                logger.warning("Fehler beim Parsen einer Activity im Fallback", file=str(activity_xml), error=str(e2))
            
            # Fallback: Versuche files.xml zu parsen
            files_data = []
            media_collections = []
            file_statistics = {}
            if extraction_result.files_xml and extraction_result.files_xml.exists():
                try:
                    files_info = parser.parse_files_xml(extraction_result.files_xml)
                    files_data = parser.convert_files_to_metadata(files_info)
                    file_statistics = parser.create_file_statistics(files_data)
                    logger.info("Files.xml parsed in fallback mode", files_count=len(files_data))
                except Exception as e3:
                    logger.warning("Files.xml parsing failed in fallback", error=str(e3))
            
            extracted_data = create_complete_extracted_data(backup_info, activities=activities)
            # Füge Medienintegration zum Fallback hinzu
            extracted_data.files = files_data
            extracted_data.file_statistics = file_statistics
        
        update_job_status(job_id, "processing", "Creating metadata mappings and media collections...")
        
        # Step 3: Serialize for JSON response with enhanced media data
        extracted_data_dict = {
            "course_id": extracted_data.course_id,
            "course_name": extracted_data.course_name,
            "course_short_name": extracted_data.course_short_name,
            "course_summary": extracted_data.course_summary,
            "course_language": extracted_data.course_language,
            "course_format": extracted_data.course_format,
            "course_start_date": extracted_data.course_start_date.isoformat() if extracted_data.course_start_date else None,
            "course_end_date": extracted_data.course_end_date.isoformat() if extracted_data.course_end_date else None,
            "course_visible": extracted_data.course_visible,
            "backup_date": extracted_data.backup_date.isoformat() if extracted_data.backup_date else None,
            "moodle_version": extracted_data.moodle_version,
            "backup_version": extracted_data.backup_version,
            "sections_count": len(extracted_data.sections),
            "activities_count": len(extracted_data.activities),
            
            # Dublin Core metadata
            "dublin_core": {
                "title": extracted_data.dublin_core.title,
                "creator": extracted_data.dublin_core.creator,
                "subject": extracted_data.dublin_core.subject,
                "description": extracted_data.dublin_core.description,
                "publisher": extracted_data.dublin_core.publisher,
                "contributor": extracted_data.dublin_core.contributor,
                "date": extracted_data.dublin_core.date.isoformat() if extracted_data.dublin_core.date else None,
                "type": extracted_data.dublin_core.type if extracted_data.dublin_core.type else None,
                "format": extracted_data.dublin_core.format,
                "identifier": extracted_data.dublin_core.identifier,
                "source": extracted_data.dublin_core.source,
                "language": extracted_data.dublin_core.language if extracted_data.dublin_core.language else None,
                "relation": extracted_data.dublin_core.relation,
                "coverage": extracted_data.dublin_core.coverage,
                "rights": extracted_data.dublin_core.rights if extracted_data.dublin_core.rights else None
            },
            
            # Educational metadata
            "educational": {
                "learning_resource_type": extracted_data.educational.learning_resource_type if extracted_data.educational.learning_resource_type else None,
                "intended_end_user_role": extracted_data.educational.intended_end_user_role,
                "context": extracted_data.educational.context if extracted_data.educational.context else None,
                "typical_age_range": extracted_data.educational.typical_age_range,
                "difficulty": extracted_data.educational.difficulty,
                "typical_learning_time": extracted_data.educational.typical_learning_time,
                "learning_objectives": extracted_data.educational.learning_objectives,
                "learning_outcomes": extracted_data.educational.learning_outcomes,
                "prerequisites": extracted_data.educational.prerequisites,
                "competencies": extracted_data.educational.competencies,
                "skills": extracted_data.educational.skills,
                "assessment_type": extracted_data.educational.assessment_type,
                "interactivity_type": extracted_data.educational.interactivity_type
            },
            
            # Sections und Activities
            "sections": extracted_data.sections,
            "activities": extracted_data.activities,
            
            # ERWEITERTE MEDIENINTEGRATION
            "files": [
                {
                    "file_id": f.file_id,
                    "original_filename": f.original_filename,
                    "filepath": f.filepath,
                    "mimetype": f.mimetype,
                    "filesize": f.filesize,
                    "media_type": f.media_type.value if hasattr(f.media_type, 'value') else str(f.media_type),
                    "file_extension": f.file_extension,
                    "title": f.title,
                    "description": f.description,
                    "author": f.author,
                    "license": f.license.value if f.license else None,
                    "is_image": f.is_image,
                    "is_video": f.is_video,
                    "is_document": f.is_document,
                    "is_audio": f.is_audio,
                    "timecreated": f.timecreated.isoformat() if f.timecreated else None,
                    "timemodified": f.timemodified.isoformat() if f.timemodified else None,
                    "used_in_activities": f.used_in_activities,
                    "used_in_sections": f.used_in_sections
                }
                for f in extracted_data.files
            ],
            
            "media_collections": [
                {
                    "collection_id": mc.collection_id,
                    "name": mc.name,
                    "description": mc.description,
                    "total_files": mc.total_files,
                    "total_size": mc.total_size,
                    "images_count": len(mc.images),
                    "videos_count": len(mc.videos),
                    "documents_count": len(mc.documents),
                    "audio_count": len(mc.audio_files),
                    "other_count": len(mc.other_files),
                    "course_id": mc.course_id,
                    "section_id": mc.section_id,
                    "activity_id": mc.activity_id
                }
                for mc in extracted_data.media_collections
            ],
            
            "file_statistics": extracted_data.file_statistics
        }
        
        processing_time = time.time() - start_time
        
        # Update job with successful completion
        update_job_status(
            job_id, 
            "completed", 
            f"Extraction and metadata mapping completed successfully. Found {len(extracted_data.files)} media files.",
            completed_at=datetime.now(),
            processing_time_seconds=processing_time,
            extracted_data=extracted_data_dict
        )
        
        logger.info("MBZ processing completed successfully with media integration", 
                   job_id=job_id, processing_time=processing_time, files_count=len(extracted_data.files))
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Extraction failed: {str(e)}"
        
        update_job_status(
            job_id, 
            "failed", 
            error_message,
            completed_at=datetime.now(),
            processing_time_seconds=processing_time,
            error_message=error_message
        )
        
        logger.error("MBZ processing failed", job_id=job_id, error=str(e), processing_time=processing_time)
    
    finally:
        # Cleanup
        try:
            if file_path.exists():
                file_path.unlink()
            if extractor:
                extractor.cleanup()
        except Exception as e:
            logger.warning("Cleanup error", job_id=job_id, error=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_start_time
    return HealthResponse(uptime_seconds=uptime)

@app.post("/extract", response_model=ExtractionJobResponse)
async def extract_mbz(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and extract MBZ file with enhanced media integration
    
    Creates a background job for processing the MBZ file.
    Returns job ID for status tracking.
    """
    
    # Validate file
    if not file.filename or not file.filename.endswith('.mbz'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .mbz files are allowed."
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file temporarily
        temp_file = Path(tempfile.mktemp(suffix=".mbz"))
        
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = len(content)
        
        # Validate MBZ file
        is_valid, error_msg = validate_mbz_file(temp_file)
        if not is_valid:
            temp_file.unlink()  # Cleanup
            raise HTTPException(status_code=400, detail=f"Invalid MBZ file: {error_msg}")
        
        # Create job record
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "message": "Job created, waiting for processing",
            "file_name": file.filename,
            "file_size": file_size,
            "created_at": datetime.now(),
            "completed_at": None,
            "processing_time_seconds": None,
            "extracted_data": None,
            "error_message": None
        }
        
        jobs[job_id] = job_data
        
        # Start background processing
        background_tasks.add_task(
            process_mbz_extraction, 
            job_id, 
            temp_file, 
            file.filename
        )
        
        logger.info("Extraction job created", job_id=job_id, filename=file.filename, size=file_size)
        
        return ExtractionJobResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        if 'temp_file' in locals() and temp_file.exists():
            temp_file.unlink()
        
        logger.error("Failed to create extraction job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create extraction job: {str(e)}")

@app.get("/extract/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate progress based on status
    progress = {
        "pending": 0,
        "processing": 50,
        "completed": 100,
        "failed": 100
    }.get(job["status"], 0)
    
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        created_at=job["created_at"],
        progress=progress
    )

@app.get("/extract/{job_id}", response_model=ExtractionResult)
async def get_job_result(job_id: str):
    """Get job result with enhanced media data"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] == "pending" or job["status"] == "processing":
        # Return 202 Accepted for pending/processing jobs
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": job["status"],
                "message": job["message"],
                "created_at": job["created_at"].isoformat()
            }
        )
    
    return ExtractionResult(**job)

@app.get("/jobs", response_model=List[ExtractionJobResponse])
async def list_jobs():
    """List all jobs"""
    job_list = []
    for job_data in jobs.values():
        job_list.append(ExtractionJobResponse(**job_data))
    
    # Sort by creation time (newest first)
    job_list.sort(key=lambda x: x.created_at, reverse=True)
    
    return job_list

@app.delete("/extract/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Don't allow deletion of processing jobs
    if job["status"] == "processing":
        raise HTTPException(status_code=400, detail="Cannot delete job that is currently processing")
    
    del jobs[job_id]
    logger.info("Job deleted", job_id=job_id)
    
    return {"message": "Job deleted successfully", "job_id": job_id}

# NEUE MEDIENENDPUNKTE

@app.get("/extract/{job_id}/media", response_model=List[MediaFileResponse])
async def get_job_media_files(job_id: str):
    """Get all media files for a completed job"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "files" not in extracted_data:
        return []
    
    return [
        MediaFileResponse(
            file_id=f["file_id"],
            original_filename=f["original_filename"],
            filepath=f["filepath"],
            mimetype=f["mimetype"],
            filesize=f["filesize"],
            media_type=f["media_type"],
            file_extension=f["file_extension"],
            is_image=f["is_image"],
            is_video=f["is_video"],
            is_document=f["is_document"],
            is_audio=f["is_audio"],
            title=f.get("title"),
            description=f.get("description"),
            author=f.get("author"),
            timecreated=datetime.fromisoformat(f["timecreated"]) if f.get("timecreated") else None,
            timemodified=datetime.fromisoformat(f["timemodified"]) if f.get("timemodified") else None
        )
        for f in extracted_data["files"]
    ]

@app.get("/extract/{job_id}/media/{file_id}", response_model=MediaFileResponse)
async def get_job_media_file(job_id: str, file_id: str):
    """Get specific media file information"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "files" not in extracted_data:
        raise HTTPException(status_code=404, detail="No media files found")
    
    # Find the specific file
    for f in extracted_data["files"]:
        if f["file_id"] == file_id:
            return MediaFileResponse(
                file_id=f["file_id"],
                original_filename=f["original_filename"],
                filepath=f["filepath"],
                mimetype=f["mimetype"],
                filesize=f["filesize"],
                media_type=f["media_type"],
                file_extension=f["file_extension"],
                is_image=f["is_image"],
                is_video=f["is_video"],
                is_document=f["is_document"],
                is_audio=f["is_audio"],
                title=f.get("title"),
                description=f.get("description"),
                author=f.get("author"),
                timecreated=datetime.fromisoformat(f["timecreated"]) if f.get("timecreated") else None,
                timemodified=datetime.fromisoformat(f["timemodified"]) if f.get("timemodified") else None
            )
    
    raise HTTPException(status_code=404, detail="Media file not found")

@app.get("/extract/{job_id}/media/{file_id}/download")
async def download_media_file(job_id: str, file_id: str):
    """
    Download a specific media file from the extracted MBZ
    
    This endpoint provides direct access to the extracted media files.
    Note: Files are only available as long as the extraction job exists.
    """
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "files" not in extracted_data:
        raise HTTPException(status_code=404, detail="No media files found")
    
    # Find the specific file
    target_file = None
    for f in extracted_data["files"]:
        if f["file_id"] == file_id:
            target_file = f
            break
    
    if not target_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    # Construct the file path in the extracted directory
    # Note: This assumes the extraction directory still exists
    # In a production environment, you might want to store file paths
    try:
        # Try to find the file in the extracted directory
        # This is a simplified approach - in production, you'd want to store file paths
        extracted_dir = Path(f"/tmp/mbz_extract_{job_id}_*")
        possible_dirs = list(extracted_dir.parent.glob(f"mbz_extract_{job_id}_*"))
        
        if not possible_dirs:
            raise HTTPException(status_code=404, detail="Extraction directory not found")
        
        extracted_path = possible_dirs[0]
        files_dir = extracted_path / "extracted" / "files"
        
        # Look for the file by contenthash
        file_path = files_dir / file_id[:2] / file_id[2:4] / file_id
        
        if not file_path.exists():
            # Try alternative path structure
            file_path = files_dir / file_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Return the file
        return FileResponse(
            path=file_path,
            filename=target_file["original_filename"],
            media_type=target_file["mimetype"]
        )
        
    except Exception as e:
        logger.error(f"Error serving file {file_id} for job {job_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Error serving file")

@app.get("/extract/{job_id}/media/type/{media_type}", response_model=List[MediaFileResponse])
async def get_job_media_by_type(job_id: str, media_type: str):
    """Get media files filtered by type"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "files" not in extracted_data:
        return []
    
    # Validate media type
    valid_types = [t.value for t in MediaType]
    if media_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid media type. Valid types: {valid_types}")
    
    # Filter files by type
    filtered_files = [
        f for f in extracted_data["files"]
        if f["media_type"] == media_type
    ]
    
    return [
        MediaFileResponse(
            file_id=f["file_id"],
            original_filename=f["original_filename"],
            filepath=f["filepath"],
            mimetype=f["mimetype"],
            filesize=f["filesize"],
            media_type=f["media_type"],
            file_extension=f["file_extension"],
            is_image=f["is_image"],
            is_video=f["is_video"],
            is_document=f["is_document"],
            is_audio=f["is_audio"],
            title=f.get("title"),
            description=f.get("description"),
            author=f.get("author"),
            timecreated=datetime.fromisoformat(f["timecreated"]) if f.get("timecreated") else None,
            timemodified=datetime.fromisoformat(f["timemodified"]) if f.get("timemodified") else None
        )
        for f in filtered_files
    ]

@app.get("/extract/{job_id}/media/collections", response_model=List[MediaCollectionResponse])
async def get_job_media_collections(job_id: str):
    """Get media collections for a completed job"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "media_collections" not in extracted_data:
        return []
    
    return [
        MediaCollectionResponse(
            collection_id=mc["collection_id"],
            name=mc["name"],
            description=mc.get("description"),
            total_files=mc["total_files"],
            total_size=mc["total_size"],
            images_count=mc["images_count"],
            videos_count=mc["videos_count"],
            documents_count=mc["documents_count"],
            audio_count=mc["audio_count"],
            other_count=mc["other_count"]
        )
        for mc in extracted_data["media_collections"]
    ]

@app.get("/extract/{job_id}/media/statistics", response_model=FileStatisticsResponse)
async def get_job_media_statistics(job_id: str):
    """Get media file statistics for a completed job"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    extracted_data = job["extracted_data"]
    if not extracted_data or "file_statistics" not in extracted_data:
        return FileStatisticsResponse(
            total_files=0,
            total_size=0,
            by_type={},
            by_extension={},
            largest_files=[]
        )
    
    stats = extracted_data["file_statistics"]
    return FileStatisticsResponse(**stats)

@app.post("/start-moodle-instance/{job_id}")
async def start_moodle_instance(job_id: str):
    """
    Starte eine Gitpod Moodle-Instanz basierend auf den extrahierten Metadaten
    """
    try:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job nicht gefunden")
        
        job_data = jobs[job_id]
        if job_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="Extraktion noch nicht abgeschlossen")
        
        extracted_data = job_data["extracted_data"]
        moodle_version = extracted_data.get("moodle_version", "4.1")
        
        # Bestimme Branch basierend auf Moodle Version
        if moodle_version.startswith("4."):
            branch = "MOODLE_401_STABLE"  # Aktueller 4.x Branch
        elif moodle_version.startswith("3."):
            branch = "MOODLE_311_STABLE"  # Legacy 3.x Branch
        else:
            branch = "main"  # Fallback auf main
            
        # Einfache Gitpod-URL für Moodle-Docker
        context_url = "https://gitpod.io/#https://github.com/moodlehq/moodle-docker"
        
        # Prüfe ob Gitpod-Environment-Variablen gesetzt sind
        gitpod_token = os.getenv('GITPOD_TOKEN')
        gitpod_org_id = os.getenv('GITPOD_ORG_ID') 
        gitpod_owner_id = os.getenv('GITPOD_OWNER_ID')
        
        if not all([gitpod_token, gitpod_org_id, gitpod_owner_id]):
            return {
                "context_url": context_url,
                "manual_start": True,
                "message": "Gitpod-Credentials nicht konfiguriert. Bitte manuell starten.",
                "instructions": f"Öffne diese URL: {context_url}"
            }
        
        # Starte Gitpod-Instanz automatisch
        try:
            cmd = [
                "python", "start_gitpod.py", 
                context_url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=".."  # Gehe zum Projekt-Root
            )
            
            if result.returncode == 0:
                # Parse Workspace-URL aus Output
                output_lines = result.stdout.strip().split('\n')
                workspace_url = None
                workspace_id = None
                
                for line in output_lines:
                    if "URL:" in line:
                        workspace_url = line.split("URL:")[1].strip()
                    elif "ID:" in line:
                        workspace_id = line.split("ID:")[1].strip()
                
                return {
                    "success": True,
                    "workspace_url": workspace_url,
                    "workspace_id": workspace_id,
                    "context_url": context_url,
                    "moodle_version": moodle_version,
                    "branch": branch,
                    "message": "Moodle-Instanz erfolgreich gestartet!"
                }
            else:
                logger.error(f"Gitpod-Start fehlgeschlagen: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "context_url": context_url,
                    "manual_start": True,
                    "message": "Automatischer Start fehlgeschlagen. Bitte manuell öffnen."
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout beim Starten der Gitpod-Instanz",
                "context_url": context_url,
                "manual_start": True
            }
        except Exception as e:
            logger.error(f"Fehler beim Gitpod-Start: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "context_url": context_url,
                "manual_start": True
            }
            
    except Exception as e:
        logger.error(f"Fehler in start_moodle_instance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interner Serverfehler: {str(e)}")

@app.post("/extract-activities")
async def extract_activities(file: UploadFile = File(...)):
    """
    Extrahiere Aktivitäten aus einer hochgeladenen MBZ-Datei und gebe sie als JSON zurück.
    """
    import shutil
    activities = []
    temp_file = None
    extraction_result = None
    try:
        if not file.filename or not file.filename.endswith('.mbz'):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .mbz files are allowed.")
        # Speichere Datei temporär
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".mbz", delete=False)
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        mbz_path = Path(temp_file.name)
        # Extrahiere MBZ
        extraction_result = extract_mbz_file(mbz_path)
        # Parse Aktivitäten
        try:
            extracted_data = parse_moodle_backup_complete(
                backup_xml_path=extraction_result.moodle_backup_xml,
                course_xml_path=extraction_result.course_xml,
                sections_path=Path(extraction_result.temp_dir, "extracted", "sections"),
                activities_path=Path(extraction_result.temp_dir, "extracted", "activities"),
                files_xml_path=extraction_result.files_xml  # NEUE FUNKTIONALITÄT
            )
        except Exception as e:
            # Fallback: Aktivitäten trotzdem extrahieren
            parser = XMLParser()
            backup_info = parser.parse_moodle_backup_xml(extraction_result.moodle_backup_xml)
            activities = []
            activities_dir = Path(extraction_result.temp_dir, "extracted", "activities")
            if activities_dir.exists() and activities_dir.is_dir():
                for activity_dir in activities_dir.iterdir():
                    if activity_dir.is_dir():
                        # Parse activity type from folder name (e.g., "page_34" -> "page")
                        activity_type = activity_dir.name.split('_')[0]
                        activity_xml = activity_dir / f"{activity_type}.xml"
                        if activity_xml.exists():
                            try:
                                activity_metadata = parser.parse_activity_xml(activity_xml)
                                activities.append(activity_metadata)
                            except Exception as e2:
                                pass
            extracted_data = create_complete_extracted_data(backup_info, activities=activities)
        activities = [a.__dict__ for a in extracted_data.activities]
        return {"activities": activities}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Extraktion: {str(e)}")
    finally:
        # Cleanup
        try:
            if temp_file is not None:
                os.unlink(temp_file.name)
            if extraction_result is not None:
                extraction_result.temp_dir and shutil.rmtree(extraction_result.temp_dir, ignore_errors=True)
        except Exception:
            pass

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    logger.info("Starting OERSync-AI Extractor Service with enhanced media integration")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 