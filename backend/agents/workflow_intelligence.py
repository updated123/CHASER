"""
Workflow Intelligence Engine
Automatically creates and manages workflow items based on case stages
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Case, Client, WorkflowItem, Provider, Meeting


class WorkflowIntelligence:
    """Intelligent workflow management based on annual review process"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_annual_review_workflow(self, case: Case) -> List[WorkflowItem]:
        """Initialize workflow items when annual review case is created"""
        items = []
        
        # Pre-meeting stage items
        pre_meeting_items = [
            {
                'item_type': 'pre_meeting_doc',
                'item_name': 'Expenditure Questionnaire',
                'description': 'Client expenditure details for annual review',
                'required_for': 'pack_prep',
                'workflow_substage': 'pack_prep',
            },
            {
                'item_type': 'questionnaire',
                'item_name': 'ATR (Attitude to Risk) Questionnaire',
                'description': 'Updated risk assessment questionnaire',
                'required_for': 'pack_prep',
                'workflow_substage': 'pack_prep',
            },
            {
                'item_type': 'pack_signoff',
                'item_name': 'Pack Sign-Off',
                'description': 'Adviser/Client Support sign-off on meeting pack',
                'required_for': 'pack_signoff',
                'workflow_substage': 'pack_signoff',
            },
        ]
        
        for item_data in pre_meeting_items:
            item = WorkflowItem(
                case_id=case.id,
                workflow_stage='pre_meeting',
                workflow_substage=item_data['workflow_substage'],
                item_type=item_data['item_type'],
                item_name=item_data['item_name'],
                description=item_data['description'],
                required_for=item_data['required_for'],
                status='pending',
                priority='medium',
                due_date=datetime.utcnow() + timedelta(days=7),  # 7 days for pre-meeting prep
            )
            items.append(item)
            self.db.add(item)
        
        # Update case workflow stage
        case.workflow_stage = 'pre_meeting'
        case.workflow_substage = 'pack_prep'
        
        self.db.commit()
        return items
    
    def advance_to_meeting_stage(self, case: Case, meeting: Meeting) -> List[WorkflowItem]:
        """Create workflow items when meeting is conducted"""
        items = []
        
        # Post-meeting items
        post_meeting_items = [
            {
                'item_type': 'fact_find_update',
                'item_name': 'Fact Find Update',
                'description': 'Update fact find with meeting information',
                'required_for': 'fact_find_update',
                'workflow_substage': 'fact_find_update',
            },
            {
                'item_type': 'meeting_notes',
                'item_name': 'Meeting Notes Review',
                'description': 'Review and confirm meeting notes',
                'required_for': 'meeting_notes',
                'workflow_substage': 'meeting_notes',
            },
        ]
        
        for item_data in post_meeting_items:
            item = WorkflowItem(
                case_id=case.id,
                workflow_stage='meeting',
                workflow_substage=item_data['workflow_substage'],
                item_type=item_data['item_type'],
                item_name=item_data['item_name'],
                description=item_data['description'],
                required_for=item_data['required_for'],
                status='pending',
                priority='high',
                due_date=datetime.utcnow() + timedelta(days=3),  # 3 days after meeting
            )
            items.append(item)
            self.db.add(item)
        
        # Update case workflow stage
        case.workflow_stage = 'meeting'
        case.workflow_substage = 'fact_find_update'
        
        self.db.commit()
        return items
    
    def advance_to_suitability_stage(self, case: Case) -> List[WorkflowItem]:
        """Create workflow items when moving to suitability stage - LOAs are critical here"""
        items = []
        
        # Get client's pension providers
        client = self.db.query(Client).filter_by(id=case.client_id).first()
        if not client:
            return items
        
        # Find providers that need LOAs (based on client portfolios or case context)
        # In real system, this would query portfolios/providers
        providers = self.db.query(Provider).limit(3).all()  # Example: get some providers
        
        # Create LOA items for each provider needed for suitability report
        for provider in providers:
            item = WorkflowItem(
                case_id=case.id,
                workflow_stage='suitability',
                workflow_substage='loa_collection',
                item_type='loa_required',
                item_name=f'LOA for {provider.name}',
                description=f'Letter of Authority required from {provider.name} to obtain pension/investment information for suitability report',
                required_for='suitability_letter',
                status='pending',
                priority='urgent',  # LOAs are urgent at suitability stage
                provider_id=provider.id,
                provider_name=provider.name,
                due_date=datetime.utcnow() + timedelta(days=5),  # 5 days to get LOAs
            )
            items.append(item)
            self.db.add(item)
        
        # Suitability letter item
        suitability_item = WorkflowItem(
            case_id=case.id,
            workflow_stage='suitability',
            workflow_substage='suitability_letter',
            item_type='suitability_letter',
            item_name='Suitability Letter',
            description='Generate suitability letter based on updated fact find and provider information',
            required_for='suitability_letter',
            status='pending',
            priority='high',
            due_date=datetime.utcnow() + timedelta(days=10),  # 10 days after LOAs
        )
        items.append(suitability_item)
        self.db.add(suitability_item)
        
        # Update case workflow stage
        case.workflow_stage = 'suitability'
        case.workflow_substage = 'loa_collection'
        
        self.db.commit()
        return items
    
    def check_and_advance_workflow(self, case: Case) -> Optional[str]:
        """Check if workflow can advance to next stage based on completed items"""
        current_stage = case.workflow_stage
        
        if current_stage == 'pre_meeting':
            # Check if all pre-meeting items are complete
            pre_meeting_items = self.db.query(WorkflowItem).filter_by(
                case_id=case.id,
                workflow_stage='pre_meeting'
            ).all()
            
            if all(item.status == 'received' for item in pre_meeting_items):
                # Check if meeting exists
                recent_meeting = self.db.query(Meeting).filter_by(
                    client_id=case.client_id
                ).order_by(Meeting.meeting_date.desc()).first()
                
                if recent_meeting and recent_meeting.meeting_type == 'annual_review':
                    self.advance_to_meeting_stage(case, recent_meeting)
                    return 'meeting'
        
        elif current_stage == 'meeting':
            # Check if all meeting items are complete
            meeting_items = self.db.query(WorkflowItem).filter_by(
                case_id=case.id,
                workflow_stage='meeting'
            ).all()
            
            if all(item.status == 'received' for item in meeting_items):
                self.advance_to_suitability_stage(case)
                return 'suitability'
        
        elif current_stage == 'suitability':
            # Check if all suitability items (including LOAs) are complete
            suitability_items = self.db.query(WorkflowItem).filter_by(
                case_id=case.id,
                workflow_stage='suitability'
            ).all()
            
            if all(item.status == 'received' for item in suitability_items):
                case.workflow_stage = 'advice_implementation'
                case.workflow_substage = 'implementation'
                self.db.commit()
                return 'advice_implementation'
        
        return None
    
    def get_workflow_status(self, case: Case) -> Dict:
        """Get comprehensive workflow status"""
        workflow_items = self.db.query(WorkflowItem).filter_by(
            case_id=case.id
        ).all()
        
        stage_items = {}
        for item in workflow_items:
            stage = item.workflow_stage
            if stage not in stage_items:
                stage_items[stage] = {
                    'total': 0,
                    'pending': 0,
                    'received': 0,
                    'overdue': 0,
                    'items': []
                }
            
            stage_items[stage]['total'] += 1
            if item.status == 'pending' or item.status == 'requested':
                stage_items[stage]['pending'] += 1
            elif item.status == 'received':
                stage_items[stage]['received'] += 1
            
            if item.due_date and datetime.utcnow() > item.due_date and item.status != 'received':
                stage_items[stage]['overdue'] += 1
            
            stage_items[stage]['items'].append({
                'id': item.id,
                'name': item.item_name,
                'type': item.item_type,
                'status': item.status,
                'priority': item.priority,
            })
        
        return {
            'current_stage': case.workflow_stage,
            'current_substage': case.workflow_substage,
            'stages': stage_items,
            'can_advance': self.check_and_advance_workflow(case) is not None,
        }
    
    def identify_blocking_items(self, case: Case) -> List[WorkflowItem]:
        """Identify items blocking workflow progression"""
        current_stage = case.workflow_stage
        
        # Get pending/overdue items for current stage
        blocking_items = self.db.query(WorkflowItem).filter(
            WorkflowItem.case_id == case.id,
            WorkflowItem.workflow_stage == current_stage,
            WorkflowItem.status.in_(['pending', 'requested', 'overdue'])
        ).all()
        
        return blocking_items

