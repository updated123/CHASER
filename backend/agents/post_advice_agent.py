"""
Autonomous agent for managing post-advice document chasing
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from models import PostAdviceItem, Case, Client, ChaseStatus, Priority, CommunicationChannel
from agents.base_agent import BaseAgent
from models import ChaseType


class PostAdviceAgent(BaseAgent):
    """Autonomous agent specialized in post-advice document chasing"""
    
    def __init__(self, db: Session, llm_service=None):
        super().__init__(db, llm_service=llm_service)
        self.chase_type = ChaseType.POST_ADVICE
        self.name = "PostAdviceAgent"
    
    def identify_chases_needed(self) -> List[Dict]:
        """Identify post-advice items that need chasing"""
        items_query = self.db.query(PostAdviceItem).join(Case).join(Client).filter(
            PostAdviceItem.status.in_([ChaseStatus.PENDING, ChaseStatus.SENT, ChaseStatus.OVERDUE])
        ).all()
        
        items = []
        now = datetime.utcnow()
        
        for item in items_query:
            days_since_last_chase = 0
            if item.last_chased_at:
                days_since_last_chase = (now - item.last_chased_at).days
            
            days_since_request = (now - item.requested_at).days if item.requested_at else 0
            
            needs_chase = False
            if item.status == ChaseStatus.PENDING:
                if not item.last_chased_at or days_since_last_chase >= 5:
                    needs_chase = True
            elif item.status == ChaseStatus.SENT:
                if days_since_last_chase >= 4:
                    needs_chase = True
            
            if needs_chase or days_since_request > 10:
                items.append({
                    'id': item.id,
                    'item': item,
                    'case_id': item.case_id,
                    'client_id': item.case.client_id,
                    'client_name': item.case.client.name,
                    'client_email': item.case.client.email,
                    'client_phone': item.case.client.phone,
                    'client_value_score': item.case.client.client_value_score,
                    'client_preferred_contact': item.case.client.preferred_contact,
                    'item_type': item.item_type,
                    'status': item.status,
                    'priority': item.priority,
                    'chase_count': item.chase_count,
                    'last_chased_at': item.last_chased_at,
                    'days_since_last_chase': days_since_last_chase,
                    'days_since_request': days_since_request,
                    'days_overdue': max(0, days_since_request - 10),
                })
        
        return items
    
    def calculate_priority(self, item: Dict) -> Priority:
        """Calculate priority for post-advice item"""
        urgency_score = self.calculate_urgency_score(item)
        days_since_request = item.get('days_since_request', 0)
        item_type = item.get('item_type')
        
        # Signed applications are critical - can't proceed without them
        if item_type == 'signed_application':
            urgency_score += 0.25
        
        if days_since_request > 14:
            return Priority.URGENT
        elif days_since_request > 10:
            return Priority.HIGH
        elif urgency_score > 0.65:
            return Priority.HIGH
        elif urgency_score > 0.35:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def should_chase(self, item: Dict) -> bool:
        """Determine if post-advice item should be chased"""
        days_since_last_chase = item.get('days_since_last_chase', 0)
        days_since_request = item.get('days_since_request', 0)
        status = item.get('status')
        
        if days_since_last_chase < 2:
            return False
        
        if days_since_request > 10:
            return True
        
        if status == ChaseStatus.PENDING and days_since_last_chase >= 5:
            return True
        elif status == ChaseStatus.SENT and days_since_last_chase >= 4:
            return True
        
        return False
    
    def generate_communication(self, item: Dict) -> Dict:
        """Generate communication for post-advice item"""
        client_name = item.get('client_name')
        item_type = item.get('item_type')
        chase_count = item.get('chase_count', 0)
        days_since_request = item.get('days_since_request', 0)
        
        item_names = {
            'signed_application': 'signed application form',
            'risk_questionnaire': 'risk questionnaire',
            'authority_to_proceed': 'authority to proceed confirmation',
            'aml_verification': 'AML verification documents',
            'annual_review_response': 'annual review response',
        }
        item_display = item_names.get(item_type, item_type.replace('_', ' '))
        
        if chase_count == 0:
            subject = f"Action Required: {item_display.title()}"
            content = f"""Hi {client_name.split()[0]},

Following our recent advice discussion, we need your {item_display} to proceed with implementing the recommendations.

This is the final step to get everything moving. Please complete and return at your earliest convenience.

If you have any questions, please don't hesitate to reach out.

Best regards"""
        elif chase_count == 1:
            subject = f"Reminder: {item_display.title()}"
            content = f"""Hi {client_name.split()[0]},

Just a quick reminder that we're still waiting for your {item_display} to proceed with implementing your financial plan.

If you've already sent it, please let me know. If you need help or have questions, I'm here to assist.

Best regards"""
        else:
            subject = f"Urgent: {item_display.title()} Required"
            content = f"""Hi {client_name.split()[0]},

We're still waiting for your {item_display} which we requested {days_since_request} days ago. This is needed to proceed with your financial plan.

Could you please prioritize completing and returning this? If there are any issues or questions, please let me know immediately so we can resolve them.

Thank you for your attention to this.

Best regards"""
        
        return {
            'subject': subject,
            'content': content,
            'tone': 'professional'
        }
    
    def select_channel(self, item: Dict) -> CommunicationChannel:
        """Select communication channel"""
        chase_count = item.get('chase_count', 0)
        item_type = item.get('item_type')
        client_preference = item.get('client_preferred_contact', 'email')
        
        # Signed applications are critical - use SMS after first chase
        if item_type == 'signed_application' and chase_count >= 1:
            return CommunicationChannel.SMS
        elif chase_count >= 2:
            return CommunicationChannel.SMS
        elif client_preference == 'sms':
            return CommunicationChannel.SMS
        else:
            return CommunicationChannel.EMAIL

