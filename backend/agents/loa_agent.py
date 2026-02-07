"""
Autonomous agent for managing LOA (Letter of Authority) chasing
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from models import LOA, Case, Client, Provider, ChaseStatus, Priority, CommunicationChannel, Communication
from agents.base_agent import BaseAgent
from models import ChaseType


class LOAAgent(BaseAgent):
    """Autonomous agent specialized in LOA chasing"""
    
    def __init__(self, db: Session, llm_service=None):
        super().__init__(db, llm_service=llm_service)
        self.chase_type = ChaseType.LOA
        self.name = "LOAAgent"
    
    def identify_chases_needed(self) -> List[Dict]:
        """Identify LOAs that need attention"""
        loas = self.db.query(LOA).join(Case).join(Client).join(Provider).filter(
            LOA.status.in_([ChaseStatus.PENDING, ChaseStatus.SENT, ChaseStatus.ACKNOWLEDGED, ChaseStatus.OVERDUE])
        ).all()
        
        items = []
        now = datetime.utcnow()
        
        for loa in loas:
            # Calculate key metrics
            days_since_last_chase = 0
            if loa.last_chased_at:
                days_since_last_chase = (now - loa.last_chased_at).days
            
            days_overdue = 0
            if loa.expected_response_date and now > loa.expected_response_date:
                days_overdue = (now - loa.expected_response_date).days
            
            # Determine if needs chasing
            needs_chase = False
            if loa.status == ChaseStatus.PENDING and not loa.sent_to_client_at:
                needs_chase = True
            elif loa.status == ChaseStatus.SENT and loa.sent_to_client_at:
                # Check if client hasn't returned after reasonable time
                days_since_sent = (now - loa.sent_to_client_at).days
                if days_since_sent > 14:  # 2 weeks
                    needs_chase = True
            elif loa.status == ChaseStatus.ACKNOWLEDGED and loa.sent_to_provider_at:
                # Check if provider is overdue
                if days_overdue > 0:
                    needs_chase = True
                elif days_since_last_chase > 10:  # Chase every 10 days if no response
                    needs_chase = True
            
            if needs_chase or days_overdue > 0:
                items.append({
                    'id': loa.id,
                    'loa': loa,
                    'case_id': loa.case_id,
                    'client_id': loa.case.client_id,
                    'client_name': loa.case.client.name,
                    'client_email': loa.case.client.email,
                    'client_phone': loa.case.client.phone,
                    'client_value_score': loa.case.client.client_value_score,
                    'provider_name': loa.provider.name,
                    'provider_reliability': loa.provider.reliability_score,
                    'status': loa.status,
                    'priority': loa.priority,
                    'chase_count': loa.chase_count,
                    'last_chased_at': loa.last_chased_at,
                    'days_since_last_chase': days_since_last_chase,
                    'days_overdue': days_overdue,
                    'expected_response_date': loa.expected_response_date,
                    'sent_to_client_at': loa.sent_to_client_at,
                    'sent_to_provider_at': loa.sent_to_provider_at,
                })
        
        return items
    
    def calculate_priority(self, item: Dict) -> Priority:
        """Calculate priority based on multiple factors"""
        urgency_score = self.calculate_urgency_score(item)
        
        # Provider reliability affects priority (unreliable providers need more chasing)
        provider_reliability = item.get('provider_reliability', 0.7)
        if provider_reliability < 0.5:
            urgency_score += 0.2
        
        # Days overdue significantly increases priority
        if item.get('days_overdue', 0) > 10:
            return Priority.URGENT
        elif item.get('days_overdue', 0) > 5:
            return Priority.HIGH
        elif urgency_score > 0.7:
            return Priority.HIGH
        elif urgency_score > 0.4:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def should_chase(self, item: Dict) -> bool:
        """Determine if LOA should be chased now"""
        status = item.get('status')
        days_since_last_chase = item.get('days_since_last_chase', 0)
        days_overdue = item.get('days_overdue', 0)
        chase_count = item.get('chase_count', 0)
        
        # Always chase if overdue
        if days_overdue > 0:
            return True
        
        # Don't chase too frequently (respectful of client/provider time)
        if days_since_last_chase < 3:
            return False
        
        # Status-based logic
        if status == ChaseStatus.PENDING:
            # Initial send to client
            return True
        elif status == ChaseStatus.SENT:
            # Client hasn't returned - chase after 14 days
            if days_since_last_chase >= 14:
                return True
        elif status == ChaseStatus.ACKNOWLEDGED:
            # Provider has it - chase if overdue or every 10 days
            if days_overdue > 0 or days_since_last_chase >= 10:
                return True
        
        return False
    
    def generate_communication(self, item: Dict) -> Dict:
        """Generate context-aware communication for LOA chasing"""
        # Use LLM if available for more natural communication
        if self.llm_service:
            item_context = {
                'client_name': item.get('client_name', 'Unknown'),
                'engagement_level': item.get('engagement_level', 'medium'),
                'preferred_contact': item.get('client_preferred_contact', 'email'),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
                'item_type': 'LOA',
                'item_details': f"LOA for {item.get('provider_name', 'provider')}",
            }
            try:
                return self.llm_service.generate_communication(item_context, 'loa', item.get('chase_count', 0))
            except Exception as e:
                # Fall through to template-based generation
                pass
        
        # Fallback to template-based generation
        status = item.get('status')
        client_name = item.get('client_name')
        provider_name = item.get('provider_name')
        days_overdue = item.get('days_overdue', 0)
        chase_count = item.get('chase_count', 0)
        
        if status == ChaseStatus.PENDING:
            # Initial request to client
            subject = f"Letter of Authority Required - {provider_name}"
            content = f"""Hi {client_name.split()[0]},

To proceed with your financial advice case, we need a signed Letter of Authority (LOA) to obtain information from {provider_name}.

This is a standard document that allows us to request your pension/investment details on your behalf.

I've attached the LOA form - please sign and return it at your earliest convenience. If you have any questions, please don't hesitate to reach out.

Best regards,
Your Financial Advisor"""
        
        elif status == ChaseStatus.SENT:
            # Follow-up with client who hasn't returned
            tone = "friendly" if chase_count < 2 else "gentle_reminder"
            if tone == "friendly":
                subject = f"Gentle Reminder: LOA for {provider_name}"
                content = f"""Hi {client_name.split()[0]},

Just checking in on the Letter of Authority for {provider_name} that we sent a couple of weeks ago.

We're ready to move forward with your case once we have the signed LOA. If you've already sent it, please let me know and I'll check our records.

If you need another copy or have any questions, I'm here to help.

Best regards"""
            else:
                subject = f"Important: LOA Required to Progress Your Case"
                content = f"""Hi {client_name.split()[0]},

We're still waiting on the signed Letter of Authority for {provider_name} to proceed with your case.

This is the final step needed before we can obtain your pension/investment information and provide our recommendations.

Could you please prioritize signing and returning the LOA? I've attached another copy for your convenience.

Thank you for your attention to this.

Best regards"""
        
        elif status == ChaseStatus.ACKNOWLEDGED:
            # Chasing provider (this would be internal note or call reminder)
            if days_overdue > 0:
                subject = f"URGENT: Follow-up Required - {provider_name} LOA Response Overdue"
                content = f"""INTERNAL NOTE:

LOA sent to {provider_name} for {client_name} is now {days_overdue} days overdue.

Expected response: {item.get('expected_response_date').strftime('%d %b %Y') if item.get('expected_response_date') else 'N/A'}
Chase count: {chase_count}

ACTION REQUIRED: Phone call recommended. Provider contact: {item.get('provider_phone', 'N/A')}

Client is waiting for this information to proceed with their case."""
            else:
                subject = f"Follow-up: {provider_name} LOA Status Check"
                content = f"""INTERNAL NOTE:

Time to follow up with {provider_name} regarding LOA for {client_name}.

Expected response date: {item.get('expected_response_date').strftime('%d %b %Y') if item.get('expected_response_date') else 'N/A'}
Days since last chase: {item.get('days_since_last_chase')}

Consider: Phone call or email to provider to check status."""
        
        else:
            subject = "LOA Status Update"
            content = f"Status update for {client_name}'s LOA with {provider_name}."
        
        return {
            'subject': subject,
            'content': content,
            'tone': 'professional'
        }
    
    def select_channel(self, item: Dict) -> CommunicationChannel:
        """Select appropriate communication channel"""
        # Use LLM if available for intelligent channel selection
        if self.llm_service:
            item_context = {
                'client_name': item.get('client_name', 'Unknown'),
                'engagement_level': item.get('engagement_level', 'medium'),
                'preferred_contact': item.get('client_preferred_contact', 'email'),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
                'priority': item.get('priority', 'medium'),
                'item_type': 'LOA',
                'status': item.get('status', 'pending'),
            }
            try:
                channel_name = self.llm_service.select_communication_channel(item_context, 'loa')
                if channel_name == 'sms':
                    return CommunicationChannel.SMS
                elif channel_name == 'phone':
                    return CommunicationChannel.PHONE
                return CommunicationChannel.EMAIL
            except Exception as e:
                # Fall through to rule-based selection
                pass
        
        # Fallback to rule-based selection
        status = item.get('status')
        chase_count = item.get('chase_count', 0)
        client_preference = item.get('client_preferred_contact', 'email')
        
        if status == ChaseStatus.ACKNOWLEDGED:
            # Provider chasing - prefer email for audit trail, but escalate to phone if urgent
            if item.get('days_overdue', 0) > 10:
                return CommunicationChannel.PHONE
            return CommunicationChannel.EMAIL
        
        # Client communication
        if chase_count >= 2:
            # Multiple chases - try SMS for urgency
            return CommunicationChannel.SMS
        elif client_preference == 'sms':
            return CommunicationChannel.SMS
        else:
            return CommunicationChannel.EMAIL

