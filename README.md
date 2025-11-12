# Customer Email Auto-Reply Bot

An intelligent email management system that automatically classifies customer emails by intent (billing, support, bug, feature) and generates contextual auto-reply drafts with case number tracking.

## Features

### A. Demo Flow
- CSV email import with batch processing
- Visible inbox list with categorized emails
- Automatic intent classification with confidence scoring
- Smart folder/category assignment
- One-click auto-reply draft generation
- Editable drafts with approval workflow
- Unique case number generation and tracking

### B. Usability
- Inbox list view with intent badges and confidence indicators
- Detailed email view with original content
- Visual folder assignments
- Inline draft editor
- Approval status indicators
- "Needs human review" flags for low-confidence classifications

### C. Data & CRUD
- Full CRUD operations for emails, templates, and drafts via REST API
- SQLite database with persistent storage
- Unique case numbers traceable to original emails
- Template management system

### D. AI Quality
- Intent classification: billing, support, bug, feature
- Confidence scoring system
- Courteous, brand-neutral tone
- Placeholder resolution (name, order ID extraction)
- Low-confidence flagging (< 40% triggers review status)

### E. Reliability
- Classification + draft generation completes in ≤5 seconds
- Graceful CSV error handling with detailed error reporting
- Partial import support
- Performance monitoring with response time headers

### F. Documentation & Testing
- Auto-generated API documentation (FastAPI/OpenAPI)
- Comprehensive smoke tests covering full workflow
- Sample data included

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── database.py          # Database configuration
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── crud.py              # CRUD operations
│   │   ├── classifier.py        # Email classification engine
│   │   └── draft_generator.py  # Auto-reply generation
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_smoke.py        # Smoke tests
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Main UI
│   ├── styles.css               # Styling
│   └── app.js                   # Frontend logic
├── data/
│   └── sample_emails.csv        # Sample test data
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Start a simple HTTP server (Python 3):
```bash
python -m http.server 8080
```

Or use any other static file server.

3. Open your browser and navigate to:
```
http://localhost:8080
```

## Usage Guide

### 1. Import Sample Emails

**Via UI:**
1. Click "Import CSV" button
2. Select `data/sample_emails.csv`
3. Review import results

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/emails/import" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample_emails.csv"
```

### 2. Browse Emails

- View all emails in the sidebar
- Filter by folder: All, Billing, Support, Bug Reports, Feature Requests
- Intent badges show classification (color-coded)
- Confidence percentage displayed
- "Review" badge for low-confidence items

### 3. View Email Details

Click any email to see:
- Original sender and subject
- Unique case number
- Classification intent and confidence score
- Folder assignment
- Full email content
- Generated drafts (if any)

### 4. Generate Auto-Reply

1. Select an email
2. Click "Generate Auto-Reply"
3. Draft is created with:
   - Case number reference
   - Personalized greeting (extracts name if present)
   - Intent-specific response template
   - Next steps outline

### 5. Edit and Approve Drafts

1. Click "Edit" on any draft
2. Modify subject and content as needed
3. Click "Save" to update
4. Click "Approve" to mark as ready

### 6. Re-classify Email

If classification is incorrect:
1. Select the email
2. Click "Re-classify"
3. System will re-analyze and update intent/folder

## API Documentation

### Access Interactive API Docs

Once the backend is running, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

#### Emails
- `POST /api/emails/` - Create email with auto-classification
- `GET /api/emails/` - List emails (supports `?folder=` filter)
- `GET /api/emails/{id}` - Get email details with drafts
- `PUT /api/emails/{id}` - Update email
- `DELETE /api/emails/{id}` - Delete email
- `POST /api/emails/{id}/classify` - Re-classify email
- `POST /api/emails/{id}/generate-draft` - Generate auto-reply draft
- `POST /api/emails/import` - Import from CSV

#### Drafts
- `POST /api/drafts/` - Create draft manually
- `GET /api/drafts/{id}` - Get draft
- `PUT /api/drafts/{id}` - Update draft (edit or approve)
- `DELETE /api/drafts/{id}` - Delete draft

#### Templates
- `POST /api/templates/` - Create template
- `GET /api/templates/` - List all templates
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

#### Health
- `GET /api/health` - Health check

## Running Tests

### Smoke Tests

Run the comprehensive smoke test suite:

```bash
cd backend
pytest tests/test_smoke.py -v -s
```

Tests cover:
1. CSV import → classification → folder changes
2. Draft creation → editing → approval
3. Performance validation (≤5s requirement)
4. Error handling
5. Low-confidence flagging
6. Placeholder resolution
7. CRUD operations

### Expected Output
```
✓ Step 1: CSV import successful - 4 emails imported
✓ Step 2: All emails classified with intent and confidence
✓ Step 3: Diverse intents detected: {billing, support, bug, feature}
✓ Step 4: Folders correctly assigned based on intent
✓ Step 5.1: Draft generated in 0.032s (case CASE-ABC123...)
...
✓ Step 7: Draft approved successfully
✓ Step 8: Draft edited successfully
🎉 SMOKE TEST PASSED: Complete flow verified
```

## CSV Format

Expected CSV format for email import:

```csv
sender,subject,content
john@example.com,Subject line,Email body content here...
```

**Required fields:**
- `sender` - Email address of sender
- `subject` - Email subject line
- `content` - Full email body

See `data/sample_emails.csv` for examples.

## Classification System

### Intent Categories

1. **Billing** - Payment, invoices, refunds, charges, subscriptions
2. **Support** - Help requests, how-to questions, guidance
3. **Bug** - Error reports, crashes, malfunctions, defects
4. **Feature** - Feature requests, enhancements, suggestions

### Confidence Scoring

- **High confidence (≥40%)**: Auto-filed to appropriate folder
- **Low confidence (<40%)**: Flagged with "Needs human review"

### Placeholder Resolution

The system automatically extracts and uses:
- **Customer name**: Detected from phrases like "My name is...", "I'm..."
- **Order ID**: Patterns like "#12345", "order 12345", "ORDER-12345"
- **Email addresses**: Extracted for reference

## Performance

The system is designed to meet strict performance requirements:

- **Classification**: <2 seconds
- **Draft generation**: <3 seconds
- **Combined operation**: ≤5 seconds (acceptance criteria)

Performance metrics are logged in API response headers (`X-Process-Time`).

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is not in use

### Frontend can't connect to API
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Ensure correct API_BASE URL in `frontend/app.js`

### CSV import fails
- Verify CSV has required columns: sender, subject, content
- Check file encoding is UTF-8
- Review error messages in import results modal

### Low classification accuracy
- Review sample emails in `data/sample_emails.csv`
- The classifier uses keyword matching; ambiguous emails will have low confidence
- Can be extended with actual AI models (OpenAI, etc.) for production use

## Future Enhancements

- Integration with real email providers (IMAP/SMTP)
- AI model integration (OpenAI GPT, Claude API)
- Multi-language support
- Custom template editor in UI
- Email threading and conversation tracking
- Automated sending with approval workflow
- Analytics dashboard
- Role-based access control

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please visit the project repository.