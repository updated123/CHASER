"""
Mock Data Service - Returns dummy data for testing without database
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


class MockDataService:
    """Provides mock data for testing without database"""
    
    @staticmethod
    def get_dashboard_stats() -> Dict:
        """Get mock dashboard statistics"""
        return {
            'total_active_chases': 45,
            'overdue_items': 12,
            'items_needing_chase': 28,
            'high_priority_items': 8,
            'predicted_bottlenecks': 5,
            'avg_days_stuck': 3.2
        }
    
    @staticmethod
    def get_active_chases() -> List[Dict]:
        """Get mock active chases"""
        clients = [
            "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis",
            "David Wilson", "Lisa Anderson", "Robert Taylor", "Jennifer Martinez"
        ]
        
        chase_types = ["loa", "client_document", "post_advice", "workflow_item"]
        priorities = ["urgent", "high", "medium", "low"]
        statuses = ["pending", "sent", "overdue", "acknowledged"]
        
        chases = []
        for i in range(20):
            chases.append({
                'id': i + 1,
                'chase_type': random.choice(chase_types),
                'client_name': random.choice(clients),
                'client_id': random.randint(1, 200),
                'case_id': random.randint(1, 80),
                'status': random.choice(statuses),
                'priority': random.choice(priorities),
                'stuck_score': round(random.uniform(0.1, 0.9), 2),
                'chase_count': random.randint(0, 5),
                'days_overdue': random.randint(0, 15),
                'days_since_last_chase': random.randint(0, 10),
                'last_chased_at': (datetime.utcnow() - timedelta(days=random.randint(0, 10))).isoformat(),
                'details': {
                    'provider_name': f"Provider {random.randint(1, 15)}" if random.choice(chase_types) == "loa" else None,
                    'document_type': random.choice(["passport", "payslip", "pension_statement"]) if random.choice(chase_types) == "client_document" else None,
                },
                'llm_priority_reasoning': 'High client value and multiple overdue chases indicate urgent attention needed',
                'llm_chase_reasoning': 'Client has been responsive in past, appropriate time since last contact',
                'llm_urgency_score': round(random.uniform(0.6, 0.95), 2)
            })
        
        return {'items': chases, 'count': len(chases)}
    
    @staticmethod
    def run_autonomous_cycle() -> Dict:
        """Mock autonomous cycle result"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_items_identified': 15,
            'actions_taken': [
                {
                    'type': 'loa',
                    'item_id': 1,
                    'client_name': 'John Smith',
                    'channel': 'email',
                    'priority': 'high',
                    'stuck_score': 0.75
                },
                {
                    'type': 'client_document',
                    'item_id': 2,
                    'client_name': 'Sarah Johnson',
                    'channel': 'sms',
                    'priority': 'urgent',
                    'stuck_score': 0.85
                },
                {
                    'type': 'post_advice',
                    'item_id': 3,
                    'client_name': 'Michael Brown',
                    'channel': 'email',
                    'priority': 'medium',
                    'stuck_score': 0.45
                }
            ],
            'summary_stats': {
                'urgent_items': 2,
                'high_priority_items': 5,
                'high_stuck_risk': 3
            }
        }
    
    @staticmethod
    def get_clients() -> List[Dict]:
        """Get mock clients"""
        return [
            {
                'id': i + 1,
                'name': f"{random.choice(['John', 'Sarah', 'Michael', 'Emily', 'David', 'Lisa'])} {random.choice(['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Anderson'])}",
                'email': f"client{i+1}@example.com",
                'phone': f"07{random.randint(100000000, 999999999)}",
                'client_value_score': round(random.uniform(0.5, 2.0), 2),
                'engagement_level': random.choice(['high', 'medium', 'low'])
            }
            for i in range(20)
        ]
    
    @staticmethod
    def get_cases(client_id: int = None) -> List[Dict]:
        """Get mock cases"""
        cases = [
            {
                'id': i + 1,
                'client_id': random.randint(1, 20),
                'case_type': random.choice(['pension_consolidation', 'investment_advice', 'retirement_planning', 'annual_review']),
                'status': random.choice(['in_progress', 'pending', 'awaiting_documents']),
                'priority': random.choice(['low', 'medium', 'high', 'urgent']),
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(0, 180))).isoformat(),
            }
            for i in range(30)
        ]
        if client_id:
            cases = [c for c in cases if c['client_id'] == client_id]
        return cases
    
    @staticmethod
    def process_insights_query(query: str) -> Dict:
        """Mock insights query processing"""
        query_lower = query.lower()
        
        # Mock results based on query type
        if 'equity' in query_lower or 'underweight' in query_lower:
            results = [
                {
                    'client_id': 1,
                    'client_name': 'John Smith',
                    'risk_profile': 'balanced',
                    'current_equity_percentage': 45.0,
                    'expected_equity_percentage': 60.0,
                    'underweight_by': 15.0,
                    'total_portfolio_value': 250000.0
                },
                {
                    'client_id': 2,
                    'client_name': 'Sarah Johnson',
                    'risk_profile': 'growth',
                    'current_equity_percentage': 65.0,
                    'expected_equity_percentage': 80.0,
                    'underweight_by': 15.0,
                    'total_portfolio_value': 180000.0
                }
            ]
            intent = 'investment_equity'
            summary = 'Found 2 clients who are underweight in equities relative to their risk profile. John Smith (balanced profile) has 45% equity vs expected 60%, and Sarah Johnson (growth profile) has 65% vs expected 80%.'
        
        elif 'isa' in query_lower and 'allowance' in query_lower:
            results = [
                {
                    'client_id': 3,
                    'client_name': 'Michael Brown',
                    'allowance_used': 5000.0,
                    'allowance_available': 15000.0,
                    'percentage_used': 25.0
                },
                {
                    'client_id': 4,
                    'client_name': 'Emily Davis',
                    'allowance_used': 0.0,
                    'allowance_available': 20000.0,
                    'percentage_used': 0.0
                }
            ]
            intent = 'investment_isa'
            summary = 'Found 2 clients with ISA allowance available. Michael Brown has £15,000 remaining (25% used), and Emily Davis has the full £20,000 allowance available.'
        
        elif 'review' in query_lower:
            results = [
                {
                    'client_id': 5,
                    'client_name': 'David Wilson',
                    'last_review_date': (datetime.utcnow() - timedelta(days=400)).isoformat(),
                    'months_since_review': 13.2,
                    'client_value_score': 8.5
                },
                {
                    'client_id': 6,
                    'client_name': 'Lisa Anderson',
                    'last_review_date': (datetime.utcnow() - timedelta(days=450)).isoformat(),
                    'months_since_review': 14.8,
                    'client_value_score': 7.8
                }
            ]
            intent = 'proactive_review'
            summary = 'Found 2 clients who haven\'t had a review in over 12 months. David Wilson (13.2 months) and Lisa Anderson (14.8 months) both require annual reviews for compliance.'
        
        elif 'protection' in query_lower and 'gap' in query_lower:
            results = [
                {
                    'client_id': 7,
                    'client_name': 'Robert Taylor',
                    'has_children': True,
                    'is_retired': False,
                    'protection_gaps': ['life_insurance', 'critical_illness'],
                    'current_policies': []
                }
            ]
            intent = 'investment_protection'
            summary = 'Found 1 client with protection gaps. Robert Taylor has children but no life insurance or critical illness cover.'
        
        elif 'cash' in query_lower or 'excess' in query_lower:
            results = [
                {
                    'client_id': 8,
                    'client_name': 'Jennifer Martinez',
                    'cash_holdings': 120000.0,
                    'monthly_expenditure': 5000.0,
                    'months_cash': 24.0,
                    'excess_months': 18.0
                }
            ]
            intent = 'investment_cash'
            summary = 'Found 1 client with excess cash. Jennifer Martinez has 24 months of cash reserves (18 months above the 6-month threshold), suggesting investment opportunities.'
        
        else:
            results = []
            intent = 'general_query'
            summary = f'Query processed: "{query}". This is a mock response. In production, this would be processed by the LLM and return real data.'
        
        return {
            'query': query,
            'intent': intent,
            'parameters': {},
            'results': results,
            'count': len(results),
            'summary': summary,
            'confidence': 0.85
        }

