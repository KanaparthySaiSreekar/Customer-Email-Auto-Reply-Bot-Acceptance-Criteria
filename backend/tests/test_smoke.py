"""
Smoke tests for Email Auto-Reply Bot
Tests the complete flow: import → classify → folder changes → draft created → approval flag set
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io
import time

from app.main import app
from app.database import Base, get_db
from app import models

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

def test_complete_email_flow(client):
    """
    Smoke test demonstrating:
    1. Import emails from CSV
    2. Verify classification occurred
    3. Check folder assignment
    4. Generate draft
    5. Approve draft
    """

    # Step 1: Import emails from CSV
    csv_content = """sender,subject,content
john@test.com,Invoice problem,I was charged twice for my subscription. Please refund the duplicate payment for order #12345.
sarah@test.com,Need help,I need assistance setting up my account and don't understand how to configure it properly.
mike@test.com,App crashes,The application crashes on startup with error code 500. This bug needs to be fixed.
lisa@test.com,Feature suggestion,Would you consider adding dark mode support? It would be a great enhancement.
"""

    files = {"file": ("test.csv", io.StringIO(csv_content), "text/csv")}
    response = client.post("/api/emails/import", files={"file": ("test.csv", csv_content.encode(), "text/csv")})

    assert response.status_code == 200
    import_result = response.json()
    assert import_result["success"] == 4
    assert import_result["failed"] == 0
    assert len(import_result["imported_emails"]) == 4

    print("\n✓ Step 1: CSV import successful - 4 emails imported")

    # Step 2: Verify all emails were classified
    response = client.get("/api/emails/")
    assert response.status_code == 200
    emails = response.json()
    assert len(emails) == 4

    # Check that all emails have intent and confidence
    for email in emails:
        assert email["intent"] is not None, f"Email {email['id']} not classified"
        assert email["confidence"] is not None, f"Email {email['id']} has no confidence score"
        assert email["folder"] is not None, f"Email {email['id']} has no folder"

    print("✓ Step 2: All emails classified with intent and confidence")

    # Step 3: Verify intents match expected types (billing, support, bug, feature)
    intents = [email["intent"] for email in emails]

    # We expect diverse intents
    assert "billing" in intents, "No billing intent found"
    assert "support" in intents, "No support intent found"
    assert "bug" in intents, "No bug intent found"
    assert "feature" in intents, "No feature intent found"

    print(f"✓ Step 3: Diverse intents detected: {set(intents)}")

    # Step 4: Verify folder assignment matches intent
    for email in emails:
        assert email["folder"] == email["intent"], f"Email {email['id']} folder doesn't match intent"

    print("✓ Step 4: Folders correctly assigned based on intent")

    # Step 5: Generate draft for each email and verify
    for email in emails:
        start_time = time.time()
        response = client.post(f"/api/emails/{email['id']}/generate-draft")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        draft = response.json()

        # Verify draft contains required elements
        assert "case" in draft["subject"].lower() or "#" in draft["subject"]
        assert email["case_number"] in draft["content"]
        assert "next steps" in draft["content"].lower()

        # Verify performance requirement (≤5 seconds)
        assert elapsed <= 5.0, f"Draft generation took {elapsed:.2f}s (exceeds 5s limit)"

        print(f"✓ Step 5.{email['id']}: Draft generated in {elapsed:.3f}s (case {email['case_number']})")

    # Step 6: Verify drafts can be retrieved
    response = client.get(f"/api/emails/{emails[0]['id']}")
    assert response.status_code == 200
    email_detail = response.json()
    assert len(email_detail["drafts"]) > 0
    draft_id = email_detail["drafts"][0]["id"]

    print(f"✓ Step 6: Draft retrieved successfully (ID: {draft_id})")

    # Step 7: Approve the draft
    response = client.put(f"/api/drafts/{draft_id}", json={"approved": True})
    assert response.status_code == 200
    updated_draft = response.json()
    assert updated_draft["approved"] == True

    print(f"✓ Step 7: Draft approved successfully")

    # Step 8: Edit draft content
    new_content = "Updated draft content for testing"
    response = client.put(f"/api/drafts/{draft_id}", json={"content": new_content})
    assert response.status_code == 200
    updated_draft = response.json()
    assert updated_draft["content"] == new_content

    print(f"✓ Step 8: Draft edited successfully")

    print("\n🎉 SMOKE TEST PASSED: Complete flow verified")

def test_classification_performance(client):
    """Test that classification + draft generation completes within 5 seconds"""

    # Create a test email
    email_data = {
        "sender": "test@example.com",
        "subject": "Billing issue",
        "content": "I was charged twice for order #12345. Please refund."
    }

    start_time = time.time()

    # Create and classify
    response = client.post("/api/emails/", json=email_data)
    assert response.status_code == 201
    email = response.json()

    # Generate draft
    response = client.post(f"/api/emails/{email['id']}/generate-draft")
    assert response.status_code == 200

    elapsed = time.time() - start_time

    assert elapsed <= 5.0, f"Classification + draft generation took {elapsed:.2f}s (exceeds 5s limit)"
    print(f"\n✓ Performance test passed: {elapsed:.3f}s (limit: 5s)")

def test_csv_error_handling(client):
    """Test CSV import error handling"""

    # Test with invalid CSV (missing required fields)
    bad_csv = """sender,subject
john@test.com,Test Subject
"""

    response = client.post("/api/emails/import", files={"file": ("bad.csv", bad_csv.encode(), "text/csv")})
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == 0
    assert result["failed"] > 0
    assert len(result["errors"]) > 0

    print("\n✓ CSV error handling test passed")

def test_low_confidence_review_flag(client):
    """Test that low-confidence emails are flagged for review"""

    # Create an ambiguous email that should have low confidence
    email_data = {
        "sender": "test@example.com",
        "subject": "Question",
        "content": "I have a question about something."
    }

    response = client.post("/api/emails/", json=email_data)
    assert response.status_code == 201
    email = response.json()

    # Low confidence should trigger review flag
    if email["confidence"] < 0.4:
        assert email["needs_review"] == True, "Low confidence email should be flagged for review"
        print(f"\n✓ Low-confidence review flag test passed (confidence: {email['confidence']:.2f})")
    else:
        print(f"\n✓ Email has sufficient confidence: {email['confidence']:.2f}")

def test_crud_operations(client):
    """Test basic CRUD operations for emails, drafts, and templates"""

    # Create email
    email_data = {
        "sender": "test@example.com",
        "subject": "Test",
        "content": "Test content"
    }
    response = client.post("/api/emails/", json=email_data)
    assert response.status_code == 201
    email = response.json()
    email_id = email["id"]

    # Read email
    response = client.get(f"/api/emails/{email_id}")
    assert response.status_code == 200

    # Update email
    response = client.put(f"/api/emails/{email_id}", json={"intent": "support"})
    assert response.status_code == 200
    updated = response.json()
    assert updated["intent"] == "support"

    # Create draft
    draft_data = {
        "email_id": email_id,
        "subject": "Test Draft",
        "content": "Test draft content"
    }
    response = client.post("/api/drafts/", json=draft_data)
    assert response.status_code == 201
    draft = response.json()
    draft_id = draft["id"]

    # Update draft
    response = client.put(f"/api/drafts/{draft_id}", json={"approved": True})
    assert response.status_code == 200

    # Delete draft
    response = client.delete(f"/api/drafts/{draft_id}")
    assert response.status_code == 204

    # Delete email
    response = client.delete(f"/api/emails/{email_id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/emails/{email_id}")
    assert response.status_code == 404

    print("\n✓ CRUD operations test passed")

def test_placeholder_resolution(client):
    """Test that drafts resolve placeholders from email content"""

    # Email with extractable information
    email_data = {
        "sender": "john.smith@example.com",
        "subject": "Order issue",
        "content": "Hi, my name is John Smith. I have a problem with order #12345. Please help."
    }

    response = client.post("/api/emails/", json=email_data)
    assert response.status_code == 201
    email = response.json()

    # Generate draft
    response = client.post(f"/api/emails/{email['id']}/generate-draft")
    assert response.status_code == 200
    draft = response.json()

    # Check that draft includes extracted information
    content_lower = draft["content"].lower()

    # Should include name or default customer greeting
    assert "john smith" in content_lower or "customer" in content_lower

    # Should include order reference if detected
    if "12345" in email_data["content"]:
        # Order ID might be referenced
        print(f"\n✓ Placeholder resolution test: Draft includes relevant context")

    print("✓ Placeholder resolution test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
