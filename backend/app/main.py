from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from . import models, schemas, crud
from .database import engine, get_db, init_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer Email Auto-Reply Bot API",
    description="API for managing customer emails, auto-classification, and draft generation",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

# Email endpoints
@app.post("/api/emails/", response_model=schemas.EmailResponse, status_code=201)
def create_email(email: schemas.EmailCreate, db: Session = Depends(get_db)):
    """Create a new email with automatic classification."""
    start_time = time.time()
    db_email = crud.create_email(db, email)
    elapsed = time.time() - start_time

    if elapsed > 5.0:
        print(f"WARNING: Email creation took {elapsed:.2f}s (exceeds 5s threshold)")

    return db_email

@app.get("/api/emails/", response_model=List[schemas.EmailResponse])
def list_emails(
    skip: int = 0,
    limit: int = 100,
    folder: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all emails with optional folder filter."""
    emails = crud.get_emails(db, skip=skip, limit=limit, folder=folder)
    return emails

@app.get("/api/emails/{email_id}", response_model=schemas.EmailDetailResponse)
def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get email details including drafts."""
    db_email = crud.get_email(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email not found")
    return db_email

@app.put("/api/emails/{email_id}", response_model=schemas.EmailResponse)
def update_email(email_id: int, email: schemas.EmailUpdate, db: Session = Depends(get_db)):
    """Update email details."""
    db_email = crud.update_email(db, email_id, email)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email not found")
    return db_email

@app.delete("/api/emails/{email_id}", status_code=204)
def delete_email(email_id: int, db: Session = Depends(get_db)):
    """Delete an email."""
    success = crud.delete_email(db, email_id)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found")

@app.post("/api/emails/{email_id}/classify", response_model=schemas.EmailResponse)
def classify_email(email_id: int, db: Session = Depends(get_db)):
    """Classify or re-classify an email."""
    start_time = time.time()
    db_email = crud.classify_email(db, email_id)
    elapsed = time.time() - start_time

    if not db_email:
        raise HTTPException(status_code=404, detail="Email not found")

    if elapsed > 5.0:
        print(f"WARNING: Classification took {elapsed:.2f}s (exceeds 5s threshold)")

    return db_email

@app.post("/api/emails/{email_id}/generate-draft", response_model=schemas.DraftResponse)
def generate_draft(email_id: int, db: Session = Depends(get_db)):
    """Generate auto-reply draft for an email."""
    start_time = time.time()
    db_draft = crud.generate_draft_for_email(db, email_id)
    elapsed = time.time() - start_time

    if not db_draft:
        raise HTTPException(status_code=404, detail="Email not found")

    if elapsed > 5.0:
        print(f"WARNING: Draft generation took {elapsed:.2f}s (exceeds 5s threshold)")

    return db_draft

@app.post("/api/emails/import", response_model=schemas.ImportResult)
async def import_emails(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import emails from CSV file."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        result = crud.import_emails_from_csv(db, csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

# Draft endpoints
@app.post("/api/drafts/", response_model=schemas.DraftResponse, status_code=201)
def create_draft(draft: schemas.DraftCreate, db: Session = Depends(get_db)):
    """Create a draft manually."""
    db_draft = crud.create_draft(db, draft)
    return db_draft

@app.get("/api/drafts/{draft_id}", response_model=schemas.DraftResponse)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    """Get draft by ID."""
    db_draft = crud.get_draft(db, draft_id)
    if not db_draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return db_draft

@app.put("/api/drafts/{draft_id}", response_model=schemas.DraftResponse)
def update_draft(draft_id: int, draft: schemas.DraftUpdate, db: Session = Depends(get_db)):
    """Update draft (e.g., edit content or approve)."""
    db_draft = crud.update_draft(db, draft_id, draft)
    if not db_draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return db_draft

@app.delete("/api/drafts/{draft_id}", status_code=204)
def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    """Delete a draft."""
    success = crud.delete_draft(db, draft_id)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")

# Template endpoints
@app.post("/api/templates/", response_model=schemas.TemplateResponse, status_code=201)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    """Create email template."""
    db_template = crud.create_template(db, template)
    return db_template

@app.get("/api/templates/", response_model=List[schemas.TemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """List all templates."""
    templates = crud.get_templates(db)
    return templates

@app.get("/api/templates/{template_id}", response_model=schemas.TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get template by ID."""
    db_template = crud.get_template(db, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@app.put("/api/templates/{template_id}", response_model=schemas.TemplateResponse)
def update_template(template_id: int, template: schemas.TemplateUpdate, db: Session = Depends(get_db)):
    """Update template."""
    db_template = crud.update_template(db, template_id, template)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@app.delete("/api/templates/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete template."""
    success = crud.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

# Health check
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "email-auto-reply-bot"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
