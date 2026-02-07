"""
Mock implementations for insights methods - returns dummy data
All methods return realistic sample data without database queries
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

class InsightsMock:
    """Mock insights methods that return dummy data"""
    
    @staticmethod
    def clients_underweight_equities() -> List[Dict]:
        return [
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
    
    @staticmethod
    def clients_with_isa_allowance() -> List[Dict]:
        return [
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
    
    @staticmethod
    def clients_with_annual_allowance() -> List[Dict]:
        return [
            {
                'client_id': 5,
                'client_name': 'David Wilson',
                'allowance_used': 20000.0,
                'allowance_available': 40000.0,
                'percentage_used': 33.3
            }
        ]
    
    @staticmethod
    def clients_with_excess_cash(months_threshold: float = 6.0) -> List[Dict]:
        return [
            {
                'client_id': 8,
                'client_name': 'Jennifer Martinez',
                'cash_holdings': 120000.0,
                'monthly_expenditure': 5000.0,
                'months_cash': 24.0,
                'excess_months': 18.0
            }
        ]
    
    @staticmethod
    def clients_missing_retirement_goals() -> List[Dict]:
        return [
            {
                'client_id': 10,
                'client_name': 'Robert Taylor',
                'target_retirement_income': 50000.0,
                'projected_retirement_income': 35000.0,
                'shortfall': 15000.0,
                'years_to_retirement': 15
            }
        ]
    
    @staticmethod
    def clients_with_protection_gaps() -> List[Dict]:
        return [
            {
                'client_id': 7,
                'client_name': 'Robert Taylor',
                'has_children': True,
                'is_retired': False,
                'protection_gaps': ['life_insurance', 'critical_illness'],
                'current_policies': []
            }
        ]
    
    @staticmethod
    def retired_clients_high_withdrawal_rate(threshold: float = 4.0) -> List[Dict]:
        return [
            {
                'client_id': 11,
                'client_name': 'Mary Anderson',
                'withdrawal_rate': 5.2,
                'portfolio_value': 500000.0,
                'annual_withdrawal': 26000.0,
                'is_sustainable': False
            }
        ]
    
    @staticmethod
    def clients_impacted_by_interest_rate_drop(target_rate: float = 3.0) -> List[Dict]:
        return [
            {
                'client_id': 12,
                'client_name': 'James Wilson',
                'fixed_income_holdings': 200000.0,
                'current_rate': 4.5,
                'impact_at_target_rate': -30000.0,
                'percentage_impact': -15.0
            }
        ]
    
    @staticmethod
    def clients_exposed_to_market_correction(correction_percentage: float = 20.0) -> List[Dict]:
        return [
            {
                'client_id': 13,
                'client_name': 'Patricia Brown',
                'equity_exposure': 80.0,
                'portfolio_value': 300000.0,
                'potential_loss': 48000.0,
                'risk_level': 'high'
            }
        ]
    
    @staticmethod
    def model_long_term_care_impact(client_name: str) -> Dict:
        return {
            'client_name': client_name,
            'current_retirement_plan': {
                'monthly_income': 3000.0,
                'assets': 500000.0
            },
            'with_long_term_care': {
                'monthly_care_cost': 4000.0,
                'assets_depleted_in_years': 8.3,
                'impact': 'significant'
            }
        }
    
    @staticmethod
    def model_early_retirement_cashflow(client_name: str, new_retirement_year: Optional[int] = None) -> Dict:
        return {
            'client_name': client_name,
            'original_retirement_year': 2030,
            'new_retirement_year': new_retirement_year or 2029,
            'monthly_income_shortfall': 500.0,
            'years_of_shortfall': 5,
            'recommendation': 'Increase contributions or delay retirement'
        }
    
    @staticmethod
    def clients_due_review(months_threshold: int = 12) -> List[Dict]:
        return [
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
    
    @staticmethod
    def business_owners_for_rd_tax_credits() -> List[Dict]:
        return [
            {
                'client_id': 14,
                'client_name': 'Tech Solutions Ltd',
                'business_type': 'technology',
                'annual_revenue': 500000.0,
                'has_rd_discussion': False
            }
        ]
    
    @staticmethod
    def clients_with_children_approaching_university(years_ahead: int = 3) -> List[Dict]:
        return [
            {
                'client_id': 15,
                'client_name': 'Family Name',
                'children_ages': [16, 18],
                'has_education_planning': False,
                'years_to_university': years_ahead
            }
        ]
    
    @staticmethod
    def high_net_worth_no_estate_planning(threshold: float = 500000.0) -> List[Dict]:
        return [
            {
                'client_id': 16,
                'client_name': 'High Net Worth Client',
                'total_portfolio_value': 750000.0,
                'has_will': False,
                'has_estate_planning': False
            }
        ]
    
    @staticmethod
    def clients_with_portfolios_no_protection() -> List[Dict]:
        return [
            {
                'client_id': 17,
                'client_name': 'Portfolio Client',
                'portfolio_count': 2,
                'total_portfolio_value': 200000.0,
                'has_children': True,
                'is_retired': False
            }
        ]
    
    @staticmethod
    def business_owners_no_exit_planning() -> List[Dict]:
        return [
            {
                'client_id': 18,
                'client_name': 'Business Owner',
                'business_type': 'retail',
                'age': 58,
                'has_exit_discussion': False
            }
        ]
    
    @staticmethod
    def clients_with_birthdays_this_month() -> List[Dict]:
        return [
            {
                'client_id': 19,
                'client_name': 'Birthday Client',
                'birthday': datetime.utcnow().strftime('%Y-%m-%d'),
                'age': 45
            }
        ]
    
    @staticmethod
    def find_similar_client_profiles(reference_client_name: str) -> List[Dict]:
        return [
            {
                'client_id': 20,
                'client_name': 'Similar Client',
                'similarity_score': 85.0,
                'matching_factors': ['risk_profile', 'age', 'portfolio_value']
            }
        ]
    
    @staticmethod
    def clients_approaching_life_events() -> List[Dict]:
        return [
            {
                'client_id': 21,
                'client_name': 'Life Event Client',
                'events': [
                    {
                        'event': 'approaching_retirement',
                        'timeline': '2.5 years',
                        'recommendation': 'Review retirement planning'
                    }
                ]
            }
        ]
    
    @staticmethod
    def pension_clients_cashflow_modelling() -> List[Dict]:
        return [
            {
                'client_id': 22,
                'client_name': 'Pension Client',
                'pension_value': 300000.0,
                'age': 55,
                'retirement_age': 65,
                'years_to_retirement': 10
            }
        ]
    
    @staticmethod
    def clients_with_similar_successful_cases(client_name: str) -> List[Dict]:
        return [
            {
                'client_id': 23,
                'client_name': 'Similar Successful Case',
                'similarity_score': 90.0,
                'value_added': 50000.0,
                'services_used': ['portfolio_review', 'tax_planning']
            }
        ]
    
    @staticmethod
    def recommendations_for_client(client_name: str) -> List[Dict]:
        return [
            {
                'recommendation_id': 1,
                'title': 'Rebalance Portfolio',
                'rationale': 'Client is underweight in equities',
                'status': 'pending',
                'date': (datetime.utcnow() - timedelta(days=30)).isoformat()
            }
        ]
    
    @staticmethod
    def risk_discussion_wording(client_name: str) -> List[Dict]:
        return [
            {
                'meeting_date': (datetime.utcnow() - timedelta(days=60)).isoformat(),
                'wording': 'We discussed that your portfolio carries moderate risk...',
                'topics': ['risk_tolerance', 'volatility', 'time_horizon']
            }
        ]
    
    @staticmethod
    def clients_recommended_platform(platform_name: str) -> List[Dict]:
        return [
            {
                'client_id': 24,
                'client_name': 'Platform Client',
                'platform_name': platform_name,
                'reasoning': 'Low fees and good service',
                'date_recommended': (datetime.utcnow() - timedelta(days=90)).isoformat()
            }
        ]
    
    @staticmethod
    def conversations_mentioning_concern(concern: str) -> List[Dict]:
        return [
            {
                'meeting_id': 1,
                'client_name': 'Concerned Client',
                'meeting_date': (datetime.utcnow() - timedelta(days=15)).isoformat(),
                'concern_mentioned': concern,
                'context': 'Client expressed concerns about market volatility'
            }
        ]
    
    @staticmethod
    def documents_waiting_from_clients() -> List[Dict]:
        return [
            {
                'document_id': 1,
                'client_name': 'Document Client',
                'document_type': 'passport',
                'requested_at': (datetime.utcnow() - timedelta(days=10)).isoformat(),
                'days_waiting': 10
            }
        ]
    
    @staticmethod
    def promises_to_clients() -> List[Dict]:
        return [
            {
                'promise_id': 1,
                'client_name': 'Jackson Family',
                'promise': 'Send pension transfer forms',
                'promised_date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'status': 'pending'
            }
        ]
    
    @staticmethod
    def sustainable_investing_discussions() -> Dict:
        return {
            'summary': '5 clients expressed interest in ESG investments',
            'preferences': ['renewable_energy', 'social_responsibility'],
            'clients_count': 5
        }
    
    @staticmethod
    def analyze_recommendation_pushback() -> Dict:
        return {
            'most_pushback': 'portfolio_rebalancing',
            'reasons': ['market_timing_concerns', 'tax_implications'],
            'acceptance_rate': 65.0
        }
    
    @staticmethod
    def concerns_raised_this_month() -> List[Dict]:
        return [
            {
                'concern': 'inflation',
                'clients_count': 8,
                'severity': 'medium'
            },
            {
                'concern': 'market_volatility',
                'clients_count': 12,
                'severity': 'high'
            }
        ]
    
    @staticmethod
    def satisfied_long_term_clients(years: int = 5) -> Dict:
        return {
            'common_factors': [
                'regular_reviews',
                'proactive_communication',
                'diversified_portfolios'
            ],
            'satisfaction_rate': 92.0,
            'clients_count': 45
        }
    
    @staticmethod
    def life_events_triggering_recommendations() -> List[Dict]:
        return [
            {
                'life_event': 'retirement',
                'implementation_rate': 85.0,
                'clients_count': 20
            },
            {
                'life_event': 'inheritance',
                'implementation_rate': 90.0,
                'clients_count': 15
            }
        ]
    
    @staticmethod
    def waiting_on_information() -> List[Dict]:
        return [
            {
                'type': 'action_item',
                'client_name': 'Waiting Client',
                'description': 'Pension transfer forms',
                'days_waiting': 7
            }
        ]
    
    @staticmethod
    def all_open_action_items() -> List[Dict]:
        return [
            {
                'id': 1,
                'client_name': 'Action Client',
                'description': 'Review portfolio allocation',
                'status': 'pending',
                'due_date': (datetime.utcnow() + timedelta(days=5)).isoformat()
            }
        ]
    
    @staticmethod
    def overdue_follow_ups() -> List[Dict]:
        return [
            {
                'id': 1,
                'client_name': 'Overdue Client',
                'description': 'Follow up on meeting',
                'due_date': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'days_overdue': 3
            }
        ]
    
    @staticmethod
    def highest_value_client_services() -> List[Dict]:
        return [
            {'service': 'portfolio_review', 'usage_count': 45},
            {'service': 'retirement_planning', 'usage_count': 32},
            {'service': 'tax_planning', 'usage_count': 28}
        ]
    
    @staticmethod
    def conversion_rates_by_referral() -> List[Dict]:
        return [
            {
                'referral_source': 'existing_client',
                'total_leads': 25,
                'converted_clients': 20,
                'conversion_rate': 80.0
            },
            {
                'referral_source': 'website',
                'total_leads': 40,
                'converted_clients': 15,
                'conversion_rate': 37.5
            }
        ]
    
    @staticmethod
    def clients_approaching_retirement(years: int = 5) -> Dict:
        return {
            'total_clients': 150,
            'approaching_retirement': 45,
            'percentage': 30.0,
            'years_ahead': years
        }
    
    @staticmethod
    def most_efficient_clients() -> List[Dict]:
        return [
            {
                'client_id': 25,
                'client_name': 'Efficient Client',
                'annual_revenue': 5000.0,
                'service_time_hours': 2.0,
                'revenue_per_hour': 2500.0
            }
        ]
    
    @staticmethod
    def satisfied_long_term_clients(years: int = 5) -> Dict:
        return {
            'total_satisfied_clients': 45,
            'average_satisfaction': 9.2,
            'common_services': [('portfolio_review', 40), ('retirement_planning', 35)],
            'common_risk_profiles': [('balanced', 25), ('growth', 15)]
        }
    
    @staticmethod
    def draft_follow_up_email(meeting_id: int) -> Dict:
        return {
            'meeting_id': meeting_id,
            'client_name': 'Test Client',
            'meeting_date': datetime.utcnow().isoformat(),
            'email_content': 'Subject: Follow-up\n\nDear Test,\n\nThank you for the meeting...',
            'action_items': [
                {
                    'id': 1,
                    'title': 'Review portfolio',
                    'description': 'Client to review portfolio allocation',
                    'assigned_to': 'client'
                }
            ]
        }

