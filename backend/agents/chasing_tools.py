"""
Agentic Chasing Tools - Autonomous identification and prioritization of chase items
These tools help advisors identify what needs chasing, when, and how
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ========== Chasing Tool Input Schemas ==========

class LOAChaseQuery(BaseModel):
    """Query for LOAs that need chasing"""
    priority: Optional[str] = Field(default=None, description="Filter by priority: 'urgent', 'high', 'medium', 'low'")
    days_overdue: Optional[int] = Field(default=None, description="Minimum days overdue to include")
    provider_name: Optional[str] = Field(default=None, description="Filter by specific provider name")
    description: str = Field(description="Identifies Letters of Authority (LOAs) that need chasing. Critical for pension consolidation and transfer cases. Tracks LOAs sent to providers, expected response dates, and identifies which ones are overdue or stuck.")


class DocumentChaseQuery(BaseModel):
    """Query for client documents that need chasing"""
    document_type: Optional[str] = Field(default=None, description="Filter by document type: 'passport', 'payslip', 'pension_statement', etc.")
    days_waiting: Optional[int] = Field(default=None, description="Minimum days waiting to include")
    client_name: Optional[str] = Field(default=None, description="Filter by specific client name")
    description: str = Field(description="Identifies documents requested from clients that are still outstanding. Tracks what was requested, when, how many times it's been chased, and identifies which documents are blocking case progression.")


class PostAdviceChaseQuery(BaseModel):
    """Query for post-advice items that need chasing"""
    item_type: Optional[str] = Field(default=None, description="Filter by item type: 'signed_application', 'risk_questionnaire', 'aml_verification', etc.")
    priority: Optional[str] = Field(default=None, description="Filter by priority level")
    description: str = Field(description="Identifies post-advice items that need chasing after recommendations have been made. Includes signed application forms, risk questionnaires, AML verification, and authority to proceed confirmations.")


class StuckItemsQuery(BaseModel):
    """Query for items that are stuck and need escalation"""
    stuck_threshold_days: int = Field(default=30, description="Number of days to consider an item 'stuck'")
    description: str = Field(description="Identifies items that have been stuck for an extended period and may need escalation, alternative approaches, or provider contact. Helps prioritize items that are blocking case progression.")


class ChasePrioritizationQuery(BaseModel):
    """Query for prioritizing what to chase next"""
    limit: int = Field(default=10, description="Number of items to return")
    consider_client_value: bool = Field(default=True, description="Whether to factor in client value score when prioritizing")
    description: str = Field(description="Intelligently prioritizes all chase items across LOAs, documents, and post-advice items. Considers urgency, client value, days overdue, and case importance to recommend what should be chased next.")


class ProviderResponseTimeQuery(BaseModel):
    """Query for provider performance and response times"""
    provider_name: Optional[str] = Field(default=None, description="Filter by specific provider name")
    description: str = Field(description="Analyzes provider response times and reliability. Identifies which providers are consistently slow, which ones need escalation, and helps set realistic expectations for clients.")


class CaseBlockingItemsQuery(BaseModel):
    """Query for items blocking case progression"""
    case_id: Optional[int] = Field(default=None, description="Filter by specific case ID")
    case_type: Optional[str] = Field(default=None, description="Filter by case type: 'pension_consolidation', 'investment_advice', etc.")
    description: str = Field(description="Identifies all items (LOAs, documents, post-advice) that are blocking specific cases from progressing. Critical for case management and client communication.")


class ChaseHistoryQuery(BaseModel):
    """Query for chase history and patterns"""
    client_id: Optional[int] = Field(default=None, description="Filter by client ID")
    item_type: Optional[str] = Field(default=None, description="Filter by item type: 'loa', 'document', 'post_advice'")
    description: str = Field(description="Analyzes chase history to identify patterns. Shows which clients are consistently slow to respond, which providers are problematic, and helps optimize chase strategies.")


class AutonomousChaseRecommendationQuery(BaseModel):
    """Query for autonomous chase recommendations"""
    action_type: Optional[str] = Field(default=None, description="Filter by recommended action: 'email', 'sms', 'phone', 'escalate'")
    description: str = Field(description="Provides intelligent, autonomous recommendations for what to chase, when, and through which channel. Considers client preferences, urgency, previous chase attempts, and best practices.")


# ========== Tool Registry ==========

CHASING_TOOLS = {
    'identify_loas_needing_chase': {
        'schema': LOAChaseQuery,
        'category': 'chasing',
        'description': 'Identifies Letters of Authority (LOAs) that need chasing. Critical for pension consolidation cases where multiple LOAs are required. Tracks LOAs sent to providers, expected response dates, and identifies overdue items that need follow-up.'
    },
    'identify_documents_needing_chase': {
        'schema': DocumentChaseQuery,
        'category': 'chasing',
        'description': 'Identifies documents requested from clients that are still outstanding. Tracks what was requested, when, chase count, and identifies documents blocking case progression. Essential for fact-find completion.'
    },
    'identify_post_advice_items_needing_chase': {
        'schema': PostAdviceChaseQuery,
        'category': 'chasing',
        'description': 'Identifies post-advice items requiring follow-up after recommendations. Includes signed applications, risk questionnaires, AML verification, and authority to proceed. Critical for case completion.'
    },
    'find_stuck_items': {
        'schema': StuckItemsQuery,
        'category': 'chasing',
        'description': 'Identifies items that have been stuck for extended periods and may need escalation or alternative approaches. Helps prioritize items blocking case progression and client satisfaction.'
    },
    'prioritize_chase_items': {
        'schema': ChasePrioritizationQuery,
        'category': 'chasing',
        'description': 'Intelligently prioritizes all chase items across LOAs, documents, and post-advice. Considers urgency, client value, days overdue, and case importance to recommend what should be chased next. Essential for daily workflow management.'
    },
    'analyze_provider_performance': {
        'schema': ProviderResponseTimeQuery,
        'category': 'chasing',
        'description': 'Analyzes provider response times and reliability. Identifies slow providers, sets realistic client expectations, and helps decide when escalation is needed. Critical for managing provider relationships.'
    },
    'identify_case_blocking_items': {
        'schema': CaseBlockingItemsQuery,
        'category': 'chasing',
        'description': 'Identifies all items (LOAs, documents, post-advice) blocking specific cases from progressing. Essential for case management, client communication, and identifying bottlenecks.'
    },
    'analyze_chase_patterns': {
        'schema': ChaseHistoryQuery,
        'category': 'chasing',
        'description': 'Analyzes chase history to identify patterns. Shows which clients are consistently slow, which providers are problematic, and helps optimize chase strategies and communication approaches.'
    },
    'get_autonomous_chase_recommendations': {
        'schema': AutonomousChaseRecommendationQuery,
        'category': 'chasing',
        'description': 'Provides intelligent, autonomous recommendations for what to chase, when, and through which channel. Considers client preferences, urgency, previous attempts, and best practices. The core of autonomous chasing.'
    },
}

