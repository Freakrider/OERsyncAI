#!/usr/bin/env python3
"""
FastAPI ILIAS Analyzer Service

Microservice für ILIAS-Export-Analyse und Moodle-Konvertierung.
"""

import sys
import uuid
import tempfile
import time
import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

# Load environment variables
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

# Import ILIAS utilities
from shared.utils.ilias import IliasAnalyzer, MoodleConverter, Module

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
class AnalysisJobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    message: str = Field(..., description="Status message")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Job creation timestamp")

class AnalysisResult(BaseModel):
    """Response model for completed analysis"""
    job_id: str
    status: str
    file_name: str
    file_size: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    analysis_data: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Dict[str, Any]] = None  # For MBZ conversion results
    moodle_mbz_available: bool = False
    error_message: Optional[str] = None
    ilias_source: Optional[Dict[str, Any]] = None  # Original ILIAS info
    mbz_path: Optional[str] = None  # Path to converted MBZ file
    conversion_report: Optional[Dict[str, Any]] = None  # NEW: Conversion compatibility report
    moodle_structure: Optional[Dict[str, Any]] = None  # NEW: Moodle structure info
    analysis_logs: Optional[List[Dict[str, Any]]] = None  # NEW: Analyzer logs for frontend

class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float
    service: str = "ilias-analyzer"

# Global job storage
jobs: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info("🚀 ILIAS Analyzer Service is starting...")
    yield
    
    # Cleanup
    logger.info("🔻 ILIAS Analyzer Service is shutting down... cleaning up temporary files")
    for job_id, job_data in jobs.items():
        try:
            # Delete uploaded ILIAS file
            ilias_path = Path(job_data.get("ilias_path", ""))
            if ilias_path.exists():
                ilias_path.unlink()
                logger.info("🗑️ Removed ILIAS file", path=str(ilias_path))
            
            # Delete extraction directories
            extract_dirs = list(Path(tempfile.gettempdir()).glob(f"ilias_extract_{job_id}_*"))
            for extract_dir in extract_dirs:
                if extract_dir.exists():
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    logger.info("🗑️ Removed extraction directory", path=str(extract_dir))
            
            # Delete MBZ file if exists
            mbz_path = job_data.get("mbz_path")
            if mbz_path and Path(mbz_path).exists():
                Path(mbz_path).unlink()
                logger.info("🗑️ Removed MBZ file", path=str(mbz_path))
                
        except Exception as e:
            logger.warning("⚠️ Error during shutdown cleanup", job_id=job_id, error=str(e))

# FastAPI App
app = FastAPI(
    title="OERSync-AI ILIAS Analyzer Service",
    description="Microservice für ILIAS-Export-Analyse und Moodle-Konvertierung",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service start time
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

async def process_ilias_analysis(job_id: str, file_path: Path, original_filename: str, convert_to_moodle: bool = False):
    """Background task for ILIAS to MBZ conversion and analysis"""
    logger.info("Starting ILIAS processing", job_id=job_id, filename=original_filename, convert_to_moodle=convert_to_moodle)
    
    start_time = time.time()
    temp_dir = None
    
    try:
        # Update to processing
        update_job_status(job_id, "processing", "Extracting ILIAS export...")
        
        # Create temporary directory for extraction
        temp_dir = Path(tempfile.mkdtemp(prefix=f"ilias_extract_{job_id}_"))
        
        # Extract ZIP file
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        logger.info("ILIAS export extracted", job_id=job_id, temp_dir=str(temp_dir))
        
        update_job_status(job_id, "processing", "Analyzing ILIAS structure...")
        
        # Initialize analyzer
        analyzer = IliasAnalyzer(str(temp_dir))
        success = analyzer.analyze()
        
        if not success:
            raise Exception("ILIAS analysis failed")
        
        # Hole die gesammelten Logs
        analysis_logs = analyzer.get_logs()
        
        logger.info("ILIAS analysis completed", job_id=job_id, 
                   course_title=analyzer.course_title,
                   modules_count=len(analyzer.modules),
                   log_entries=len(analysis_logs))
        
        mbz_path = None
        mbz_analysis_result = None
        conversion_report = None
        structure_info = None  # Initialize here
        
        if convert_to_moodle:
            update_job_status(job_id, "processing", "Converting to Moodle format...")
            
            try:
                logger.info("Starting Moodle conversion", job_id=job_id)
                converter = MoodleConverter(analyzer)
                mbz_path = converter.convert(generate_report=True)
                logger.info("Moodle conversion completed", job_id=job_id, mbz_path=mbz_path, mbz_size=os.path.getsize(mbz_path))
                
                # Hole Conversion-Report wenn verfügbar
                if converter.conversion_report:
                    conversion_report = {
                        "info_count": len(converter.conversion_report.info_issues),
                        "warning_count": len(converter.conversion_report.warning_issues),
                        "error_count": len(converter.conversion_report.error_issues),
                        "warnings": [
                            {
                                "item": issue.ilias_item,
                                "feature": issue.ilias_feature,
                                "message": issue.message,
                                "alternative": issue.moodle_alternative
                            }
                            for issue in converter.conversion_report.warning_issues[:10]  # Erste 10
                        ],
                        "errors": [
                            {
                                "item": issue.ilias_item,
                                "feature": issue.ilias_feature,
                                "message": issue.message,
                                "alternative": issue.moodle_alternative
                            }
                            for issue in converter.conversion_report.error_issues[:10]  # Erste 10
                        ]
                    }
                
                # Hole Struktur-Informationen wenn verfügbar
                structure_info = None
                if converter.moodle_structure:
                    structure_info = {
                        "sections_count": len(converter.moodle_structure.sections),
                        "activities_count": sum(len(s.activities) for s in converter.moodle_structure.sections),
                        "sections": [
                            {
                                "id": section.section_id,
                                "name": section.name,
                                "activities_count": len(section.activities)
                            }
                            for section in converter.moodle_structure.sections
                        ]
                    }
                
                logger.info("Moodle conversion completed", 
                           job_id=job_id, 
                           mbz_path=mbz_path,
                           has_report=conversion_report is not None,
                           has_structure=structure_info is not None)
                
                # Now analyze the MBZ file through the extractor service
                update_job_status(job_id, "processing", "Analyzing converted MBZ file...")
                
                # Send MBZ to extractor service
                import aiohttp
                extractor_url = os.getenv('EXTRACTOR_URL', 'http://localhost:8001')
                logger.info("Sending MBZ to extractor", job_id=job_id, extractor_url=extractor_url, mbz_path=mbz_path)
                
                async with aiohttp.ClientSession() as session:
                    with open(mbz_path, 'rb') as mbz_file:
                        data = aiohttp.FormData()
                        data.add_field('file', mbz_file, filename=os.path.basename(mbz_path))
                        
                        # Call extractor service
                        logger.debug("Posting MBZ to extractor", job_id=job_id, url=f'{extractor_url}/extract')
                        async with session.post(f'{extractor_url}/extract', data=data) as resp:
                            logger.info("Extractor response received", job_id=job_id, status=resp.status)
                            if resp.status == 200:
                                extractor_result = await resp.json()
                                extractor_job_id = extractor_result['job_id']
                                logger.info("MBZ sent to extractor successfully", job_id=job_id, extractor_job_id=extractor_job_id)
                                
                                # Poll extractor for results
                                max_attempts = 60
                                for attempt in range(max_attempts):
                                    await asyncio.sleep(2)
                                    logger.debug("Polling extractor for results", job_id=job_id, attempt=attempt+1, max_attempts=max_attempts)
                                    async with session.get(f'{extractor_url}/extract/{extractor_job_id}') as status_resp:
                                        status_data = await status_resp.json()
                                        logger.debug("Extractor status", job_id=job_id, extractor_status=status_data['status'])
                                        if status_data['status'] == 'completed':
                                            mbz_analysis_result = status_data
                                            logger.info("MBZ analysis completed successfully", job_id=job_id, 
                                                       sections_count=len(status_data.get('extracted_data', {}).get('sections', [])),
                                                       activities_count=len(status_data.get('extracted_data', {}).get('activities', [])))
                                            break
                                        elif status_data['status'] == 'failed':
                                            error_msg = status_data.get('error_message', 'Unknown error')
                                            logger.error("Extractor analysis failed", job_id=job_id, error=error_msg)
                                            raise Exception(f"MBZ analysis failed: {error_msg}")
                                else:
                                    logger.error("Extractor polling timeout", job_id=job_id)
                                    raise Exception("MBZ analysis timeout - extractor did not complete in time")
                            else:
                                error_text = await resp.text()
                                logger.error("Failed to send MBZ to extractor", job_id=job_id, status=resp.status, error=error_text)
                                raise Exception(f"Failed to send MBZ to extractor: HTTP {resp.status} - {error_text}")
                
            except Exception as e:
                logger.error("Moodle conversion/analysis failed", job_id=job_id, error=str(e), exc_info=True)
                # Check if it's an extractor communication error
                if "extractor" in str(e).lower() or "connection" in str(e).lower():
                    logger.warning("Extractor service nicht verfügbar - Fallback ohne Extractor-Analyse", job_id=job_id)
                    # Conversion was successful, but extractor failed
                    # Continue without extractor analysis - user can still download MBZ
                    if mbz_path and os.path.exists(mbz_path):
                        logger.info("MBZ-Datei wurde erfolgreich erstellt, aber Extractor-Analyse fehlgeschlagen", 
                                   job_id=job_id, mbz_path=mbz_path)
                        # Don't raise exception - continue with fallback
                    else:
                        raise Exception(f"Conversion failed: {str(e)}")
                else:
                    raise Exception(f"Conversion failed: {str(e)}")
        
        processing_time = time.time() - start_time
        
        # If MBZ was analyzed, use that data (from extractor)
        if mbz_analysis_result and mbz_analysis_result.get('extracted_data'):
            # Erstelle ILIAS analysis_data auch für MBZ-Konvertierungen
            analysis_data = {
                "course_title": analyzer.course_title,
                "installation_id": analyzer.installation_id,
                "installation_url": analyzer.installation_url,
                "modules_count": len(analyzer.modules),
                "has_container_structure": analyzer.container_structure is not None,
                "modules": [
                    {
                        "id": module.id,
                        "title": module.title,
                        "type": module.type,
                        "items": module.items
                    }
                    for module in analyzer.modules
                ]
            }
            
            update_job_status(
                job_id,
                "completed",
                "ILIAS successfully converted to MBZ and analyzed!",
                completed_at=datetime.now(),
                processing_time_seconds=processing_time,
                analysis_data=analysis_data,  # NEU: ILIAS Module hinzufügen
                extracted_data=mbz_analysis_result.get('extracted_data'),
                moodle_mbz_available=True,
                mbz_path=mbz_path,
                ilias_source={
                    "course_title": analyzer.course_title,
                    "modules_count": len(analyzer.modules),
                    "has_container_structure": analyzer.container_structure is not None
                },
                conversion_report=conversion_report,  # NEW
                moodle_structure=structure_info,  # NEW
                analysis_logs=analysis_logs  # NEW: Logs ans Frontend
            )
        else:
            # Simple analysis without conversion (or conversion without extractor)
            analysis_data = {
                "course_title": analyzer.course_title,
                "installation_id": analyzer.installation_id,
                "installation_url": analyzer.installation_url,
                "modules_count": len(analyzer.modules),
                "has_container_structure": analyzer.container_structure is not None,
                "modules": [
                    {
                        "id": module.id,
                        "title": module.title,
                        "type": module.type,
                        "items": module.items
                    }
                    for module in analyzer.modules
                ]
            }
            
            # Wenn konvertiert wurde (aber keine extractor-Analyse), markiere MBZ als verfügbar
            is_mbz_available = convert_to_moodle and mbz_path is not None
            
            # Erstelle minimale extracted_data aus Moodle-Struktur wenn Extractor fehlgeschlagen
            extracted_data_fallback = None
            if is_mbz_available and structure_info:
                logger.info("Erstelle Fallback extracted_data aus Moodle-Struktur", job_id=job_id)
                extracted_data_fallback = {
                    "course_name": analysis_data.get('course_title', 'Konvertierter ILIAS-Kurs'),
                    "course_summary": f"Aus ILIAS konvertiert - {structure_info['sections_count']} Sections, {structure_info['activities_count']} Activities",
                    "sections": structure_info.get('sections', []),
                    "activities": sum([s.get('activities_count', 0) for s in structure_info.get('sections', [])]),
                    "moodle_version": "Converted from ILIAS",
                    "backup_date": datetime.now().isoformat(),
                    "warning": "⚠️ Extractor-Service nicht verfügbar - Nur Struktur-Übersicht. Bitte MBZ-Datei herunterladen für vollständige Inhalte."
                }
            
            update_job_status(
                job_id,
                "completed",
                f"ILIAS {'converted to Moodle' if is_mbz_available else 'analysis completed'}. Found {len(analyzer.modules)} modules." + 
                (" (Extractor-Analyse fehlgeschlagen - nur Struktur-Übersicht)" if is_mbz_available and extracted_data_fallback else ""),
                completed_at=datetime.now(),
                processing_time_seconds=processing_time,
                analysis_data=analysis_data,
                extracted_data=extracted_data_fallback,  # NEU: Fallback-Daten wenn Extractor fehlschlägt
                moodle_mbz_available=is_mbz_available,
                mbz_path=mbz_path if is_mbz_available else None,
                conversion_report=conversion_report if is_mbz_available else None,  # NEW
                moodle_structure=structure_info if is_mbz_available else None,  # NEW
                analysis_logs=analysis_logs  # NEW: Logs ans Frontend
            )
        
        logger.info("ILIAS processing completed successfully",
                   job_id=job_id, processing_time=processing_time)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Processing failed: {str(e)}"
        
        update_job_status(
            job_id,
            "failed",
            error_message,
            completed_at=datetime.now(),
            processing_time_seconds=processing_time,
            error_message=error_message
        )
        
        logger.error("ILIAS processing failed", job_id=job_id, error=str(e), processing_time=processing_time)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_start_time
    return HealthResponse(uptime_seconds=uptime)

@app.post("/analyze", response_model=AnalysisJobResponse)
async def analyze_ilias(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    convert_to_moodle: bool = False
):
    """
    Upload and analyze ILIAS export file
    
    Creates a background job for processing the ILIAS export.
    Returns job ID for status tracking.
    
    Optional: Convert to Moodle MBZ format
    """
    
    # Validate file
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .zip files are allowed."
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file temporarily
        temp_file = Path(tempfile.mktemp(suffix=".zip"))
        
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = len(content)
        ilias_path = str(temp_file)
        
        # Create job record
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "message": "Job created, waiting for processing",
            "file_name": file.filename,
            "file_size": file_size,
            "ilias_path": ilias_path,
            "created_at": datetime.now(),
            "completed_at": None,
            "processing_time_seconds": None,
            "analysis_data": None,
            "extracted_data": None,
            "moodle_mbz_available": False,
            "error_message": None,
            "ilias_source": None,
            "mbz_path": None
        }
        
        jobs[job_id] = job_data
        
        # Start background processing
        background_tasks.add_task(
            process_ilias_analysis,
            job_id,
            temp_file,
            file.filename,
            convert_to_moodle
        )
        
        logger.info("Analysis job created", job_id=job_id, filename=file.filename, size=file_size)
        
        return AnalysisJobResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        if 'temp_file' in locals() and temp_file.exists():
            temp_file.unlink()
        
        logger.error("Failed to create analysis job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create analysis job: {str(e)}")

@app.get("/analyze/{job_id}/status", response_model=JobStatus)
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

@app.get("/analyze/{job_id}", response_model=AnalysisResult)
async def get_job_result(job_id: str):
    """Get job result"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] == "pending" or job["status"] == "processing":
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": job["status"],
                "message": job["message"],
                "created_at": job["created_at"].isoformat()
            }
        )
    
    return AnalysisResult(**job)

@app.get("/analyze/{job_id}/download-moodle")
async def download_moodle_mbz(job_id: str):
    """Download converted Moodle MBZ file"""
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not job.get("moodle_mbz_available"):
        raise HTTPException(status_code=404, detail="Moodle MBZ not available for this job")
    
    mbz_path = job.get("mbz_path")
    if not mbz_path or not Path(mbz_path).exists():
        raise HTTPException(status_code=404, detail="Moodle MBZ file not found")
    
    return FileResponse(
        path=mbz_path,
        filename=os.path.basename(mbz_path),
        media_type="application/octet-stream"
    )

@app.get("/jobs", response_model=List[AnalysisJobResponse])
async def list_jobs():
    """List all jobs"""
    job_list = []
    for job_data in jobs.values():
        job_list.append(AnalysisJobResponse(**job_data))
    
    # Sort by creation time (newest first)
    job_list.sort(key=lambda x: x.created_at, reverse=True)
    
    return job_list

@app.delete("/analyze/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Don't allow deletion of processing jobs
    if job["status"] == "processing":
        raise HTTPException(status_code=400, detail="Cannot delete job that is currently processing")
    
    # Cleanup files
    try:
        ilias_path = Path(job.get("ilias_path", ""))
        if ilias_path.exists():
            ilias_path.unlink()
        
        mbz_path = job.get("mbz_path")
        if mbz_path and Path(mbz_path).exists():
            Path(mbz_path).unlink()
    except Exception as e:
        logger.warning("Error cleaning up files for deleted job", job_id=job_id, error=str(e))
    
    del jobs[job_id]
    logger.info("Job deleted", job_id=job_id)
    
    return {"message": "Job deleted successfully", "job_id": job_id}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

if __name__ == "__main__":
    import os
    port = int(os.getenv("SERVICE_PORT", "8004"))  # Default to 8004 for local dev
    logger.info(f"Starting OERSync-AI ILIAS Analyzer Service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

