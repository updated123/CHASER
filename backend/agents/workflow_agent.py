"""
Workflow-Aware Agent for Annual Review Process
Handles chasing at different workflow stages based on the client journey
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from models import (
    Case, Client, WorkflowItem, Provider, ChaseStatus, Priority, 
    CommunicationChannel, Communication
)
from agents.base_agent import BaseAgent
from models import ChaseType


class WorkflowAgent(BaseAgent):
    """Agent specialized in workflow-aware chasing for annual reviews"""
    
    def __init__(self, db: Session, llm_service=None):
        super().__init__(db, llm_service=llm_service)
        self.chase_type = ChaseType.WORKFLOW_ITEM
        self.name = "WorkflowAgent"
        
        # Workflow stage definitions
        self.stage_priorities = {
            'pre_meeting': {
                'pack_prep': 'high',
                'pack_signoff': 'urgent',
                'client_responses': 'high',
            },
            'meeting': {
                'fact_find_update': 'high',
                'meeting_notes': 'medium',
            },
            'suitability': {
                'loa_collection': 'urgent',  # Critical - LOAs needed for suitability letter
                'suitability_letter': 'high',
            },
            'advice_implementation': {
                'implementation_docs': 'high',
            }
        }
    
    def identify_chases_needed(self) -> List[Dict]:
        """Identify workflow items needing attention based on workflow stage"""
        # Get all annual review cases in progress
        annual_review_cases = self.db.query(Case).filter(
            Case.case_type == 'annual_review',
            Case.status.in_(['in_progress', 'pending', 'awaiting_documents'])
        ).all()
        
        items = []
        now = datetime.utcnow()
        
        for case in annual_review_cases:
            client = self.db.query(Client).filter_by(id=case.client_id).first()
            if not client:
                continue
            
            # Get workflow items for this case
            workflow_items = self.db.query(WorkflowItem).filter(
                WorkflowItem.case_id == case.id,
                WorkflowItem.status.in_(['pending', 'requested', 'overdue'])
            ).all()
            
            for item in workflow_items:
                # Calculate metrics
                days_since_request = 0
                if item.requested_at:
                    days_since_request = (now - item.requested_at).days
                
                days_since_last_chase = 0
                if item.last_chased_at:
                    days_since_last_chase = (now - item.last_chased_at).days
                
                days_overdue = 0
                if item.due_date and now > item.due_date:
                    days_overdue = (now - item.due_date).days
                
                # Determine if needs chase based on workflow stage
                needs_chase = self._should_chase_for_stage(
                    item, case, days_since_request, days_since_last_chase, days_overdue
                )
                
                if needs_chase:
                    provider_name = None
                    if item.provider_id:
                        provider = self.db.query(Provider).filter_by(id=item.provider_id).first()
                        provider_name = provider.name if provider else item.provider_name
                    
                    items.append({
                        'id': item.id,
                        'client_id': client.id,
                        'client_name': client.name,
                        'case_id': case.id,
                        'case_type': case.case_type,
                        'workflow_stage': item.workflow_stage,
                        'workflow_substage': item.workflow_substage,
                        'item_type': item.item_type,
                        'item_name': item.item_name,
                        'description': item.description,
                        'required_for': item.required_for,
                        'status': item.status,
                        'priority': item.priority,
                        'chase_count': item.chase_count,
                        'days_since_request': days_since_request,
                        'days_since_last_chase': days_since_last_chase,
                        'days_overdue': days_overdue,
                        'last_chased_at': item.last_chased_at,
                        'due_date': item.due_date,
                        'provider_name': provider_name,
                        'provider_id': item.provider_id,
                        'client_value_score': client.client_value_score,
                        'engagement_level': client.engagement_level,
                        'client_preferred_contact': client.preferred_contact,
                    })
        
        return items
    
    def _should_chase_for_stage(self, item: WorkflowItem, case: Case, 
                                 days_since_request: int, days_since_last_chase: int, 
                                 days_overdue: int) -> bool:
        """Determine if item should be chased based on workflow stage"""
        stage = item.workflow_stage
        substage = item.workflow_substage
        
        # Suitability stage - LOAs are critical
        if stage == 'suitability' and item.item_type == 'loa_required':
            # LOAs needed urgently for suitability letter
            if days_since_request >= 3:  # Start chasing after 3 days
                return True
            if days_overdue > 0:
                return True
            if days_since_last_chase >= 5:
                return True
        
        # Pre-meeting pack signoff - urgent
        if stage == 'pre_meeting' and substage == 'pack_signoff':
            if days_since_request >= 2:
                return True
            if days_overdue > 0:
                return True
        
        # Pre-meeting client responses
        if stage == 'pre_meeting' and substage == 'client_responses':
            if days_since_request >= 5:
                return True
            if days_since_last_chase >= 3:
                return True
        
        # Post-meeting fact find updates
        if stage == 'meeting' and substage == 'fact_find_update':
            if days_since_request >= 3:
                return True
            if days_since_last_chase >= 2:
                return True
        
        # General rules
        if days_overdue > 0:
            return True
        if days_since_last_chase >= 7:
            return True
        
        return False
    
    def calculate_priority(self, item: Dict) -> Priority:
        """Calculate priority based on workflow stage and context"""
        stage = item.get('workflow_stage')
        substage = item.get('workflow_substage')
        item_type = item.get('item_type')
        days_overdue = item.get('days_overdue', 0)
        
        # Use LLM if available for intelligent priority
        if self.llm_service:
            item_context = {
                'workflow_stage': stage,
                'workflow_substage': substage,
                'item_type': item_type,
                'item_name': item.get('item_name'),
                'days_overdue': days_overdue,
                'required_for': item.get('required_for'),
            }
            try:
                analysis = self.llm_service.analyze_priority(item_context, 'workflow_item')
                priority_str = analysis.get('priority', 'medium')
                return Priority[priority_str.upper()] if hasattr(Priority, priority_str.upper()) else Priority.MEDIUM
            except:
                pass
        
        # Rule-based priority
        # Suitability stage LOAs are urgent
        if stage == 'suitability' and item_type == 'loa_required':
            if days_overdue > 0:
                return Priority.URGENT
            return Priority.HIGH
        
        # Pack signoff is urgent
        if substage == 'pack_signoff':
            return Priority.URGENT
        
        # Overdue items are high priority
        if days_overdue > 0:
            return Priority.HIGH
        
        # Check stage-specific priorities
        if stage in self.stage_priorities:
            if substage in self.stage_priorities[stage]:
                priority_str = self.stage_priorities[stage][substage]
                return Priority[priority_str.upper()]
        
        return Priority.MEDIUM
    
    def should_chase(self, item: Dict) -> bool:
        """Determine if should chase now"""
        # Use LLM if available
        if self.llm_service:
            item_context = {
                'workflow_stage': item.get('workflow_stage'),
                'workflow_substage': item.get('workflow_substage'),
                'item_type': item.get('item_type'),
                'days_since_last_chase': item.get('days_since_last_chase', 0),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
            }
            try:
                decision = self.llm_service.should_chase_now(item_context, 'workflow_item')
                return decision.get('should_chase', False)
            except:
                pass
        
        # Rule-based decision
        return self._should_chase_for_stage(
            None, None,
            item.get('days_since_request', 0),
            item.get('days_since_last_chase', 0),
            item.get('days_overdue', 0)
        )
    
    def generate_communication(self, item: Dict) -> Dict:
        """Generate context-aware communication based on workflow stage"""
        # Use LLM if available
        if self.llm_service:
            item_context = {
                'client_name': item.get('client_name', 'Unknown'),
                'workflow_stage': item.get('workflow_stage'),
                'workflow_substage': item.get('workflow_substage'),
                'item_name': item.get('item_name'),
                'item_type': item.get('item_type'),
                'required_for': item.get('required_for'),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
            }
            try:
                return self.llm_service.generate_communication(
                    item_context, 'workflow_item', item.get('chase_count', 0)
                )
            except:
                pass
        
        # Fallback to template-based generation
        client_name = item.get('client_name', 'Client')
        first_name = client_name.split()[0] if client_name else 'Client'
        stage = item.get('workflow_stage')
        substage = item.get('workflow_substage')
        item_name = item.get('item_name', 'item')
        item_type = item.get('item_type')
        chase_count = item.get('chase_count', 0)
        days_overdue = item.get('days_overdue', 0)
        
        # Stage-specific messaging
        if stage == 'pre_meeting':
            if substage == 'pack_signoff':
                subject = f"Urgent: Pack Sign-Off Required for Annual Review"
                content = f"""Hi {first_name},

We're preparing your annual review meeting pack and need your sign-off to proceed.

This is required before we can send the pack to you. Please review and sign off at your earliest convenience.

Best regards"""
            elif substage == 'client_responses':
                subject = f"Annual Review: {item_name} Required"
                content = f"""Hi {first_name},

As part of your upcoming annual review meeting, we need your {item_name.lower()}.

This helps us prepare properly for our meeting. Please complete and return at your earliest convenience.

Best regards"""
            else:
                subject = f"Annual Review: {item_name} Required"
                content = f"""Hi {first_name},

We're preparing for your annual review meeting and need {item_name.lower()}.

Please provide this at your earliest convenience.

Best regards"""
        
        elif stage == 'meeting':
            if substage == 'fact_find_update':
                subject = f"Post-Meeting: Fact Find Update Required"
                content = f"""Hi {first_name},

Following our annual review meeting, we need to update your fact find with the latest information.

Please review and confirm any changes to your circumstances, financial situation, or objectives.

Best regards"""
        
        elif stage == 'suitability':
            if item_type == 'loa_required':
                provider_name = item.get('provider_name', 'your pension provider')
                subject = f"Urgent: Letter of Authority Required for Suitability Report"
                content = f"""Hi {first_name},

To complete your suitability report, we need a Letter of Authority (LOA) for {provider_name}.

This is required to obtain your current pension/investment information. Please sign and return the attached LOA form as soon as possible.

Without this, we cannot complete your suitability report.

Best regards"""
            else:
                subject = f"Suitability Report: {item_name} Required"
                content = f"""Hi {first_name},

To complete your suitability report, we need {item_name.lower()}.

Please provide this at your earliest convenience.

Best regards"""
        
        else:
            subject = f"Action Required: {item_name}"
            content = f"""Hi {first_name},

We need {item_name.lower()} to proceed with your case.

Please provide this at your earliest convenience.

Best regards"""
        
        # Escalate tone if overdue or multiple chases
        if days_overdue > 0 or chase_count > 1:
            content += "\n\nThis is urgent as it's blocking progress on your case."
        
        return {
            'subject': subject,
            'content': content,
            'tone': 'professional' if chase_count == 0 else 'urgent'
        }
    
    def select_channel(self, item: Dict) -> CommunicationChannel:
        """Select communication channel based on workflow stage and urgency"""
        # Use LLM if available
        if self.llm_service:
            item_context = {
                'workflow_stage': item.get('workflow_stage'),
                'workflow_substage': item.get('workflow_substage'),
                'item_type': item.get('item_type'),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
                'preferred_contact': item.get('client_preferred_contact', 'email'),
            }
            try:
                channel_name = self.llm_service.select_communication_channel(item_context, 'workflow_item')
                if channel_name == 'sms':
                    return CommunicationChannel.SMS
                elif channel_name == 'phone':
                    return CommunicationChannel.PHONE
                return CommunicationChannel.EMAIL
            except:
                pass
        
        # Rule-based selection
        stage = item.get('workflow_stage')
        substage = item.get('workflow_substage')
        days_overdue = item.get('days_overdue', 0)
        chase_count = item.get('chase_count', 0)
        
        # Urgent items (pack signoff, suitability LOAs) get SMS after first chase
        if (substage == 'pack_signoff' or 
            (stage == 'suitability' and item.get('item_type') == 'loa_required')):
            if chase_count >= 1:
                return CommunicationChannel.SMS
        
        # Overdue items get SMS
        if days_overdue > 3:
            return CommunicationChannel.SMS
        
        # Multiple chases get SMS
        if chase_count >= 2:
            return CommunicationChannel.SMS
        
        # Default to email
        preferred = item.get('client_preferred_contact', 'email')
        if preferred == 'sms':
            return CommunicationChannel.SMS
        return CommunicationChannel.EMAIL

