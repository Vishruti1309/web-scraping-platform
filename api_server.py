from fastapi import FastAPI
from scheduler_orchestrator import ScrapingOrchestrator
from fastapi.middleware.cors import CORSMiddleware
import uuid
from storage_manager import FileExporter
from fastapi import Body       
import threading


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
jobs = {}
orchestrator = ScrapingOrchestrator()

@app.get("/")
def home():
    return {"message": "Job Tracker API is running"}

import uuid
import threading

@app.post("/scrape/{source}")
def scrape(source: str):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "running",
        "source": source,
        "result": None
    }

    def run_scraper():
        result = orchestrator.scrape_source(source)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result

    thread = threading.Thread(target=run_scraper)
    thread.start()

    return {"job_id": job_id, "status": "started"}

@app.get("/job/{job_id}")
def get_job(job_id: str):
    return jobs.get(job_id, {"error": "Job not found"})

@app.get("/data/{source}")
def get_data(source: str):
    data = orchestrator.storage.get_data(source, limit=50)
    return data

@app.post("/save")
def save_job(job: dict = Body(...)):
    from storage_manager import StorageManager, FileExporter

    storage = StorageManager()
    exporter = FileExporter()

    # Save to DB
    storage.save_saved_job(job)

    # EXPORT
    # exporter.export_all_formats([job], "saved_jobs")

    # return {"message": "Job saved successfully"}
    
    files = exporter.export_all_formats([job], "saved_jobs")

    # Get one file (CSV for example)
    file_path = files.get("csv")

    filename = os.path.basename(file_path) if file_path else None

    return {
        "message": "Job saved successfully",
        "file": filename
    }

@app.delete("/clear-data")
def clear_data():
    from storage_manager import StorageManager

    storage = StorageManager()
    cursor = storage.connection.cursor()

    cursor.execute("DELETE FROM saved_jobs")
    storage.connection.commit()

    return {"message": "All scraped data deleted"}


@app.get("/saved-jobs")
def get_saved_jobs():
    from storage_manager import StorageManager

    storage = StorageManager()
    cursor = storage.connection.cursor()

    cursor.execute("SELECT * FROM saved_jobs ORDER BY saved_at DESC")
    rows = cursor.fetchall()

    data = [dict(row) for row in rows]

    return data

from fastapi.responses import FileResponse
import os

@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = f"exports/{filename}"

    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    
    return {"error": "File not found"}