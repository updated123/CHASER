"""
LangGraph-based Insights Tools - Structured tool definitions for intelligent query routing
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


# ========== Tool Input Schemas ==========

class EquityAllocationQuery(BaseModel):
    """Query for clients with equity allocation issues"""
    description: str = Field(description="Analyze clients whose equity allocation is below their risk profile expectations. Identifies investment opportunities where portfolios need rebalancing to match risk tolerance and time horizon.")


class AllowanceQuery(BaseModel):
    """Query for tax allowance availability"""
    allowance_type: str = Field(description="Type of allowance: 'isa' for ISA allowance, 'annual' for pension annual allowance")
    description: str = Field(description="Find clients who have remaining tax allowances available for the current tax year. Helps identify opportunities for tax-efficient investments.")


class CashAnalysisQuery(BaseModel):
    """Query for excess cash analysis"""
    months_threshold: float = Field(default=6.0, description="Number of months of expenditure to use as threshold (default: 6 months)")
    description: str = Field(description="Identify clients holding excess cash above their emergency fund needs. Helps find opportunities to discuss investment strategies for cash reserves.")


class RetirementGoalQuery(BaseModel):
    """Query for retirement goal shortfalls"""
    description: str = Field(description="Analyze clients whose current investment trajectory will not meet their stated retirement income goals. Identifies clients needing portfolio adjustments or additional contributions.")


class ProtectionGapQuery(BaseModel):
    """Query for protection coverage gaps"""
    description: str = Field(description="Identify clients with insufficient protection coverage based on their family circumstances, dependents, and financial obligations. Critical for risk management.")


class WithdrawalRateQuery(BaseModel):
    """Query for retirement withdrawal rates"""
    threshold: float = Field(default=4.0, description="Withdrawal rate percentage threshold (default: 4.0%)")
    description: str = Field(description="Find retired clients taking unsustainable withdrawal rates that may deplete their retirement savings prematurely.")


class InterestRateImpactQuery(BaseModel):
    """Query for interest rate impact modeling"""
    target_rate: float = Field(description="Target interest rate to model (e.g., 3.0 for 3%)")
    description: str = Field(description="Model the financial impact on clients if interest rates change to a specified level. Analyzes fixed-income holdings, mortgages, and savings.")


class MarketCorrectionQuery(BaseModel):
    """Query for market correction exposure"""
    correction_percentage: float = Field(default=20.0, description="Market correction percentage to model (default: 20%)")
    description: str = Field(description="Identify clients most exposed to market volatility and model portfolio impact of a market correction. Helps with risk management conversations.")


class LongTermCareQuery(BaseModel):
    """Query for long-term care impact modeling"""
    client_name: str = Field(description="Full name of the client or family to analyze")
    description: str = Field(description="Model the financial impact on a client's retirement plan if long-term care is needed. Analyzes care costs, asset depletion, and family financial security.")


class EarlyRetirementQuery(BaseModel):
    """Query for early retirement cashflow modeling"""
    client_name: str = Field(description="Full name of the client to analyze")
    new_retirement_year: Optional[int] = Field(default=None, description="New retirement year to model (if different from planned)")
    description: str = Field(description="Model cashflow and financial viability if a client retires earlier than planned. Analyzes income sources, expenses, and portfolio sustainability.")


class ReviewDueQuery(BaseModel):
    """Query for clients due for reviews"""
    months_threshold: int = Field(default=12, description="Months since last review to use as threshold (default: 12)")
    description: str = Field(description="Find clients who haven't had a review meeting in the specified number of months. Critical for compliance and relationship management.")


class RDTCreditQuery(BaseModel):
    """Query for R&D tax credit opportunities"""
    description: str = Field(description="Identify business owner clients who might benefit from R&D tax credit changes. Helps identify tax planning opportunities.")


class UniversityPlanningQuery(BaseModel):
    """Query for university education planning"""
    years_ahead: int = Field(default=3, description="Years ahead to look for children approaching university age (default: 3)")
    description: str = Field(description="Find clients with children approaching university age who don't have education funding plans in place.")


class EstatePlanningQuery(BaseModel):
    """Query for estate planning gaps"""
    threshold: float = Field(default=500000.0, description="Net worth threshold in GBP (default: £500,000)")
    description: str = Field(description="Identify high-net-worth clients without comprehensive estate planning. Critical for inheritance tax planning and wealth transfer.")


class BirthdayQuery(BaseModel):
    """Query for client birthdays"""
    description: str = Field(description="Find all clients with birthdays in the current month. Helps with relationship building and proactive outreach.")


class SimilarProfileQuery(BaseModel):
    """Query for similar client profiles"""
    client_name: str = Field(description="Reference client name to find similar profiles")
    description: str = Field(description="Find clients with similar financial profiles, circumstances, and goals to a reference client. Useful for identifying best practices and opportunities.")


class LifeEventQuery(BaseModel):
    """Query for approaching life events"""
    description: str = Field(description="Identify clients approaching significant life events (retirement, children leaving home, inheritance, etc.) that may require financial planning adjustments.")


class RecommendationQuery(BaseModel):
    """Query for client recommendations"""
    client_name: str = Field(description="Full name of the client")
    description: str = Field(description="Retrieve all recommendations made to a specific client, including rationale and implementation status. Critical for compliance and follow-up.")


class RiskDiscussionQuery(BaseModel):
    """Query for risk discussion records"""
    client_name: str = Field(description="Full name of the client or family")
    description: str = Field(description="Retrieve exact wording and documentation of risk discussions with clients. Essential for compliance and demonstrating suitability.")


class PlatformRecommendationQuery(BaseModel):
    """Query for platform recommendations"""
    platform_name: str = Field(description="Name of the platform (e.g., 'Platform X', 'Hargreaves Lansdown')")
    description: str = Field(description="Find all clients where a specific platform was recommended and the reasoning behind each recommendation.")


class ConcernDiscussionQuery(BaseModel):
    """Query for concern discussions"""
    concern: str = Field(description="Topic of concern (e.g., 'market volatility', 'inflation', 'pension security')")
    description: str = Field(description="Find all client conversations that mentioned specific concerns. Helps understand client sentiment and common worries.")


class DocumentsWaitingQuery(BaseModel):
    """Query for pending documents"""
    description: str = Field(description="List all documents still waiting to be received from clients. Critical for case progression and compliance.")


class PromisesQuery(BaseModel):
    """Query for promises made to clients"""
    description: str = Field(description="Track all promises made to clients including what was promised and when. Essential for follow-up and relationship management.")


class SustainableInvestingQuery(BaseModel):
    """Query for sustainable investing discussions"""
    description: str = Field(description="Generate summary of all discussions about sustainable investing preferences with clients. Helps understand ESG interest across client base.")


class PushbackAnalysisQuery(BaseModel):
    """Query for recommendation pushback analysis"""
    description: str = Field(description="Analyze which types of recommendations get the most pushback from clients and understand the reasons. Helps improve recommendation strategies.")


class ConcernsThisMonthQuery(BaseModel):
    """Query for recent client concerns"""
    description: str = Field(description="Identify concerns and worries clients raised in meetings this month. Helps understand current client sentiment and common issues.")


class ServiceUsageQuery(BaseModel):
    """Query for service usage patterns"""
    description: str = Field(description="Analyze which services are used most by highest-value clients. Helps understand service value and identify upsell opportunities.")


class ConversionRateQuery(BaseModel):
    """Query for conversion rate analysis"""
    description: str = Field(description="Analyze conversion rates from initial meeting to becoming a client, broken down by referral source. Helps optimize marketing and referral strategies.")


class RetirementDemographicsQuery(BaseModel):
    """Query for retirement demographics"""
    years_ahead: int = Field(default=5, description="Years ahead to analyze (default: 5)")
    description: str = Field(description="Analyze what percentage of the client book is approaching retirement in the specified timeframe. Critical for business planning.")


class ClientEfficiencyQuery(BaseModel):
    """Query for client efficiency metrics"""
    description: str = Field(description="Identify clients who generate the most revenue but require the least time to service. Helps optimize client portfolio and identify ideal client profiles.")


class SatisfactionPatternQuery(BaseModel):
    """Query for client satisfaction patterns"""
    years: int = Field(default=5, description="Minimum years as client (default: 5)")
    description: str = Field(description="Analyze what characteristics and factors are common among most satisfied long-term clients. Helps identify best practices.")


class LifeEventTriggerQuery(BaseModel):
    """Query for life events triggering implementation"""
    description: str = Field(description="Identify which life events most commonly trigger clients to actually implement recommendations. Helps with timing and approach strategies.")


class WaitingOnQuery(BaseModel):
    """Query for items waiting on clients"""
    description: str = Field(description="List all items where we are waiting for information or decisions from clients. Critical for case management and follow-up.")


class ActionItemsQuery(BaseModel):
    """Query for all open action items"""
    description: str = Field(description="Retrieve all open action items across the entire client base. Provides comprehensive view of pending tasks and follow-ups.")


class OverdueFollowUpsQuery(BaseModel):
    """Query for overdue follow-ups"""
    description: str = Field(description="Find all follow-up commitments that are now overdue. Critical for relationship management and compliance.")


class CashflowModellingQuery(BaseModel):
    """Query for cashflow modelling opportunities"""
    description: str = Field(description="Identify pension clients who might benefit from cashflow modelling service. Helps identify clients who need detailed retirement planning analysis.")


class ProtectionCoverageQuery(BaseModel):
    """Query for protection coverage gaps"""
    description: str = Field(description="Find clients with investment portfolios but no protection cover (life insurance, critical illness, income protection). Critical for comprehensive financial planning.")


class ExitPlanningQuery(BaseModel):
    """Query for exit planning discussions"""
    description: str = Field(description="Identify business owner clients who haven't discussed exit planning. Important for succession planning and business value maximization.")


class FollowUpEmailQuery(BaseModel):
    """Query for drafting follow-up emails"""
    meeting_id: Optional[int] = Field(default=None, description="Meeting ID to draft email for. If not provided, uses most recent meeting.")
    meeting_date: Optional[str] = Field(default=None, description="Date of meeting in YYYY-MM-DD format (alternative to meeting_id)")
    description: str = Field(description="Draft a professional follow-up email for a meeting with key actions agreed. Includes meeting summary, action items, and next steps.")


class SimilarSuccessfulCasesQuery(BaseModel):
    """Query for similar successful cases"""
    client_name: str = Field(description="Reference client name to find similar successful cases")
    description: str = Field(description="Find clients whose circumstances are similar to cases where significant value was added. Helps identify opportunities to replicate successful strategies.")


# ========== Tool Registry ==========

INSIGHTS_TOOLS = {
    # Investment Insights
    'analyze_equity_allocation': {
        'schema': EquityAllocationQuery,
        'category': 'investment',
        'description': 'Find clients who are underweight in equities relative to their risk profile and time horizon. Identifies portfolios needing rebalancing to match risk tolerance.'
    },
    'check_allowance_availability': {
        'schema': AllowanceQuery,
        'category': 'investment',
        'description': 'Show clients with ISA allowance or pension annual allowance still available this tax year. Helps identify tax-efficient investment opportunities.'
    },
    'analyze_excess_cash': {
        'schema': CashAnalysisQuery,
        'category': 'investment',
        'description': 'Identify clients holding excess cash above emergency fund needs'
    },
    'analyze_retirement_goals': {
        'schema': RetirementGoalQuery,
        'category': 'investment',
        'description': 'Flag clients where current investment trajectory won\'t meet their stated retirement income goals. Identifies clients needing portfolio adjustments or additional contributions.'
    },
    'identify_protection_gaps': {
        'schema': ProtectionGapQuery,
        'category': 'investment',
        'description': 'Identify clients with insufficient protection coverage'
    },
    'analyze_withdrawal_rates': {
        'schema': WithdrawalRateQuery,
        'category': 'investment',
        'description': 'Find retired clients with unsustainable withdrawal rates'
    },
    'model_interest_rate_impact': {
        'schema': InterestRateImpactQuery,
        'category': 'investment',
        'description': 'Model financial impact of interest rate changes on clients'
    },
    'analyze_market_correction_exposure': {
        'schema': MarketCorrectionQuery,
        'category': 'investment',
        'description': 'Identify clients most exposed to market volatility'
    },
    'model_long_term_care_impact': {
        'schema': LongTermCareQuery,
        'category': 'investment',
        'description': 'Model financial impact of long-term care needs'
    },
    'model_early_retirement': {
        'schema': EarlyRetirementQuery,
        'category': 'investment',
        'description': 'Model cashflow if client retires earlier than planned'
    },
    
    # Proactive Insights
    'find_review_due_clients': {
        'schema': ReviewDueQuery,
        'category': 'proactive',
        'description': 'Find clients who haven\'t had a review meeting in over the specified number of months. Critical for compliance (annual reviews required) and relationship management.'
    },
    'identify_rd_tax_credit_opportunities': {
        'schema': RDTCreditQuery,
        'category': 'proactive',
        'description': 'Identify business owners who might benefit from R&D tax credits'
    },
    'find_university_planning_needs': {
        'schema': UniversityPlanningQuery,
        'category': 'proactive',
        'description': 'Find clients needing education funding planning'
    },
    'identify_estate_planning_gaps': {
        'schema': EstatePlanningQuery,
        'category': 'proactive',
        'description': 'Identify high-net-worth clients without estate planning'
    },
    'find_birthday_clients': {
        'schema': BirthdayQuery,
        'category': 'proactive',
        'description': 'Find clients with birthdays this month'
    },
    'find_similar_profiles': {
        'schema': SimilarProfileQuery,
        'category': 'proactive',
        'description': 'Find clients with similar financial profiles, circumstances, and goals to a reference client. Useful for identifying best practices and opportunities based on successful cases.'
    },
    'identify_life_events': {
        'schema': LifeEventQuery,
        'category': 'proactive',
        'description': 'Identify clients approaching significant life events'
    },
    
    # Compliance Insights
    'get_client_recommendations': {
        'schema': RecommendationQuery,
        'category': 'compliance',
        'description': 'Pull every recommendation made to a specific client including the rationale given. Critical for compliance and demonstrating suitability.'
    },
    'get_risk_discussion_wording': {
        'schema': RiskDiscussionQuery,
        'category': 'compliance',
        'description': 'Retrieve exact wording when discussing risk with a client or family. Essential for compliance and demonstrating that risk was properly explained.'
    },
    'get_platform_recommendations': {
        'schema': PlatformRecommendationQuery,
        'category': 'compliance',
        'description': 'Find clients where a platform was recommended'
    },
    'find_concern_discussions': {
        'schema': ConcernDiscussionQuery,
        'category': 'compliance',
        'description': 'Find all client conversations that mentioned concerns about a specific topic (e.g., market volatility, inflation, pension security). Helps understand client sentiment.'
    },
    'list_documents_waiting': {
        'schema': DocumentsWaitingQuery,
        'category': 'compliance',
        'description': 'List all documents waiting from clients'
    },
    'track_promises_to_clients': {
        'schema': PromisesQuery,
        'category': 'compliance',
        'description': 'Track all promises made to clients'
    },
    'summarize_sustainable_investing': {
        'schema': SustainableInvestingQuery,
        'category': 'compliance',
        'description': 'Summarize sustainable investing discussions'
    },
    'analyze_recommendation_pushback': {
        'schema': PushbackAnalysisQuery,
        'category': 'compliance',
        'description': 'Analyze which recommendations get pushback'
    },
    
    # Business Insights
    'get_concerns_this_month': {
        'schema': ConcernsThisMonthQuery,
        'category': 'business',
        'description': 'Identify concerns and worries clients raised in meetings this month. Helps understand current client sentiment and common issues affecting clients.'
    },
    'analyze_service_usage': {
        'schema': ServiceUsageQuery,
        'category': 'business',
        'description': 'Analyze service usage by highest-value clients'
    },
    'analyze_conversion_rates': {
        'schema': ConversionRateQuery,
        'category': 'business',
        'description': 'Analyze conversion rates by referral source'
    },
    'analyze_retirement_demographics': {
        'schema': RetirementDemographicsQuery,
        'category': 'business',
        'description': 'Analyze retirement demographics of client book'
    },
    'identify_efficient_clients': {
        'schema': ClientEfficiencyQuery,
        'category': 'business',
        'description': 'Identify most efficient clients (high revenue, low time)'
    },
    'analyze_satisfaction_patterns': {
        'schema': SatisfactionPatternQuery,
        'category': 'business',
        'description': 'Analyze patterns of satisfied long-term clients'
    },
    'identify_life_event_triggers': {
        'schema': LifeEventTriggerQuery,
        'category': 'business',
        'description': 'Identify which life events most commonly trigger clients to actually implement recommendations. Helps with timing and approach strategies for future recommendations.'
    },
    
    # Follow-up Insights
    'list_waiting_on_clients': {
        'schema': WaitingOnQuery,
        'category': 'followup',
        'description': 'List items waiting for client information or decisions'
    },
    'get_all_action_items': {
        'schema': ActionItemsQuery,
        'category': 'followup',
        'description': 'Get all open action items across client base'
    },
    'find_overdue_follow_ups': {
        'schema': OverdueFollowUpsQuery,
        'category': 'followup',
        'description': 'Find overdue follow-up commitments'
    },
    'identify_cashflow_modelling_opportunities': {
        'schema': CashflowModellingQuery,
        'category': 'proactive',
        'description': 'Identify pension clients who might benefit from cashflow modelling service'
    },
    'identify_protection_coverage_gaps': {
        'schema': ProtectionCoverageQuery,
        'category': 'proactive',
        'description': 'Find clients with investment portfolios but no protection cover'
    },
    'identify_exit_planning_needs': {
        'schema': ExitPlanningQuery,
        'category': 'proactive',
        'description': 'Identify business owner clients who haven\'t discussed exit planning'
    },
    'draft_follow_up_email': {
        'schema': FollowUpEmailQuery,
        'category': 'followup',
        'description': 'Draft professional follow-up email for a meeting with key actions and next steps'
    },
    'find_similar_successful_cases': {
        'schema': SimilarSuccessfulCasesQuery,
        'category': 'business',
        'description': 'Find clients with similar circumstances to cases where significant value was added'
    },
}

