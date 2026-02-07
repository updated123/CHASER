"""
Chasing Engine - Autonomous identification and prioritization of chase items
Core functionality for the Agentic Chaser system
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from agents.insights_mock import InsightsMock

logger = logging.getLogger(__name__)


class ChasingEngine:
    """Engine for autonomous chasing of LOAs, documents, and post-advice items"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def identify_loas_needing_chase(
        self, 
        priority: Optional[str] = None,
        days_overdue: Optional[int] = None,
        provider_name: Optional[str] = None
    ) -> List[Dict]:
        """Identify LOAs that need chasing"""
        logger.info(f"[Chasing] Identifying LOAs needing chase (priority={priority}, days_overdue={days_overdue})")
        
        # Mock data representing realistic LOA scenarios
        loas = [
            {
                'loa_id': 1,
                'case_id': 101,
                'client_name': 'John Smith',
                'provider_name': 'Aviva',
                'provider_id': 1,
                'status': 'sent_to_provider',
                'sent_to_provider_at': (datetime.utcnow() - timedelta(days=25)).isoformat(),
                'expected_response_date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'days_overdue': 5,
                'chase_count': 1,
                'last_chased_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'priority': 'high',
                'case_type': 'pension_consolidation',
                'client_value_score': 8.5,
                'is_stuck': True,
                'recommended_action': 'phone_call',
                'reason': 'Overdue by 5 days, high-value client, first chase sent 3 days ago'
            },
            {
                'loa_id': 2,
                'case_id': 102,
                'client_name': 'Sarah Johnson',
                'provider_name': 'Legal & General',
                'provider_id': 2,
                'status': 'sent_to_provider',
                'sent_to_provider_at': (datetime.utcnow() - timedelta(days=18)).isoformat(),
                'expected_response_date': (datetime.utcnow() + timedelta(days=2)).isoformat(),
                'days_overdue': 0,
                'chase_count': 0,
                'last_chased_at': None,
                'priority': 'medium',
                'case_type': 'pension_consolidation',
                'client_value_score': 7.2,
                'is_stuck': False,
                'recommended_action': 'monitor',
                'reason': 'Within expected timeframe, but approaching due date'
            },
            {
                'loa_id': 3,
                'case_id': 103,
                'client_name': 'Michael Brown',
                'provider_name': 'Standard Life',
                'provider_id': 3,
                'status': 'sent_to_provider',
                'sent_to_provider_at': (datetime.utcnow() - timedelta(days=35)).isoformat(),
                'expected_response_date': (datetime.utcnow() - timedelta(days=15)).isoformat(),
                'days_overdue': 15,
                'chase_count': 2,
                'last_chased_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'priority': 'urgent',
                'case_type': 'pension_transfer',
                'client_value_score': 9.1,
                'is_stuck': True,
                'recommended_action': 'escalate',
                'reason': 'Severely overdue, multiple chases sent, high-value client - needs escalation'
            },
            {
                'loa_id': 4,
                'case_id': 104,
                'client_name': 'Emily Davis',
                'provider_name': 'Prudential',
                'provider_id': 4,
                'status': 'awaiting_client_signature',
                'sent_to_client_at': (datetime.utcnow() - timedelta(days=10)).isoformat(),
                'expected_response_date': None,
                'days_overdue': None,
                'chase_count': 1,
                'last_chased_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'priority': 'high',
                'case_type': 'pension_consolidation',
                'client_value_score': 6.8,
                'is_stuck': False,
                'recommended_action': 'email',
                'reason': 'Awaiting client signature, first reminder sent 3 days ago'
            }
        ]
        
        # Apply filters
        if priority:
            loas = [l for l in loas if l['priority'] == priority]
        if days_overdue is not None:
            loas = [l for l in loas if l.get('days_overdue', 0) >= days_overdue]
        if provider_name:
            loas = [l for l in loas if provider_name.lower() in l['provider_name'].lower()]
        
        return sorted(loas, key=lambda x: (
            {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('priority', 'medium'), 2),
            -(x.get('days_overdue') if x.get('days_overdue') is not None else 0),
            -(x.get('client_value_score') if x.get('client_value_score') is not None else 0)
        ))
    
    def identify_documents_needing_chase(
        self,
        document_type: Optional[str] = None,
        days_waiting: Optional[int] = None,
        client_name: Optional[str] = None
    ) -> List[Dict]:
        """Identify client documents that need chasing"""
        logger.info(f"[Chasing] Identifying documents needing chase (type={document_type}, days_waiting={days_waiting})")
        
        documents = [
            {
                'document_id': 1,
                'case_id': 201,
                'client_name': 'David Wilson',
                'document_type': 'pension_statement',
                'requested_at': (datetime.utcnow() - timedelta(days=14)).isoformat(),
                'days_waiting': 14,
                'chase_count': 2,
                'last_chased_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'priority': 'high',
                'is_blocking': True,
                'case_type': 'pension_consolidation',
                'client_value_score': 7.5,
                'recommended_action': 'phone_call',
                'reason': 'Blocking case progression, multiple chases sent, approaching critical delay'
            },
            {
                'document_id': 2,
                'case_id': 202,
                'client_name': 'Lisa Anderson',
                'document_type': 'passport',
                'requested_at': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                'days_waiting': 7,
                'chase_count': 1,
                'last_chased_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'priority': 'medium',
                'is_blocking': True,
                'case_type': 'investment_advice',
                'client_value_score': 6.2,
                'recommended_action': 'sms',
                'reason': 'AML verification required, first reminder sent'
            },
            {
                'document_id': 3,
                'case_id': 203,
                'client_name': 'Robert Taylor',
                'document_type': 'p60',
                'requested_at': (datetime.utcnow() - timedelta(days=21)).isoformat(),
                'days_waiting': 21,
                'chase_count': 3,
                'last_chased_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'priority': 'urgent',
                'is_blocking': True,
                'case_type': 'tax_planning',
                'client_value_score': 8.9,
                'recommended_action': 'phone_call',
                'reason': 'Severely overdue, multiple chases, high-value client, tax deadline approaching'
            },
            {
                'document_id': 4,
                'case_id': 204,
                'client_name': 'Jennifer Martinez',
                'document_type': 'investment_valuation',
                'requested_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'days_waiting': 5,
                'chase_count': 0,
                'last_chased_at': None,
                'priority': 'low',
                'is_blocking': False,
                'case_type': 'annual_review',
                'client_value_score': 5.5,
                'recommended_action': 'email',
                'reason': 'Recently requested, within acceptable timeframe'
            }
        ]
        
        # Apply filters
        if document_type:
            documents = [d for d in documents if document_type.lower() in d['document_type'].lower()]
        if days_waiting is not None:
            documents = [d for d in documents if d['days_waiting'] >= days_waiting]
        if client_name:
            documents = [d for d in documents if client_name.lower() in d['client_name'].lower()]
        
        return sorted(documents, key=lambda x: (
            {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['priority'], 2),
            -x.get('days_waiting', 0),
            -(x.get('client_value_score') or 0)
        ))
    
    def identify_post_advice_items_needing_chase(
        self,
        item_type: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """Identify post-advice items that need chasing"""
        logger.info(f"[Chasing] Identifying post-advice items needing chase (type={item_type}, priority={priority})")
        
        items = [
            {
                'item_id': 1,
                'case_id': 301,
                'client_name': 'James Wilson',
                'item_type': 'signed_application',
                'requested_at': (datetime.utcnow() - timedelta(days=12)).isoformat(),
                'days_waiting': 12,
                'chase_count': 2,
                'last_chased_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'priority': 'high',
                'case_type': 'investment_advice',
                'client_value_score': 7.8,
                'recommended_action': 'phone_call',
                'reason': 'Application form blocking implementation, multiple chases sent'
            },
            {
                'item_id': 2,
                'case_id': 302,
                'client_name': 'Patricia Brown',
                'item_type': 'risk_questionnaire',
                'requested_at': (datetime.utcnow() - timedelta(days=8)).isoformat(),
                'days_waiting': 8,
                'chase_count': 1,
                'last_chased_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'priority': 'medium',
                'case_type': 'pension_advice',
                'client_value_score': 6.5,
                'recommended_action': 'email',
                'reason': 'Risk questionnaire required before proceeding'
            },
            {
                'item_id': 3,
                'case_id': 303,
                'client_name': 'William Taylor',
                'item_type': 'authority_to_proceed',
                'requested_at': (datetime.utcnow() - timedelta(days=18)).isoformat(),
                'days_waiting': 18,
                'chase_count': 3,
                'last_chased_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'priority': 'urgent',
                'case_type': 'pension_transfer',
                'client_value_score': 9.2,
                'recommended_action': 'escalate',
                'reason': 'Severely overdue, blocking time-sensitive transfer, high-value client'
            }
        ]
        
        # Apply filters
        if item_type:
            items = [i for i in items if item_type.lower() in i['item_type'].lower()]
        if priority:
            items = [i for i in items if i['priority'] == priority]
        
        return sorted(items, key=lambda x: (
            {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['priority'], 2),
            -x.get('days_waiting', 0),
            -(x.get('client_value_score') or 0)
        ))
    
    def find_stuck_items(self, stuck_threshold_days: int = 30) -> List[Dict]:
        """Find items that are stuck and need escalation"""
        logger.info(f"[Chasing] Finding stuck items (threshold={stuck_threshold_days} days)")
        
        # Combine all chase items and filter for stuck ones
        all_items = []
        
        # Get stuck LOAs
        loas = self.identify_loas_needing_chase()
        for loa in loas:
            days_since_sent = (datetime.utcnow() - datetime.fromisoformat(loa['sent_to_provider_at'].replace('Z', '+00:00'))).days
            if days_since_sent >= stuck_threshold_days:
                all_items.append({
                    **loa,
                    'item_category': 'loa',
                    'days_stuck': days_since_sent
                })
        
        # Get stuck documents
        documents = self.identify_documents_needing_chase()
        for doc in documents:
            if doc['days_waiting'] >= stuck_threshold_days:
                all_items.append({
                    **doc,
                    'item_category': 'document',
                    'days_stuck': doc['days_waiting']
                })
        
        # Get stuck post-advice items
        post_advice = self.identify_post_advice_items_needing_chase()
        for item in post_advice:
            if item['days_waiting'] >= stuck_threshold_days:
                all_items.append({
                    **item,
                    'item_category': 'post_advice',
                    'days_stuck': item['days_waiting']
                })
        
        return sorted(all_items, key=lambda x: (-x['days_stuck'], -x.get('client_value_score', 0)))
    
    def prioritize_chase_items(
        self,
        limit: int = 10,
        consider_client_value: bool = True
    ) -> List[Dict]:
        """Intelligently prioritize all chase items"""
        logger.info(f"[Chasing] Prioritizing chase items (limit={limit}, consider_value={consider_client_value})")
        
        all_items = []
        
        # Get all LOAs needing chase
        for loa in self.identify_loas_needing_chase():
            score = self._calculate_priority_score(loa, consider_client_value)
            all_items.append({
                **loa,
                'item_category': 'loa',
                'priority_score': score
            })
        
        # Get all documents needing chase
        for doc in self.identify_documents_needing_chase():
            score = self._calculate_priority_score(doc, consider_client_value)
            all_items.append({
                **doc,
                'item_category': 'document',
                'priority_score': score
            })
        
        # Get all post-advice items needing chase
        for item in self.identify_post_advice_items_needing_chase():
            score = self._calculate_priority_score(item, consider_client_value)
            all_items.append({
                **item,
                'item_category': 'post_advice',
                'priority_score': score
            })
        
        # Sort by priority score and return top items
        sorted_items = sorted(all_items, key=lambda x: -x['priority_score'])
        return sorted_items[:limit]
    
    def _calculate_priority_score(self, item: Dict, consider_client_value: bool) -> float:
        """Calculate priority score for an item"""
        score = 0.0
        
        # Priority weight
        priority_weights = {'urgent': 100, 'high': 75, 'medium': 50, 'low': 25}
        score += priority_weights.get(item.get('priority', 'medium'), 50)
        
        # Days overdue/waiting
        days = item.get('days_overdue') or item.get('days_waiting', 0)
        score += min(days * 2, 50)  # Cap at 50 points
        
        # Client value (if enabled)
        if consider_client_value:
            score += item.get('client_value_score', 5) * 5
        
        # Is blocking
        if item.get('is_blocking') or item.get('is_stuck'):
            score += 30
        
        # Chase count (more chases = higher priority)
        score += min(item.get('chase_count', 0) * 5, 20)
        
        return score
    
    def analyze_provider_performance(self, provider_name: Optional[str] = None) -> Dict:
        """Analyze provider response times and reliability"""
        logger.info(f"[Chasing] Analyzing provider performance (provider={provider_name})")
        
        providers = [
            {
                'provider_name': 'Aviva',
                'avg_response_days': 18,
                'reliability_score': 0.75,
                'total_loas': 12,
                'on_time_count': 9,
                'overdue_count': 3,
                'avg_days_overdue': 5.2,
                'recommendation': 'Generally reliable but occasional delays. Consider setting expectations at 20 days.'
            },
            {
                'provider_name': 'Legal & General',
                'avg_response_days': 15,
                'reliability_score': 0.85,
                'total_loas': 15,
                'on_time_count': 13,
                'overdue_count': 2,
                'avg_days_overdue': 3.5,
                'recommendation': 'Reliable provider. Good track record.'
            },
            {
                'provider_name': 'Standard Life',
                'avg_response_days': 25,
                'reliability_score': 0.60,
                'total_loas': 8,
                'on_time_count': 4,
                'overdue_count': 4,
                'avg_days_overdue': 12.3,
                'recommendation': 'Frequently delayed. Consider escalation process and setting client expectations at 30 days.'
            }
        ]
        
        if provider_name:
            providers = [p for p in providers if provider_name.lower() in p['provider_name'].lower()]
        
        return {
            'providers': providers,
            'summary': f'Analyzed {len(providers)} providers. Average response time: {sum(p["avg_response_days"] for p in providers) / len(providers):.1f} days.'
        }
    
    def identify_case_blocking_items(
        self,
        case_id: Optional[int] = None,
        case_type: Optional[str] = None
    ) -> List[Dict]:
        """Identify items blocking case progression"""
        logger.info(f"[Chasing] Identifying blocking items (case_id={case_id}, case_type={case_type})")
        
        blocking_items = []
        
        # Get blocking LOAs
        loas = self.identify_loas_needing_chase()
        for loa in loas:
            if case_id and loa['case_id'] != case_id:
                continue
            if case_type and loa['case_type'] != case_type:
                continue
            if loa.get('is_stuck') or loa.get('days_overdue', 0) > 0:
                blocking_items.append({
                    **loa,
                    'item_category': 'loa',
                    'blocking_reason': f"LOA overdue by {loa.get('days_overdue', 0)} days"
                })
        
        # Get blocking documents
        documents = self.identify_documents_needing_chase()
        for doc in documents:
            if case_id and doc['case_id'] != case_id:
                continue
            if case_type and doc['case_type'] != case_type:
                continue
            if doc.get('is_blocking'):
                blocking_items.append({
                    **doc,
                    'item_category': 'document',
                    'blocking_reason': f"Document waiting for {doc['days_waiting']} days"
                })
        
        # Get blocking post-advice items
        post_advice = self.identify_post_advice_items_needing_chase()
        for item in post-advice:
            if case_id and item['case_id'] != case_id:
                continue
            if case_type and item['case_type'] != case_type:
                continue
            if item['days_waiting'] > 7:  # Post-advice items waiting > 7 days are blocking
                blocking_items.append({
                    **item,
                    'item_category': 'post_advice',
                    'blocking_reason': f"Post-advice item waiting for {item['days_waiting']} days"
                })
        
        return sorted(blocking_items, key=lambda x: (
            {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['priority'], 2),
            -x.get('days_overdue', x.get('days_waiting', 0))
        ))
    
    def get_autonomous_chase_recommendations(
        self,
        action_type: Optional[str] = None
    ) -> List[Dict]:
        """Get autonomous chase recommendations"""
        logger.info(f"[Chasing] Generating autonomous chase recommendations")
        
        # Get prioritized items
        prioritized = self.prioritize_chase_items(limit=15, consider_client_value=True)
        
        recommendations = []
        for item in prioritized:
            rec = {
                **item,
                'recommended_channel': item.get('recommended_action', 'email'),
                'recommended_timing': self._calculate_optimal_timing(item),
                'suggested_message': self._generate_chase_message(item),
                'reasoning': item.get('reason', 'Item requires follow-up')
            }
            
            if action_type and rec['recommended_channel'] != action_type:
                continue
            
            recommendations.append(rec)
        
        return recommendations
    
    def _calculate_optimal_timing(self, item: Dict) -> str:
        """Calculate optimal timing for chase"""
        last_chased = item.get('last_chased_at')
        if not last_chased:
            return 'immediate'
        
        days_since_chase = (datetime.utcnow() - datetime.fromisoformat(last_chased.replace('Z', '+00:00'))).days
        
        if days_since_chase < 2:
            return 'wait_2_days'
        elif days_since_chase < 5:
            return 'ready_now'
        else:
            return 'overdue_for_chase'
    
    def _generate_chase_message(self, item: Dict) -> str:
        """Generate suggested chase message"""
        category = item.get('item_category', 'item')
        client_name = item.get('client_name', 'Client')
        
        if category == 'loa':
            return f"Hi {client_name}, just following up on the Letter of Authority sent to {item.get('provider_name', 'the provider')}. Expected response was {item.get('expected_response_date', 'recently')}. Could you confirm if you've received any updates?"
        elif category == 'document':
            return f"Hi {client_name}, we're still waiting on your {item.get('document_type', 'document')} to proceed with your case. Could you send this when convenient? Let me know if you need any clarification."
        else:
            return f"Hi {client_name}, just checking in on the {item.get('item_type', 'item')} we discussed. This is needed to move forward with your case. Please let me know if you have any questions."

