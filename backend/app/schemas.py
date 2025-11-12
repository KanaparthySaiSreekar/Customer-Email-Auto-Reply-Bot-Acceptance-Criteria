from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmailBase(BaseModel):
    sender: str
    subject: str
    content: str

class EmailCreate(EmailBase):
    pass

class EmailUpdate(BaseModel):
    sender: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    folder: Optional[str] = None

class EmailResponse(EmailBase):
    id: int
    case_number: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    folder: Optional[str] = None
    needs_review: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TemplateBase(BaseModel):
    name: str
    intent_type: str
    subject_template: str
    body_template: str

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    intent_type: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None

class TemplateResponse(TemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DraftBase(BaseModel):
    subject: str
    content: str

class DraftCreate(DraftBase):
    email_id: int

class DraftUpdate(BaseModel):
    subject: Optional[str] = None
    content: Optional[str] = None
    approved: Optional[bool] = None

class DraftResponse(DraftBase):
    id: int
    email_id: int
    approved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailDetailResponse(EmailResponse):
    drafts: list[DraftResponse] = []

    class Config:
        from_attributes = True

class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    needs_review: bool

class ImportResult(BaseModel):
    success: int
    failed: int
    errors: list[str]
    imported_emails: list[EmailResponse]
