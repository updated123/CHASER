"""
Data models for the Agentic Chaser system
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class ChaseType(str, Enum):
    LOA = "loa"
    CLIENT_DOCUMENT = "client_document"
    POST_ADVICE = "post_advice"
    WORKFLOW_ITEM = "workflow_item"  # Annual review workflow items
    PRE_MEETING_PACK = "pre_meeting_pack"  # Pre-meeting documents and questionnaires
    POST_MEETING_DOC = "post_meeting_doc"  # Post-meeting fact find updates


class ChaseStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RECEIVED = "received"
    OVERDUE = "overdue"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    STUCK = "stuck"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommunicationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"


# SQLAlchemy Models
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    client_value_score = Column(Float, default=1.0)  # For prioritization
    engagement_level = Column(String, default="medium")  # high, medium, low
    preferred_contact = Column(String, default="email")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Client circumstances
    date_of_birth = Column(DateTime)
    is_business_owner = Column(Boolean, default=False)
    business_type = Column(String)  # e.g., "limited_company", "sole_trader"
    marital_status = Column(String)  # single, married, divorced, widowed
    has_children = Column(Boolean, default=False)
    children_ages = Column(JSON)  # List of ages: [5, 8, 15]
    is_retired = Column(Boolean, default=False)
    retirement_date = Column(DateTime)
    target_retirement_date = Column(DateTime)
    target_retirement_income = Column(Float)  # Annual income goal
    
    # Risk profile
    risk_profile = Column(String)  # conservative, moderate, balanced, growth, adventurous
    risk_score = Column(Integer)  # 1-10
    time_horizon_years = Column(Integer)  # Investment time horizon
    
    # Financial summary
    total_portfolio_value = Column(Float, default=0.0)
    total_cash_holdings = Column(Float, default=0.0)
    monthly_expenditure = Column(Float, default=0.0)
    annual_income = Column(Float, default=0.0)
    
    # Allowances
    isa_allowance_used = Column(Float, default=0.0)  # Current tax year
    annual_allowance_used = Column(Float, default=0.0)  # Pension annual allowance
    tax_year = Column(Integer)  # Current tax year (e.g., 2024)
    
    # Client relationship
    last_review_date = Column(DateTime)
    next_review_due = Column(DateTime)
    satisfaction_score = Column(Float)  # 1-10
    referral_source = Column(String)  # Where they came from
    annual_revenue = Column(Float, default=0.0)  # Revenue from this client
    annual_service_time_hours = Column(Float, default=0.0)  # Time spent servicing
    
    # Estate planning
    has_estate_planning = Column(Boolean, default=False)
    has_will = Column(Boolean, default=False)
    has_lpa = Column(Boolean, default=False)  # Lasting Power of Attorney
    
    cases = relationship("Case", back_populates="client")
    communications = relationship("Communication", back_populates="client")
    portfolios = relationship("InvestmentPortfolio", back_populates="client")
    protection_policies = relationship("ProtectionPolicy", back_populates="client")
    meetings = relationship("Meeting", back_populates="client")
    recommendations = relationship("Recommendation", back_populates="client")
    action_items = relationship("ActionItem", back_populates="client")


class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    avg_response_days = Column(Integer, default=15)
    contact_email = Column(String)
    contact_phone = Column(String)
    reliability_score = Column(Float, default=0.7)  # 0-1, how often they respond on time
    created_at = Column(DateTime, default=datetime.utcnow)
    
    loas = relationship("LOA", back_populates="provider")


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    case_type = Column(String, nullable=False)  # pension_consolidation, investment_advice, annual_review, etc.
    status = Column(String, default="in_progress")
    priority = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    target_completion_date = Column(DateTime)
    
    # Workflow tracking for annual reviews
    workflow_stage = Column(String)  # pre_meeting, meeting, suitability, advice_implementation
    workflow_substage = Column(String)  # pack_prep, pack_signoff, client_responses, fact_find_update, loa_collection, suitability_letter
    
    client = relationship("Client", back_populates="cases")
    loas = relationship("LOA", back_populates="case")
    document_requests = relationship("DocumentRequest", back_populates="case")
    post_advice_items = relationship("PostAdviceItem", back_populates="case")
    recommendations = relationship("Recommendation", back_populates="case")
    action_items = relationship("ActionItem", back_populates="case")
    workflow_items = relationship("WorkflowItem", back_populates="case")


class LOA(Base):
    __tablename__ = "loas"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    sent_to_client_at = Column(DateTime)
    received_from_client_at = Column(DateTime)
    sent_to_provider_at = Column(DateTime)
    expected_response_date = Column(DateTime)
    actual_response_date = Column(DateTime)
    chase_count = Column(Integer, default=0)
    last_chased_at = Column(DateTime)
    stuck_score = Column(Float, default=0.0)  # ML-like score for bottleneck prediction
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("Case", back_populates="loas")
    provider = relationship("Provider", back_populates="loas")


class DocumentRequest(Base):
    __tablename__ = "document_requests"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    document_type = Column(String, nullable=False)  # passport, payslip, pension_statement, etc.
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    requested_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    chase_count = Column(Integer, default=0)
    last_chased_at = Column(DateTime)
    stuck_score = Column(Float, default=0.0)
    notes = Column(Text)
    
    case = relationship("Case", back_populates="document_requests")


class PostAdviceItem(Base):
    __tablename__ = "post_advice_items"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    item_type = Column(String, nullable=False)  # signed_application, risk_questionnaire, etc.
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    requested_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    chase_count = Column(Integer, default=0)
    last_chased_at = Column(DateTime)
    stuck_score = Column(Float, default=0.0)
    notes = Column(Text)
    
    case = relationship("Case", back_populates="post_advice_items")


class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    chase_type = Column(String, nullable=False)
    chase_id = Column(Integer, nullable=False)  # ID of LOA, DocumentRequest, or PostAdviceItem
    channel = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # outbound, inbound
    subject = Column(String)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    response_received = Column(Boolean, default=False)
    
    client = relationship("Client", back_populates="communications")


class InvestmentPortfolio(Base):
    __tablename__ = "investment_portfolios"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "ISA Portfolio", "SIPP"
    portfolio_type = Column(String, nullable=False)  # isa, sipp, gia, pension
    platform = Column(String)  # Platform name
    total_value = Column(Float, default=0.0)
    
    # Asset allocation
    equity_percentage = Column(Float, default=0.0)
    bond_percentage = Column(Float, default=0.0)
    cash_percentage = Column(Float, default=0.0)
    property_percentage = Column(Float, default=0.0)
    other_percentage = Column(Float, default=0.0)
    
    # Allowances
    isa_allowance_used = Column(Float, default=0.0)  # For ISA portfolios
    annual_allowance_used = Column(Float, default=0.0)  # For pension portfolios
    
    last_valuation_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="portfolios")


class ProtectionPolicy(Base):
    __tablename__ = "protection_policies"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    policy_type = Column(String, nullable=False)  # life_insurance, critical_illness, income_protection, etc.
    provider = Column(String)
    sum_assured = Column(Float)
    monthly_premium = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default="active")  # active, lapsed, cancelled
    notes = Column(Text)
    
    client = relationship("Client", back_populates="protection_policies")


class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    meeting_type = Column(String, nullable=False)  # annual_review, initial_meeting, ad_hoc, etc.
    meeting_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    location = Column(String)  # office, client_home, video_call, phone
    
    # Meeting content
    notes = Column(Text)
    transcript = Column(Text)  # Full conversation transcript if available
    concerns_raised = Column(JSON)  # List of concerns mentioned
    topics_discussed = Column(JSON)  # List of topics
    
    # Outcomes
    recommendations_made = Column(JSON)  # List of recommendation IDs
    action_items_created = Column(JSON)  # List of action item IDs
    next_meeting_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="meetings")


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    
    recommendation_type = Column(String, nullable=False)  # investment, pension, protection, platform, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)  # Why this recommendation was made
    exact_wording = Column(Text)  # Exact wording used when discussing
    
    # Status
    status = Column(String, default="pending")  # pending, accepted, rejected, implemented, deferred
    client_response = Column(String)  # What client said
    implementation_date = Column(DateTime)
    
    # Context
    platform_recommended = Column(String)  # If recommending a platform
    product_recommended = Column(String)  # Product name if applicable
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="recommendations")
    case = relationship("Case", back_populates="recommendations")


class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    action_type = Column(String, nullable=False)  # client_action, adviser_action, follow_up, etc.
    
    # Status
    status = Column(String, default="open")  # open, in_progress, completed, overdue, cancelled
    priority = Column(String, default="medium")
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Assignment
    assigned_to = Column(String)  # client, adviser, or specific person
    waiting_on = Column(String)  # Who we're waiting on: client, provider, etc.
    
    # Follow-up
    follow_up_email_drafted = Column(Boolean, default=False)
    follow_up_email_content = Column(Text)
    
    client = relationship("Client", back_populates="action_items")
    case = relationship("Case", back_populates="action_items")


class WorkflowItem(Base):
    """Tracks items needed at different workflow stages"""
    __tablename__ = "workflow_items"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    
    # Workflow context
    workflow_stage = Column(String, nullable=False)  # pre_meeting, meeting, suitability, advice_implementation
    workflow_substage = Column(String)  # pack_prep, pack_signoff, client_responses, fact_find_update, loa_collection
    item_type = Column(String, nullable=False)  # pre_meeting_doc, questionnaire, pack_signoff, fact_find_update, loa_required, suitability_letter
    
    # Item details
    item_name = Column(String, nullable=False)  # e.g., "Expenditure Questionnaire", "ATR Questionnaire", "LOA for Aviva"
    description = Column(Text)
    required_for = Column(String)  # What this is needed for: "pack_prep", "suitability_letter", etc.
    
    # Status
    status = Column(String, default="pending")  # pending, requested, received, overdue
    priority = Column(String, default="medium")
    
    # Timing
    requested_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime)
    due_date = Column(DateTime)
    
    # Chasing
    chase_count = Column(Integer, default=0)
    last_chased_at = Column(DateTime)
    stuck_score = Column(Float, default=0.0)
    
    # Provider context (for LOAs)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    provider_name = Column(String)  # e.g., "Aviva", "AJ Bell"
    
    # Notes
    notes = Column(Text)
    
    case = relationship("Case", back_populates="workflow_items")
    provider = relationship("Provider")


# Pydantic Models for API
class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    client_value_score: float
    engagement_level: str
    
    class Config:
        from_attributes = True


class ChaseItemResponse(BaseModel):
    id: int
    chase_type: str
    status: str
    priority: str
    chase_count: int
    stuck_score: float
    days_overdue: Optional[int]
    next_chase_due: Optional[datetime]
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_active_chases: int
    overdue_items: int
    items_needing_chase: int
    avg_days_stuck: float
    high_priority_items: int
    predicted_bottlenecks: int

