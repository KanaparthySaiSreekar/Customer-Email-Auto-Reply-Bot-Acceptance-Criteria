from typing import Optional
import uuid

class DraftGenerator:
    """
    Generates auto-reply drafts based on email intent and templates.
    """

    DEFAULT_TEMPLATES = {
        "billing": {
            "subject": "Re: {original_subject} - Case #{case_number}",
            "body": """Dear {customer_name},

Thank you for contacting us regarding your billing inquiry.

We have received your message and created case #{case_number} to track your request.

Next steps:
1. Our billing team will review your account details
2. We will investigate the matter within 1-2 business days
3. You will receive a detailed response with resolution options

If you have any additional information related to {order_reference}your inquiry, please reply to this email with your case number.

Best regards,
Customer Support Team"""
        },
        "support": {
            "subject": "Re: {original_subject} - Case #{case_number}",
            "body": """Dear {customer_name},

Thank you for reaching out to our support team.

We have received your request and created case #{case_number} for tracking purposes.

Next steps:
1. Our support specialists will review your question
2. We will provide detailed guidance within 24 hours
3. If additional information is needed, we will contact you promptly

In the meantime, you may find our knowledge base helpful at [support.example.com].

Thank you for your patience.

Best regards,
Customer Support Team"""
        },
        "bug": {
            "subject": "Re: {original_subject} - Bug Report #{case_number}",
            "body": """Dear {customer_name},

Thank you for reporting this issue to us.

We have logged this as bug report #{case_number} and our technical team has been notified.

Next steps:
1. Our engineering team will investigate the reported issue
2. We will attempt to reproduce the problem in our test environment
3. You will receive updates on the progress and estimated resolution time within 48 hours

Your detailed report helps us improve our product. We appreciate your patience as we work on a solution.

Technical Reference: #{case_number}

Best regards,
Technical Support Team"""
        },
        "feature": {
            "subject": "Re: {original_subject} - Feature Request #{case_number}",
            "body": """Dear {customer_name},

Thank you for your feature suggestion!

We have recorded your request as feature #{case_number} for our product team's review.

Next steps:
1. Our product team will evaluate the suggested feature
2. We will assess feasibility and alignment with our roadmap
3. You will be notified if this feature is scheduled for development

We value customer feedback and continuously work to improve our product based on user needs.

Feature Reference: #{case_number}

Best regards,
Product Team"""
        }
    }

    def generate_case_number(self) -> str:
        """Generate unique case number."""
        return f"CASE-{uuid.uuid4().hex[:12].upper()}"

    def generate_draft(
        self,
        intent: str,
        case_number: str,
        original_subject: str,
        extracted_info: dict,
        custom_template: Optional[dict] = None
    ) -> dict:
        """
        Generate auto-reply draft based on intent and extracted information.

        Args:
            intent: Classified intent (billing/support/bug/feature)
            case_number: Unique case number
            original_subject: Original email subject
            extracted_info: Dictionary with extracted information (name, order_id, etc.)
            custom_template: Optional custom template to use instead of default

        Returns:
            Dictionary with 'subject' and 'content' keys
        """
        # Use custom template if provided, otherwise use default
        template = custom_template or self.DEFAULT_TEMPLATES.get(
            intent,
            self.DEFAULT_TEMPLATES["support"]  # Fallback to support template
        )

        # Prepare placeholders
        placeholders = {
            "case_number": case_number,
            "original_subject": original_subject,
            "customer_name": extracted_info.get("name", "Customer"),
            "order_reference": f"order {extracted_info['order_id']}, " if "order_id" in extracted_info else "",
        }

        # Format subject and body
        subject = template["subject"].format(**placeholders)
        body = template["body"].format(**placeholders)

        return {
            "subject": subject,
            "content": body
        }
