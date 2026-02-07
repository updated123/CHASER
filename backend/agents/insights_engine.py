"""
Insights Engine - Answers adviser queries about clients, investments, compliance, etc.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case
from models import (
    Client, InvestmentPortfolio, ProtectionPolicy, Meeting, Recommendation,
    ActionItem, Case, Communication
)
from agents.llm_service import LLMService
from agents.insights_mock import InsightsMock

logger = logging.getLogger(__name__)


class InsightsEngine:
    """Engine for answering adviser insight queries"""
    
    def __init__(self, db: Session, llm_service=None):
        # db can be None or mock session - we use mock data anyway
        self.db = db
        self.llm_service = llm_service or LLMService()  # Use LLM for natural language queries
        self.current_tax_year = 2024  # Could be dynamic
        self.isa_allowance = 20000.0  # Current ISA allowance
        self.annual_allowance = 60000.0  # Pension annual allowance
        # All methods will use mock data - db queries return empty lists
    
    # ========== INVESTMENT INSIGHTS ==========
    
    def clients_underweight_equities(self) -> List[Dict]:
        """Which clients are underweight in equities relative to their risk profile?"""
        return InsightsMock.clients_underweight_equities()
    
    def clients_with_isa_allowance(self) -> List[Dict]:
        """Show clients with ISA allowance still available this tax year"""
        return InsightsMock.clients_with_isa_allowance()
    
    def clients_with_annual_allowance(self) -> List[Dict]:
        """Show clients with pension annual allowance still available"""
        return InsightsMock.clients_with_annual_allowance()
    
    def clients_with_excess_cash(self, months_threshold: float = 6.0) -> List[Dict]:
        """Clients with cash excess above threshold months of expenditure"""
        clients = self.db.query(Client).filter(
            Client.total_cash_holdings > 0,
            Client.monthly_expenditure > 0
        ).all()
        
        results = []
        for client in clients:
            months_cash = client.total_cash_holdings / client.monthly_expenditure
            
            if months_cash > months_threshold:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'cash_holdings': client.total_cash_holdings,
                    'monthly_expenditure': client.monthly_expenditure,
                    'months_cash': round(months_cash, 1),
                    'excess_months': round(months_cash - months_threshold, 1),
                })
        
        return sorted(results, key=lambda x: x['excess_months'], reverse=True)
    
    def clients_missing_retirement_goals(self) -> List[Dict]:
        """Clients where current trajectory won't meet retirement income goals"""
        clients = self.db.query(Client).filter(
            Client.target_retirement_income.isnot(None),
            Client.target_retirement_income > 0,
            Client.target_retirement_date.isnot(None)
        ).all()
        
        results = []
        for client in clients:
            years_to_retirement = (client.target_retirement_date - datetime.utcnow()).days / 365.25
            
            if years_to_retirement <= 0:
                continue
            
            # Simple projection (would be more sophisticated in reality)
            current_portfolio = client.total_portfolio_value
            annual_contribution = (client.annual_income * 0.15) if client.annual_income else 0
            growth_rate = 0.05  # 5% assumed growth
            
            projected_value = self._project_portfolio_value(
                current_portfolio, annual_contribution, growth_rate, years_to_retirement
            )
            
            # 4% withdrawal rule
            projected_income = projected_value * 0.04
            
            if projected_income < client.target_retirement_income:
                shortfall = client.target_retirement_income - projected_income
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'target_retirement_date': client.target_retirement_date.isoformat(),
                    'years_to_retirement': round(years_to_retirement, 1),
                    'target_income': client.target_retirement_income,
                    'projected_income': round(projected_income, 2),
                    'shortfall': round(shortfall, 2),
                    'current_portfolio': current_portfolio,
                })
        
        return sorted(results, key=lambda x: x['shortfall'], reverse=True)
    
    def clients_with_protection_gaps(self) -> List[Dict]:
        """Clients with protection gaps based on family circumstances"""
        clients = self.db.query(Client).filter(
            or_(
                Client.has_children == True,
                Client.marital_status.in_(['married', 'civil_partnership'])
            )
        ).all()
        
        results = []
        for client in clients:
            policies = self.db.query(ProtectionPolicy).filter_by(
                client_id=client.id,
                status='active'
            ).all()
            
            has_life = any(p.policy_type == 'life_insurance' for p in policies)
            has_critical_illness = any(p.policy_type == 'critical_illness' for p in policies)
            has_income_protection = any(p.policy_type == 'income_protection' for p in policies)
            
            gaps = []
            if client.has_children and not has_life:
                gaps.append('life_insurance')
            if client.has_children and not has_critical_illness:
                gaps.append('critical_illness')
            if not client.is_retired and not has_income_protection:
                gaps.append('income_protection')
            
            if gaps:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'has_children': client.has_children,
                    'is_retired': client.is_retired,
                    'protection_gaps': gaps,
                    'current_policies': [p.policy_type for p in policies],
                })
        
        return results
    
    def retired_clients_high_withdrawal_rate(self, threshold: float = 4.0) -> List[Dict]:
        """Retired clients taking more than threshold % withdrawal rate"""
        logger.info(f"[insights] Analyzing high withdrawal rates (threshold: {threshold}%)")
        return InsightsMock.retired_clients_high_withdrawal_rate(threshold)
    
    def clients_impacted_by_interest_rate_drop(self, target_rate: float = 3.0) -> List[Dict]:
        """Show clients who would be impacted if interest rates drop to target_rate"""
        logger.info(f"[insights] Analyzing impact of interest rate drop to {target_rate}%")
        return InsightsMock.clients_impacted_by_interest_rate_drop(target_rate)
    
    def model_long_term_care_impact(self, client_name: str) -> Dict:
        """Model what happens to a family's plan if one needs long-term care"""
        logger.info(f"[insights] Modeling long-term care impact for {client_name}")
        return InsightsMock.model_long_term_care_impact(client_name)
    
    def clients_exposed_to_market_correction(self, correction_percentage: float = 20.0) -> List[Dict]:
        """Which clients are most exposed if we see a market correction?"""
        logger.info(f"[insights] Analyzing exposure to {correction_percentage}% market correction")
        return InsightsMock.clients_exposed_to_market_correction(correction_percentage)
    
    def model_early_retirement_cashflow(self, client_name: str, new_retirement_year: Optional[int] = None) -> Dict:
        """Model cashflow if client retires earlier than planned"""
        logger.info(f"[insights] Modeling early retirement cashflow for {client_name} (year: {new_retirement_year})")
        return InsightsMock.model_early_retirement_cashflow(client_name, new_retirement_year)
        
        # Calculate shortfall
        target_income = client.target_retirement_income or (original_projected_value * 0.04)
        original_projected_income = original_projected_value * 0.04
        new_projected_income = new_projected_value * 0.04
        shortfall = target_income - new_projected_income
        
        result = {
            'client_id': client.id,
            'client_name': client.name,
            'original_retirement_year': original_retirement_year,
            'new_retirement_year': new_retirement_year,
            'years_earlier': years_difference,
            'current_portfolio': current_portfolio,
            'original_projected_portfolio': round(original_projected_value, 2),
            'new_projected_portfolio': round(new_projected_value, 2),
            'portfolio_difference': round(original_projected_value - new_projected_value, 2),
            'target_retirement_income': target_income,
            'original_projected_income': round(original_projected_income, 2),
            'new_projected_income': round(new_projected_income, 2),
            'income_shortfall': round(shortfall, 2),
            'recommendation': 'Consider increasing contributions or adjusting retirement income expectations' if shortfall > 0 else 'Early retirement appears feasible',
        }
        
        logger.info(f"[insights] Early retirement impact: {shortfall:.2f} shortfall")
        return result
    
    # ========== PROACTIVE INSIGHTS ==========
    
    def clients_due_review(self, months_threshold: int = 12) -> List[Dict]:
        """Clients who haven't had a review in over threshold months"""
        return InsightsMock.clients_due_review(months_threshold)
    
    def business_owners_for_rd_tax_credits(self) -> List[Dict]:
        """Business owners who might benefit from R&D tax credit changes"""
        return InsightsMock.business_owners_for_rd_tax_credits()
        
        results = []
        for client in clients:
            # Check if they have recent cases or meetings discussing R&D
            recent_meetings = self.db.query(Meeting).filter(
                Meeting.client_id == client.id,
                Meeting.meeting_date > datetime.utcnow() - timedelta(days=365)
            ).all()
            
            has_rd_discussion = any(
                'rd' in str(m.topics_discussed).lower() or 
                'research' in str(m.topics_discussed).lower() or
                'development' in str(m.topics_discussed).lower()
                for m in recent_meetings if m.topics_discussed
            )
            
            results.append({
                'client_id': client.id,
                'client_name': client.name,
                'business_type': client.business_type,
                'has_rd_discussion': has_rd_discussion,
                'annual_revenue': client.annual_revenue,
            })
        
        return results
    
    def clients_with_children_approaching_university(self, years_ahead: int = 3) -> List[Dict]:
        """Clients with children approaching university age but no education planning"""
        return InsightsMock.clients_with_children_approaching_university(years_ahead)
        
        results = []
        for client in clients:
            if not client.children_ages:
                continue
            
            children_approaching = []
            for age in client.children_ages:
                if isinstance(age, (int, float)) and 15 <= age <= (18 + years_ahead):
                    children_approaching.append(age)
            
            if children_approaching:
                # Check for education planning in cases or recommendations
                education_cases = self.db.query(Case).filter(
                    Case.client_id == client.id,
                    Case.case_type.like('%education%')
                ).count()
                
                education_recommendations = self.db.query(Recommendation).filter(
                    Recommendation.client_id == client.id,
                    Recommendation.recommendation_type.like('%education%')
                ).count()
                
                if education_cases == 0 and education_recommendations == 0:
                    results.append({
                        'client_id': client.id,
                        'client_name': client.name,
                        'children_ages': client.children_ages,
                        'children_approaching_university': children_approaching,
                        'has_education_planning': False,
                    })
        
        return results
    
    def high_net_worth_no_estate_planning(self, threshold: float = 500000.0) -> List[Dict]:
        """High-net-worth clients without estate planning"""
        return InsightsMock.high_net_worth_no_estate_planning(threshold)
        
        results = []
        for client in clients:
            results.append({
                'client_id': client.id,
                'client_name': client.name,
                'total_portfolio_value': client.total_portfolio_value,
                'has_will': client.has_will,
                'has_lpa': client.has_lpa,
                'has_estate_planning': client.has_estate_planning,
            })
        
        return sorted(results, key=lambda x: x['total_portfolio_value'], reverse=True)
    
    def pension_clients_cashflow_modelling(self) -> List[Dict]:
        """Pension clients who might benefit from cashflow modelling service"""
        logger.info("[insights] Finding pension clients for cashflow modelling")
        return InsightsMock.pension_clients_cashflow_modelling()
        
        results = []
        for client in clients:
            # Check if they have cashflow modelling case
            cases = self.db.query(Case).filter_by(client_id=client.id).all()
            has_cashflow_case = any('cashflow' in c.case_type.lower() or 'modelling' in c.case_type.lower() for c in cases)
            
            if not has_cashflow_case:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'pension_value': client.pension_value or 0,
                    'age': self._calculate_age(client.date_of_birth) if client.date_of_birth else None,
                    'retirement_age': client.planned_retirement_age or 65,
                    'years_to_retirement': (client.planned_retirement_age or 65) - (self._calculate_age(client.date_of_birth) or 0) if client.date_of_birth else None,
                })
        
        logger.info(f"[insights] Found {len(results)} pension clients for cashflow modelling")
        return sorted(results, key=lambda x: x.get('pension_value', 0), reverse=True)
    
    def clients_with_portfolios_no_protection(self) -> List[Dict]:
        """Clients with investment portfolios but no protection cover"""
        logger.info("[insights] Finding clients with portfolios but no protection")
        return InsightsMock.clients_with_portfolios_no_protection()
        
        results = []
        for client in clients:
            portfolios = self.db.query(InvestmentPortfolio).filter_by(
                client_id=client.id
            ).count()
            
            protection_policies = self.db.query(ProtectionPolicy).filter_by(
                client_id=client.id,
                status='active'
            ).count()
            
            if portfolios > 0 and protection_policies == 0:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'portfolio_count': portfolios,
                    'total_portfolio_value': client.total_portfolio_value,
                    'has_children': client.has_children,
                    'is_retired': client.is_retired,
                })
        
        return sorted(results, key=lambda x: x['total_portfolio_value'], reverse=True)
    
    def business_owners_no_exit_planning(self) -> List[Dict]:
        """Business owner clients who haven't discussed exit planning"""
        return InsightsMock.business_owners_no_exit_planning()
        
        results = []
        for client in clients:
            # Check meetings and recommendations for exit planning
            meetings = self.db.query(Meeting).filter_by(client_id=client.id).all()
            recommendations = self.db.query(Recommendation).filter_by(client_id=client.id).all()
            
            has_exit_discussion = False
            for meeting in meetings:
                if meeting.topics_discussed and 'exit' in str(meeting.topics_discussed).lower():
                    has_exit_discussion = True
                    break
            
            if not has_exit_discussion:
                for rec in recommendations:
                    if 'exit' in rec.recommendation_type.lower() or 'exit' in rec.title.lower():
                        has_exit_discussion = True
                        break
            
            if not has_exit_discussion:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'business_type': client.business_type,
                    'age': self._calculate_age(client.date_of_birth) if client.date_of_birth else None,
                })
        
        return results
    
    def clients_with_birthdays_this_month(self) -> List[Dict]:
        """Clients with birthdays this month"""
        logger.info("[insights] Finding clients with birthdays this month")
        return InsightsMock.clients_with_birthdays_this_month()
        
        results = []
        for client in clients:
            if client.date_of_birth.month == current_month:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'birthday': client.date_of_birth.strftime('%Y-%m-%d'),
                    'age': self._calculate_age(client.date_of_birth),
                })
        
        logger.info(f"[insights] Found {len(results)} clients with birthdays this month")
        return sorted(results, key=lambda x: x['birthday'])
    
    def find_similar_client_profiles(self, reference_client_name: str) -> List[Dict]:
        """Find clients with similar profiles to a reference client"""
        logger.info(f"[insights] Finding similar profiles to {reference_client_name}")
        return InsightsMock.find_similar_client_profiles(reference_client_name)
        if not reference_client:
            logger.warning(f"[insights] Reference client {reference_client_name} not found")
            return []
        
        # Get reference client's successful cases
        reference_cases = self.db.query(Case).filter_by(client_id=reference_client.id).all()
        successful_case_types = [c.case_type for c in reference_cases if c.status == 'completed']
        
        # Find similar clients based on:
        # - Similar risk profile
        # - Similar portfolio value range (±20%)
        # - Similar age range (±5 years)
        # - Similar circumstances (retired, business owner, etc.)
        reference_age = self._calculate_age(reference_client.date_of_birth)
        portfolio_range = (reference_client.total_portfolio_value * 0.8, reference_client.total_portfolio_value * 1.2)
        
        similar_clients = self.db.query(Client).filter(
            Client.id != reference_client.id,
            Client.risk_profile == reference_client.risk_profile,
            Client.total_portfolio_value.between(portfolio_range[0], portfolio_range[1]),
            Client.is_retired == reference_client.is_retired,
            Client.is_business_owner == reference_client.is_business_owner,
        ).all()
        
        results = []
        for client in similar_clients:
            client_age = self._calculate_age(client.date_of_birth)
            age_diff = abs(client_age - reference_age) if client_age and reference_age else 999
            
            if age_diff <= 5:  # Within 5 years
                # Check what services they've used
                client_cases = self.db.query(Case).filter_by(client_id=client.id).all()
                services_used = [c.case_type for c in client_cases]
                
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'age': client_age,
                    'portfolio_value': client.total_portfolio_value,
                    'risk_profile': client.risk_profile,
                    'services_used': services_used,
                    'similarity_score': self._calculate_similarity_score(reference_client, client),
                    'recommended_services': [s for s in successful_case_types if s not in services_used],
                })
        
        logger.info(f"[insights] Found {len(results)} similar clients")
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)[:10]
    
    def clients_approaching_life_events(self) -> List[Dict]:
        """Identify clients approaching significant life events that might trigger recommendations"""
        logger.info("[insights] Identifying clients approaching life events")
        clients = self.db.query(Client).all()
        
        results = []
        current_date = datetime.utcnow()
        
        for client in clients:
            events = []
            
            # Approaching retirement
            if client.target_retirement_date and not client.is_retired:
                years_to_retirement = (client.target_retirement_date - current_date).days / 365.25
                if 1 <= years_to_retirement <= 3:
                    events.append({
                        'event': 'approaching_retirement',
                        'timeline': f"{round(years_to_retirement, 1)} years",
                        'recommendation': 'Review retirement planning and income strategy'
                    })
            
            # Children approaching university age
            if client.has_children and client.children_ages:
                for age in client.children_ages:
                    if isinstance(age, (int, float)) and 15 <= age <= 17:
                        events.append({
                            'event': 'child_approaching_university',
                            'timeline': f"{18 - age} years",
                            'recommendation': 'Discuss education funding and planning'
                        })
            
            # Approaching state pension age (simplified - would need actual calculation)
            client_age = self._calculate_age(client.date_of_birth)
            if client_age and 62 <= client_age <= 66:
                events.append({
                    'event': 'approaching_state_pension_age',
                    'timeline': f"{66 - client_age} years",
                    'recommendation': 'Review state pension entitlement and planning'
                })
            
            # Business owners approaching typical exit age
            if client.is_business_owner:
                if client_age and 55 <= client_age <= 65:
                    events.append({
                        'event': 'potential_business_exit',
                        'timeline': '5-10 years',
                        'recommendation': 'Discuss business exit planning and succession'
                    })
            
            if events:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'age': client_age,
                    'upcoming_events': events,
                    'priority': 'high' if len(events) > 1 else 'medium',
                })
        
        logger.info(f"[insights] Found {len(results)} clients approaching life events")
        return sorted(results, key=lambda x: len(x['upcoming_events']), reverse=True)
    
    # ========== COMPLIANCE INSIGHTS ==========
    
    def recommendations_for_client(self, client_name: str) -> List[Dict]:
        """Pull every recommendation made to a client and rationale"""
        return InsightsMock.recommendations_for_client(client_name)
        if not client:
            return []
        
        recommendations = self.db.query(Recommendation).filter_by(
            client_id=client.id
        ).order_by(Recommendation.created_at.desc()).all()
        
        results = []
        for rec in recommendations:
            meeting = None
            if rec.meeting_id:
                meeting = self.db.query(Meeting).filter_by(id=rec.meeting_id).first()
            
            results.append({
                'recommendation_id': rec.id,
                'title': rec.title,
                'type': rec.recommendation_type,
                'description': rec.description,
                'rationale': rec.rationale,
                'exact_wording': rec.exact_wording,
                'status': rec.status,
                'created_at': rec.created_at.isoformat(),
                'meeting_date': meeting.meeting_date.isoformat() if meeting else None,
            })
        
        return results
    
    def risk_discussion_wording(self, client_name: str) -> List[Dict]:
        """Exact wording when discussing risk with a client"""
        return InsightsMock.risk_discussion_wording(client_name)
        if not client:
            return []
        
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.client_id == client.id,
            or_(
                Recommendation.recommendation_type.like('%risk%'),
                Recommendation.title.like('%risk%')
            )
        ).all()
        
        meetings = self.db.query(Meeting).filter_by(client_id=client.id).all()
        
        results = []
        for rec in recommendations:
            if rec.exact_wording:
                results.append({
                    'type': 'recommendation',
                    'date': rec.created_at.isoformat(),
                    'wording': rec.exact_wording,
                })
        
        for meeting in meetings:
            if meeting.transcript and 'risk' in meeting.transcript.lower():
                results.append({
                    'type': 'meeting_transcript',
                    'date': meeting.meeting_date.isoformat(),
                    'wording': meeting.transcript,
                })
        
        return sorted(results, key=lambda x: x['date'], reverse=True)
    
    def clients_recommended_platform(self, platform_name: str) -> List[Dict]:
        """Show all clients where Platform X was recommended and why"""
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.platform_recommended.ilike(f'%{platform_name}%')
        ).all()
        
        results = []
        for rec in recommendations:
            client = self.db.query(Client).filter_by(id=rec.client_id).first()
            results.append({
                'client_id': client.id if client else None,
                'client_name': client.name if client else 'Unknown',
                'recommendation_id': rec.id,
                'title': rec.title,
                'rationale': rec.rationale,
                'exact_wording': rec.exact_wording,
                'created_at': rec.created_at.isoformat(),
                'status': rec.status,
            })
        
        return results
    
    def conversations_mentioning_concern(self, concern: str) -> List[Dict]:
        """Client conversations that mentioned concerns about a topic"""
        logger.info(f"[insights] Finding conversations mentioning: {concern}")
        meetings = self.db.query(Meeting).filter(
            or_(
                Meeting.notes.ilike(f'%{concern}%'),
                Meeting.transcript.ilike(f'%{concern}%'),
                Meeting.concerns_raised.isnot(None)
            )
        ).all()
        
        results = []
        for meeting in meetings:
            client = self.db.query(Client).filter_by(id=meeting.client_id).first()
            
            concerns_list = []
            if meeting.concerns_raised:
                concerns_list = meeting.concerns_raised if isinstance(meeting.concerns_raised, list) else [meeting.concerns_raised]
            
            if concern.lower() in str(meeting.concerns_raised).lower() or concern.lower() in str(meeting.notes).lower():
                results.append({
                    'meeting_id': meeting.id,
                    'client_id': client.id if client else None,
                    'client_name': client.name if client else 'Unknown',
                    'meeting_date': meeting.meeting_date.isoformat(),
                    'meeting_type': meeting.meeting_type,
                    'concerns_raised': concerns_list,
                    'notes': meeting.notes,
                })
        
        logger.info(f"[insights] Found {len(results)} conversations mentioning {concern}")
        return sorted(results, key=lambda x: x['meeting_date'], reverse=True)
    
    def sustainable_investing_discussions(self) -> Dict:
        """Generate summary of all discussions about sustainable investing preferences"""
        logger.info("[insights] Analyzing sustainable investing discussions")
        meetings = self.db.query(Meeting).filter(
            or_(
                Meeting.notes.ilike('%sustainable%'),
                Meeting.notes.ilike('%esg%'),
                Meeting.notes.ilike('%environmental%'),
                Meeting.notes.ilike('%social%'),
                Meeting.notes.ilike('%governance%'),
                Meeting.transcript.ilike('%sustainable%'),
                Meeting.transcript.ilike('%esg%'),
            )
        ).all()
        
        clients_discussed = set()
        recommendations_made = []
        
        for meeting in meetings:
            client = self.db.query(Client).filter_by(id=meeting.client_id).first()
            if client:
                clients_discussed.add(client.id)
            
            # Check for related recommendations
            recs = self.db.query(Recommendation).filter_by(meeting_id=meeting.id).all()
            for rec in recs:
                if 'sustainable' in rec.title.lower() or 'esg' in rec.title.lower():
                    recommendations_made.append({
                        'client_name': client.name if client else 'Unknown',
                        'recommendation': rec.title,
                        'status': rec.status,
                        'date': rec.created_at.isoformat(),
                    })
        
        result = {
            'total_discussions': len(meetings),
            'unique_clients': len(clients_discussed),
            'recommendations_made': len(recommendations_made),
            'recommendations': recommendations_made,
            'acceptance_rate': self._calculate_acceptance_rate(recommendations_made),
        }
        
        logger.info(f"[insights] Found {len(meetings)} sustainable investing discussions")
        return result
    
    def analyze_recommendation_pushback(self) -> Dict:
        """Which types of recommendations get the most pushback and why?"""
        logger.info("[insights] Analyzing recommendation pushback patterns")
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.status.in_(['rejected', 'deferred'])
        ).all()
        
        pushback_by_type = {}
        pushback_reasons = {}
        
        for rec in recommendations:
            rec_type = rec.recommendation_type
            pushback_by_type[rec_type] = pushback_by_type.get(rec_type, 0) + 1
            
            # Extract reasons from client response
            if rec.client_response:
                response_lower = rec.client_response.lower()
                if 'cost' in response_lower or 'expensive' in response_lower:
                    pushback_reasons['cost'] = pushback_reasons.get('cost', 0) + 1
                if 'complex' in response_lower or 'complicated' in response_lower:
                    pushback_reasons['complexity'] = pushback_reasons.get('complexity', 0) + 1
                if 'time' in response_lower or 'busy' in response_lower:
                    pushback_reasons['time_constraints'] = pushback_reasons.get('time_constraints', 0) + 1
                if 'risk' in response_lower or 'risky' in response_lower:
                    pushback_reasons['risk_concerns'] = pushback_reasons.get('risk_concerns', 0) + 1
                if 'not ready' in response_lower or 'later' in response_lower:
                    pushback_reasons['timing'] = pushback_reasons.get('timing', 0) + 1
        
        # Calculate acceptance rates by type
        all_recommendations = self.db.query(Recommendation).all()
        total_by_type = {}
        accepted_by_type = {}
        
        for rec in all_recommendations:
            rec_type = rec.recommendation_type
            total_by_type[rec_type] = total_by_type.get(rec_type, 0) + 1
            if rec.status == 'accepted' or rec.status == 'implemented':
                accepted_by_type[rec_type] = accepted_by_type.get(rec_type, 0) + 1
        
        acceptance_rates = {}
        for rec_type, total in total_by_type.items():
            accepted = accepted_by_type.get(rec_type, 0)
            acceptance_rates[rec_type] = round((accepted / total * 100), 1) if total > 0 else 0
        
        result = {
            'total_pushback': len(recommendations),
            'pushback_by_type': sorted(pushback_by_type.items(), key=lambda x: x[1], reverse=True),
            'common_reasons': sorted(pushback_reasons.items(), key=lambda x: x[1], reverse=True),
            'acceptance_rates_by_type': acceptance_rates,
            'lowest_acceptance_types': sorted(acceptance_rates.items(), key=lambda x: x[1])[:5],
        }
        
        logger.info(f"[insights] Analyzed {len(recommendations)} pushback cases")
        return result
    
    def clients_with_similar_successful_cases(self, reference_client_name: str) -> List[Dict]:
        """Show clients whose circumstances are similar to cases where we added significant value"""
        logger.info(f"[insights] Finding clients similar to successful cases for {reference_client_name}")
        return InsightsMock.clients_with_similar_successful_cases(reference_client_name)
        if not reference_client:
            return []
        
        # Get high-value cases for reference client
        reference_cases = self.db.query(Case).filter_by(client_id=reference_client.id).all()
        high_value_cases = [c for c in reference_cases if c.status == 'completed']
        
        if not high_value_cases:
            return []
        
        # Find clients with similar profiles who haven't had these services
        similar_clients = self.find_similar_client_profiles(reference_client_name)
        
        results = []
        for similar in similar_clients:
            client = self.db.query(Client).filter_by(id=similar['client_id']).first()
            if not client:
                continue
            
            # Check what services they're missing
            client_cases = self.db.query(Case).filter_by(client_id=client.id).all()
            client_service_types = [c.case_type for c in client_cases]
            
            missing_services = [s for s in similar['recommended_services'] if s not in client_service_types]
            
            if missing_services:
                results.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'similarity_score': similar['similarity_score'],
                    'successful_services_for_reference': [c.case_type for c in high_value_cases],
                    'missing_high_value_services': missing_services,
                    'potential_value': 'high' if len(missing_services) > 1 else 'medium',
                })
        
        logger.info(f"[insights] Found {len(results)} clients with similar successful case opportunities")
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    
    def life_events_triggering_recommendations(self) -> Dict:
        """What life events trigger clients to actually implement recommendations?"""
        logger.info("[insights] Analyzing life events triggering recommendation implementation")
        recommendations = self.db.query(Recommendation).filter(
            Recommendation.status == 'implemented'
        ).all()
        
        # Get meetings around implementation dates
        events_triggering = {}
        
        for rec in recommendations:
            if rec.implementation_date:
                # Find meetings within 3 months before implementation
                meeting_window_start = rec.implementation_date - timedelta(days=90)
                
                meetings = self.db.query(Meeting).filter(
                    Meeting.client_id == rec.client_id,
                    Meeting.meeting_date >= meeting_window_start,
                    Meeting.meeting_date <= rec.implementation_date
                ).all()
                
                for meeting in meetings:
                    # Check for life events in meeting notes
                    notes_lower = (meeting.notes or '').lower()
                    transcript_lower = (meeting.transcript or '').lower()
                    
                    if 'retirement' in notes_lower or 'retiring' in notes_lower:
                        events_triggering['retirement'] = events_triggering.get('retirement', 0) + 1
                    if 'marriage' in notes_lower or 'married' in notes_lower:
                        events_triggering['marriage'] = events_triggering.get('marriage', 0) + 1
                    if 'birth' in notes_lower or 'baby' in notes_lower or 'child' in notes_lower:
                        events_triggering['birth_of_child'] = events_triggering.get('birth_of_child', 0) + 1
                    if 'divorce' in notes_lower or 'divorced' in notes_lower:
                        events_triggering['divorce'] = events_triggering.get('divorce', 0) + 1
                    if 'inheritance' in notes_lower or 'inherited' in notes_lower:
                        events_triggering['inheritance'] = events_triggering.get('inheritance', 0) + 1
                    if 'job' in notes_lower and ('change' in notes_lower or 'new' in notes_lower):
                        events_triggering['job_change'] = events_triggering.get('job_change', 0) + 1
                    if 'illness' in notes_lower or 'health' in notes_lower:
                        events_triggering['health_event'] = events_triggering.get('health_event', 0) + 1
        
        result = {
            'total_implementations': len(recommendations),
            'life_events_triggering_implementation': sorted(events_triggering.items(), key=lambda x: x[1], reverse=True),
            'most_common_trigger': max(events_triggering.items(), key=lambda x: x[1])[0] if events_triggering else None,
        }
        
        logger.info(f"[insights] Analyzed {len(recommendations)} implementations")
        return result
    
    def documents_waiting_from_clients(self) -> List[Dict]:
        """What documents are still waiting for from clients?"""
        from models import DocumentRequest
        
        requests = self.db.query(DocumentRequest).filter(
            DocumentRequest.status.in_(['pending', 'overdue'])
        ).all()
        
        results = []
        for req in requests:
            case = self.db.query(Case).filter_by(id=req.case_id).first()
            client = self.db.query(Client).filter_by(id=case.client_id).first() if case else None
            
            days_waiting = (datetime.utcnow() - req.requested_at).days if req.requested_at else 0
            
            results.append({
                'document_request_id': req.id,
                'client_id': client.id if client else None,
                'client_name': client.name if client else 'Unknown',
                'document_type': req.document_type,
                'case_type': case.case_type if case else None,
                'requested_at': req.requested_at.isoformat() if req.requested_at else None,
                'days_waiting': days_waiting,
                'chase_count': req.chase_count,
            })
        
        return sorted(results, key=lambda x: x['days_waiting'], reverse=True)
    
    def promises_to_clients(self) -> List[Dict]:
        """What was promised to clients and when?"""
        action_items = self.db.query(ActionItem).filter(
            ActionItem.action_type == 'adviser_action',
            ActionItem.status.in_(['open', 'in_progress'])
        ).all()
        
        results = []
        for item in action_items:
            client = self.db.query(Client).filter_by(id=item.client_id).first()
            meeting = self.db.query(Meeting).filter_by(id=item.meeting_id).first() if item.meeting_id else None
            
            results.append({
                'action_item_id': item.id,
                'client_id': client.id if client else None,
                'client_name': client.name if client else 'Unknown',
                'title': item.title,
                'description': item.description,
                'promised_at': item.created_at.isoformat(),
                'due_date': item.due_date.isoformat() if item.due_date else None,
                'meeting_date': meeting.meeting_date.isoformat() if meeting else None,
                'status': item.status,
                'is_overdue': item.due_date and item.due_date < datetime.utcnow() if item.due_date else False,
            })
        
        return sorted(results, key=lambda x: x['promised_at'], reverse=True)
    
    # ========== BUSINESS INSIGHTS ==========
    
    def concerns_raised_this_month(self) -> Dict:
        """Concerns clients raised in meetings this month"""
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        
        meetings = self.db.query(Meeting).filter(
            Meeting.meeting_date >= start_of_month,
            Meeting.concerns_raised.isnot(None)
        ).all()
        
        concerns_count = {}
        for meeting in meetings:
            if meeting.concerns_raised:
                concerns = meeting.concerns_raised if isinstance(meeting.concerns_raised, list) else [meeting.concerns_raised]
                for concern in concerns:
                    concern_str = str(concern).lower()
                    concerns_count[concern_str] = concerns_count.get(concern_str, 0) + 1
        
        return {
            'month': start_of_month.strftime('%Y-%m'),
            'total_meetings': len(meetings),
            'concerns': sorted(concerns_count.items(), key=lambda x: x[1], reverse=True),
        }
    
    def highest_value_client_services(self) -> List[Dict]:
        """Which services do highest-value clients use most?"""
        return InsightsMock.highest_value_client_services()
    
    def conversion_rates_by_referral(self) -> List[Dict]:
        """Conversion rates from initial meeting to becoming a client by referral source"""
        return InsightsMock.conversion_rates_by_referral()
    
    def clients_approaching_retirement(self, years: int = 5) -> Dict:
        """What percentage of book is approaching retirement in next N years?"""
        return InsightsMock.clients_approaching_retirement(years)
    
    def most_efficient_clients(self) -> List[Dict]:
        """Clients generating most revenue but taking least time to service"""
        return InsightsMock.most_efficient_clients()
    
    def satisfied_long_term_clients(self, years: int = 5) -> List[Dict]:
        """What do most satisfied long-term clients have in common?"""
        return InsightsMock.satisfied_long_term_clients(years)
    
    # ========== FOLLOW-UP AND ACTIONS ==========
    
    def draft_follow_up_email(self, meeting_id: int) -> Dict:
        """Draft follow-up email for a meeting with key actions"""
        return InsightsMock.draft_follow_up_email(meeting_id)
    
    def waiting_on_information(self) -> List[Dict]:
        """Which clients are we waiting on for information or decisions?"""
        return InsightsMock.waiting_on_information()
    
    def all_open_action_items(self) -> List[Dict]:
        """Show all open action items across client base"""
        return InsightsMock.all_open_action_items()
    
    def overdue_follow_ups(self) -> List[Dict]:
        """Follow-ups that were committed to but are now overdue"""
        return InsightsMock.overdue_follow_ups()
    
    # ========== HELPER METHODS ==========
    
    def _get_expected_equity_for_risk(self, risk_profile: str) -> float:
        """Get expected equity allocation based on risk profile"""
        risk_map = {
            'conservative': 20,
            'moderate': 40,
            'balanced': 60,
            'growth': 80,
            'adventurous': 95,
        }
        return risk_map.get(risk_profile.lower(), 50)
    
    def _project_portfolio_value(self, current: float, annual_contribution: float, 
                                 growth_rate: float, years: float) -> float:
        """Simple portfolio projection"""
        future_value = current
        for _ in range(int(years)):
            future_value = future_value * (1 + growth_rate) + annual_contribution
        return future_value
    
    def _calculate_age(self, date_of_birth: datetime) -> Optional[int]:
        """Calculate age from date of birth"""
        if not date_of_birth:
            return None
        today = datetime.utcnow()
        return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    
    def _calculate_similarity_score(self, client1: Client, client2: Client) -> float:
        """Calculate similarity score between two clients (0-100)"""
        score = 0.0
        max_score = 0.0
        
        # Risk profile match (30 points)
        max_score += 30
        if client1.risk_profile == client2.risk_profile:
            score += 30
        
        # Portfolio value similarity (25 points)
        max_score += 25
        if client1.total_portfolio_value > 0 and client2.total_portfolio_value > 0:
            ratio = min(client1.total_portfolio_value, client2.total_portfolio_value) / max(client1.total_portfolio_value, client2.total_portfolio_value)
            score += 25 * ratio
        
        # Age similarity (20 points)
        max_score += 20
        age1 = self._calculate_age(client1.date_of_birth)
        age2 = self._calculate_age(client2.date_of_birth)
        if age1 and age2:
            age_diff = abs(age1 - age2)
            if age_diff <= 5:
                score += 20 * (1 - age_diff / 5)
        
        # Circumstances match (25 points)
        max_score += 25
        if client1.is_retired == client2.is_retired:
            score += 12.5
        if client1.is_business_owner == client2.is_business_owner:
            score += 12.5
        
        return round((score / max_score) * 100, 1) if max_score > 0 else 0.0
    
    def _calculate_acceptance_rate(self, recommendations: List[Dict]) -> float:
        """Calculate acceptance rate from recommendations list"""
        if not recommendations:
            return 0.0
        
        accepted = sum(1 for r in recommendations if r.get('status') in ['accepted', 'implemented'])
        return round((accepted / len(recommendations)) * 100, 1)
    
    # ========== NATURAL LANGUAGE QUERY SUPPORT ==========
    
    def process_natural_language_query(self, query: str) -> Dict:
        """
        Process natural language queries using agentic architecture with semantic tool matching
        Uses LangGraph with Azure OpenAI for intelligent query understanding
        """
        try:
            from agents.insights_agent import InsightsAgent
            agent = InsightsAgent(self.db, self.llm_service)
            result = agent.process_query(query)
            # If agentic system didn't find results, try fallback
            if result.get('count', 0) == 0 and not result.get('tools_used'):
                logger.info("Agentic system returned no results, trying fallback")
                return self._process_query_fallback(query)
            return result
        except ImportError:
            logger.warning("Agentic system not available, using fallback")
            return self._process_query_fallback(query)
        except Exception as e:
            logger.error(f"Error in agentic processing: {e}", exc_info=True)
            return self._process_query_fallback(query)
    
    def _process_query_fallback(self, query: str) -> Dict:
        """Fallback keyword-based query processing"""
        # Get available data context
        available_data = {
            'clients': self.db.query(Client).count(),
            'portfolios': self.db.query(InvestmentPortfolio).count(),
            'meetings': self.db.query(Meeting).count(),
            'recommendations': self.db.query(Recommendation).count(),
            'action_items': self.db.query(ActionItem).count(),
        }
        
        # Use LLM to parse query
        parsed = self.llm_service.process_natural_language_query(query, available_data)
        
        intent = parsed.get('intent', '').lower()
        parameters = parsed.get('parameters', {})
        
        # Route to appropriate method based on intent (fallback)
        results = []
        summary = None
        
        # Investment queries
        if 'equity' in intent or 'underweight' in intent or 'allocation' in intent:
            results = self.clients_underweight_equities()
        elif 'isa' in intent and 'allowance' in intent:
            results = self.clients_with_isa_allowance()
        elif 'annual' in intent and 'allowance' in intent:
            results = self.clients_with_annual_allowance()
        elif 'cash' in intent or 'excess' in intent:
            months = parameters.get('months', 6.0)
            results = self.clients_with_excess_cash(months_threshold=months)
        elif 'retirement' in intent and ('goal' in intent or 'shortfall' in intent):
            results = self.clients_missing_retirement_goals()
        elif 'protection' in intent and 'gap' in intent:
            results = self.clients_with_protection_gaps()
        elif 'withdrawal' in intent or 'withdraw' in intent:
            threshold = parameters.get('threshold', 4.0)
            results = self.retired_clients_high_withdrawal_rate(threshold=threshold)
        elif 'interest' in intent and 'rate' in intent:
            target_rate = parameters.get('target_rate', 3.0)
            results = self.clients_impacted_by_interest_rate_drop(target_rate=target_rate)
        elif 'market' in intent and ('correction' in intent or 'exposure' in intent):
            correction = parameters.get('correction_percentage', 20.0)
            results = self.clients_exposed_to_market_correction(correction_percentage=correction)
        elif 'long' in intent and 'term' in intent and 'care' in intent:
            client_name = parameters.get('client_name', query.split()[0] if query.split() else '')
            results = self.model_long_term_care_impact(client_name)
        elif 'retire' in intent and ('early' in intent or 'earlier' in intent):
            client_name = parameters.get('client_name', query.split()[0] if query.split() else '')
            new_year = parameters.get('new_retirement_year', None)
            if new_year:
                results = self.model_early_retirement_cashflow(client_name, new_year)
        
        # Proactive queries
        elif 'review' in intent or 'meeting' in intent:
            months = parameters.get('months', 12)
            results = self.clients_due_review(months_threshold=months)
        elif 'rd' in intent or 'r&d' in intent or 'research' in intent:
            results = self.business_owners_for_rd_tax_credits()
        elif 'university' in intent or 'education' in intent:
            years = parameters.get('years_ahead', 3)
            results = self.clients_with_children_approaching_university(years_ahead=years)
        elif 'estate' in intent or 'planning' in intent:
            threshold = parameters.get('threshold', 500000.0)
            results = self.high_net_worth_no_estate_planning(threshold=threshold)
        elif 'birthday' in intent:
            results = self.clients_with_birthdays_this_month()
        elif 'similar' in intent and 'profile' in intent:
            client_name = parameters.get('client_name', query.split()[-1] if query.split() else '')
            results = self.find_similar_client_profiles(client_name)
        elif 'life' in intent and 'event' in intent:
            results = self.clients_approaching_life_events()
        elif 'similar' in intent and ('case' in intent or 'success' in intent):
            client_name = parameters.get('client_name', query.split()[-1] if query.split() else '')
            results = self.clients_with_similar_successful_cases(client_name)
        
        # Compliance queries
        elif 'recommendation' in intent:
            client_name = parameters.get('client_name', query.split()[-1] if query.split() else '')
            results = self.recommendations_for_client(client_name)
        elif 'risk' in intent and 'discussion' in intent:
            client_name = parameters.get('client_name', query.split()[-1] if query.split() else '')
            results = self.risk_discussion_wording(client_name)
        elif 'document' in intent and ('waiting' in intent or 'pending' in intent):
            results = self.documents_waiting_from_clients()
        elif 'promise' in intent:
            results = self.promises_to_clients()
        elif 'sustainable' in intent or 'esg' in intent:
            results = self.sustainable_investing_discussions()
        elif 'pushback' in intent or 'rejection' in intent:
            results = self.analyze_recommendation_pushback()
        
        # Business queries
        elif 'concern' in intent:
            results = self.concerns_raised_this_month()
        elif 'conversion' in intent:
            results = self.conversion_rates_by_referral()
        elif 'efficient' in intent:
            results = self.most_efficient_clients()
        elif 'life' in intent and 'event' in intent and ('trigger' in intent or 'implement' in intent):
            results = self.life_events_triggering_recommendations()
        
        # Follow-up queries
        elif 'waiting' in intent or 'wait' in intent:
            results = self.waiting_on_information()
        elif 'action' in intent or 'follow' in intent:
            results = self.all_open_action_items()
        elif 'overdue' in intent:
            results = self.overdue_follow_ups()
        
        # Generate summary using LLM
        if results and self.llm_service:
            summary = self.llm_service.generate_insights_summary(query, results)
        
        return {
            'query': query,
            'intent': intent,
            'parameters': parameters,
            'results': results,
            'count': len(results) if isinstance(results, list) else 1,
            'summary': summary,
            'confidence': parsed.get('confidence', 0.0),
        }

