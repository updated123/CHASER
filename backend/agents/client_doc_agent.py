"""
Autonomous agent for managing client document chasing
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from models import DocumentRequest, Case, Client, ChaseStatus, Priority, CommunicationChannel
from agents.base_agent import BaseAgent
from models import ChaseType


class ClientDocAgent(BaseAgent):
    """Autonomous agent specialized in client document chasing"""
    
    def __init__(self, db: Session, llm_service=None):
        super().__init__(db, llm_service=llm_service)
        self.chase_type = ChaseType.CLIENT_DOCUMENT
        self.name = "ClientDocAgent"
    
    def identify_chases_needed(self) -> List[Dict]:
        """Identify document requests that need chasing"""
        requests = self.db.query(DocumentRequest).join(Case).join(Client).filter(
            DocumentRequest.status.in_([ChaseStatus.PENDING, ChaseStatus.SENT, ChaseStatus.OVERDUE])
        ).all()
        
        items = []
        now = datetime.utcnow()
        
        for req in requests:
            days_since_last_chase = 0
            if req.last_chased_at:
                days_since_last_chase = (now - req.last_chased_at).days
            
            days_since_request = (now - req.requested_at).days if req.requested_at else 0
            
            # Needs chasing if requested but not received
            needs_chase = False
            if req.status == ChaseStatus.PENDING:
                # Initial request or follow-up needed
                if not req.last_chased_at or days_since_last_chase >= 7:
                    needs_chase = True
            elif req.status == ChaseStatus.SENT:
                # Client acknowledged but hasn't sent
                if days_since_last_chase >= 5:
                    needs_chase = True
            
            if needs_chase or days_since_request > 14:
                items.append({
                    'id': req.id,
                    'request': req,
                    'case_id': req.case_id,
                    'client_id': req.case.client_id,
                    'client_name': req.case.client.name,
                    'client_email': req.case.client.email,
                    'client_phone': req.case.client.phone,
                    'client_value_score': req.case.client.client_value_score,
                    'client_preferred_contact': req.case.client.preferred_contact,
                    'document_type': req.document_type,
                    'status': req.status,
                    'priority': req.priority,
                    'chase_count': req.chase_count,
                    'last_chased_at': req.last_chased_at,
                    'days_since_last_chase': days_since_last_chase,
                    'days_since_request': days_since_request,
                    'days_overdue': max(0, days_since_request - 14),
                })
        
        return items
    
    def calculate_priority(self, item: Dict) -> Priority:
        """Calculate priority for document request"""
        urgency_score = self.calculate_urgency_score(item)
        days_since_request = item.get('days_since_request', 0)
        
        # Critical documents (like ID) are higher priority
        critical_docs = ['passport', 'driving_licence', 'proof_of_identity']
        if item.get('document_type') in critical_docs:
            urgency_score += 0.2
        
        if days_since_request > 21:  # 3 weeks
            return Priority.URGENT
        elif days_since_request > 14:  # 2 weeks
            return Priority.HIGH
        elif urgency_score > 0.6:
            return Priority.HIGH
        elif urgency_score > 0.3:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def should_chase(self, item: Dict) -> bool:
        """Determine if document should be chased"""
        days_since_last_chase = item.get('days_since_last_chase', 0)
        days_since_request = item.get('days_since_request', 0)
        status = item.get('status')
        
        # Don't chase too frequently
        if days_since_last_chase < 3:
            return False
        
        # Chase if overdue
        if days_since_request > 14:
            return True
        
        # Chase based on status
        if status == ChaseStatus.PENDING and days_since_last_chase >= 7:
            return True
        elif status == ChaseStatus.SENT and days_since_last_chase >= 5:
            return True
        
        return False
    
    def generate_communication(self, item: Dict) -> Dict:
        """Generate communication for document request"""
        client_name = item.get('client_name')
        doc_type = item.get('document_type')
        chase_count = item.get('chase_count', 0)
        days_since_request = item.get('days_since_request', 0)
        
        # Humanize document type names
        doc_names = {
            'passport': 'passport',
            'driving_licence': 'driving licence',
            'proof_of_identity': 'proof of identity',
            'proof_of_address': 'proof of address',
            'payslip': 'payslip',
            'p60': 'P60',
            'pension_statement': 'pension statement',
            'investment_valuation': 'investment valuation',
        }
        doc_display = doc_names.get(doc_type, doc_type.replace('_', ' '))
        
        if chase_count == 0:
            # Initial request
            subject = f"Document Request: {doc_display.title()}"
            content = f"""Hi {client_name.split()[0]},

To complete your financial review, we need a copy of your {doc_display}.

You can send this via email (scanned or photo is fine) or post. If you have any questions about what we need, please let me know.

Thank you for your help in moving your case forward.

Best regards"""
        elif chase_count == 1:
            # First follow-up
            subject = f"Gentle Reminder: {doc_display.title()} Request"
            content = f"""Hi {client_name.split()[0]},

Just a friendly reminder that we're still waiting for your {doc_display} to proceed with your financial review.

If you've already sent it, please let me know and I'll check our records. If you need help locating the document or have any questions, I'm here to help.

Best regards"""
        else:
            # Multiple chases - more direct
            subject = f"Important: {doc_display.title()} Required"
            content = f"""Hi {client_name.split()[0]},

We're still waiting for your {doc_display} which is needed to complete your financial review. We requested this {days_since_request} days ago.

This is the final document we need to provide your recommendations. Could you please send it at your earliest convenience?

If you're having trouble locating it or have questions, please let me know and I can help.

Thank you for your attention to this.

Best regards"""
        
        return {
            'subject': subject,
            'content': content,
            'tone': 'friendly' if chase_count < 2 else 'professional'
        }
    
    def select_channel(self, item: Dict) -> CommunicationChannel:
        """Select communication channel for document request"""
        chase_count = item.get('chase_count', 0)
        client_preference = item.get('client_preferred_contact', 'email')
        
        # After multiple chases, try SMS for visibility
        if chase_count >= 2:
            return CommunicationChannel.SMS
        elif client_preference == 'sms':
            return CommunicationChannel.SMS
        else:
            return CommunicationChannel.EMAIL

