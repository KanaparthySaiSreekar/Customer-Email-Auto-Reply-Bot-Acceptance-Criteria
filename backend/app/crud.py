from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from . import models, schemas
from .classifier import EmailClassifier
from .draft_generator import DraftGenerator
import csv
import io
from datetime import datetime

classifier = EmailClassifier()
draft_gen = DraftGenerator()

def create_email(db: Session, email: schemas.EmailCreate, auto_classify: bool = True) -> models.Email:
    """Create a new email with optional auto-classification."""
    case_number = draft_gen.generate_case_number()

    db_email = models.Email(
        case_number=case_number,
        sender=email.sender,
        subject=email.subject,
        content=email.content
    )

    if auto_classify:
        intent, confidence, needs_review = classifier.classify(email.subject, email.content)
        db_email.intent = intent
        db_email.confidence = confidence
        db_email.folder = intent  # Folder corresponds to intent
        db_email.needs_review = needs_review

    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def get_email(db: Session, email_id: int) -> Optional[models.Email]:
    """Get email by ID."""
    return db.query(models.Email).filter(models.Email.id == email_id).first()

def get_email_by_case(db: Session, case_number: str) -> Optional[models.Email]:
    """Get email by case number."""
    return db.query(models.Email).filter(models.Email.case_number == case_number).first()

def get_emails(db: Session, skip: int = 0, limit: int = 100, folder: Optional[str] = None) -> List[models.Email]:
    """Get list of emails with optional folder filter."""
    query = db.query(models.Email)
    if folder:
        query = query.filter(models.Email.folder == folder)
    return query.order_by(desc(models.Email.created_at)).offset(skip).limit(limit).all()

def update_email(db: Session, email_id: int, email_update: schemas.EmailUpdate) -> Optional[models.Email]:
    """Update email."""
    db_email = get_email(db, email_id)
    if not db_email:
        return None

    update_data = email_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_email, key, value)

    db_email.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_email)
    return db_email

def delete_email(db: Session, email_id: int) -> bool:
    """Delete email."""
    db_email = get_email(db, email_id)
    if not db_email:
        return False

    db.delete(db_email)
    db.commit()
    return True

def classify_email(db: Session, email_id: int) -> Optional[models.Email]:
    """Classify an email and update its intent, confidence, and folder."""
    db_email = get_email(db, email_id)
    if not db_email:
        return None

    intent, confidence, needs_review = classifier.classify(db_email.subject, db_email.content)
    db_email.intent = intent
    db_email.confidence = confidence
    db_email.folder = intent
    db_email.needs_review = needs_review
    db_email.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_email)
    return db_email

def generate_draft_for_email(db: Session, email_id: int) -> Optional[models.Draft]:
    """Generate auto-reply draft for an email."""
    db_email = get_email(db, email_id)
    if not db_email:
        return None

    # Ensure email is classified
    if not db_email.intent:
        classify_email(db, email_id)
        db.refresh(db_email)

    # Extract information for placeholders
    extracted_info = classifier.extract_info(db_email.content)

    # Generate draft
    draft_content = draft_gen.generate_draft(
        intent=db_email.intent,
        case_number=db_email.case_number,
        original_subject=db_email.subject,
        extracted_info=extracted_info
    )

    # Create draft
    db_draft = models.Draft(
        email_id=email_id,
        subject=draft_content["subject"],
        content=draft_content["content"]
    )

    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft

def create_draft(db: Session, draft: schemas.DraftCreate) -> Optional[models.Draft]:
    """Create a draft manually."""
    db_draft = models.Draft(**draft.model_dump())
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft

def get_draft(db: Session, draft_id: int) -> Optional[models.Draft]:
    """Get draft by ID."""
    return db.query(models.Draft).filter(models.Draft.id == draft_id).first()

def update_draft(db: Session, draft_id: int, draft_update: schemas.DraftUpdate) -> Optional[models.Draft]:
    """Update draft."""
    db_draft = get_draft(db, draft_id)
    if not db_draft:
        return None

    update_data = draft_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_draft, key, value)

    db_draft.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_draft)
    return db_draft

def delete_draft(db: Session, draft_id: int) -> bool:
    """Delete draft."""
    db_draft = get_draft(db, draft_id)
    if not db_draft:
        return False

    db.delete(db_draft)
    db.commit()
    return True

def create_template(db: Session, template: schemas.TemplateCreate) -> models.Template:
    """Create email template."""
    db_template = models.Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_templates(db: Session) -> List[models.Template]:
    """Get all templates."""
    return db.query(models.Template).all()

def get_template(db: Session, template_id: int) -> Optional[models.Template]:
    """Get template by ID."""
    return db.query(models.Template).filter(models.Template.id == template_id).first()

def update_template(db: Session, template_id: int, template_update: schemas.TemplateUpdate) -> Optional[models.Template]:
    """Update template."""
    db_template = get_template(db, template_id)
    if not db_template:
        return None

    update_data = template_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)

    db_template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_template)
    return db_template

def delete_template(db: Session, template_id: int) -> bool:
    """Delete template."""
    db_template = get_template(db, template_id)
    if not db_template:
        return False

    db.delete(db_template)
    db.commit()
    return True

def import_emails_from_csv(db: Session, csv_content: str) -> dict:
    """
    Import emails from CSV content.
    Expected format: sender,subject,content
    Returns: dict with success/failure counts and errors
    """
    result = {
        "success": 0,
        "failed": 0,
        "errors": [],
        "imported_emails": []
    }

    try:
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        required_fields = ["sender", "subject", "content"]

        # Validate headers
        if not all(field in reader.fieldnames for field in required_fields):
            result["errors"].append(f"CSV must contain columns: {', '.join(required_fields)}")
            result["failed"] += 1
            return result

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            try:
                # Validate row data
                if not all(row.get(field, "").strip() for field in required_fields):
                    result["errors"].append(f"Row {row_num}: Missing required fields")
                    result["failed"] += 1
                    continue

                # Create email
                email_data = schemas.EmailCreate(
                    sender=row["sender"].strip(),
                    subject=row["subject"].strip(),
                    content=row["content"].strip()
                )

                db_email = create_email(db, email_data, auto_classify=True)
                result["success"] += 1
                result["imported_emails"].append(db_email)

            except Exception as e:
                result["errors"].append(f"Row {row_num}: {str(e)}")
                result["failed"] += 1

    except Exception as e:
        result["errors"].append(f"CSV parsing error: {str(e)}")
        result["failed"] += 1

    return result
