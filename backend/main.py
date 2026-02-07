"""
FastAPI main application for Agentic Chaser
"""
import os
import logging
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict
import uvicorn

from mock_db import get_db, init_db
from models import Client, LOA, DocumentRequest, PostAdviceItem, Case
from agents.orchestrator import AgentOrchestrator
from agents.langgraph_orchestrator import LangGraphOrchestrator
from agents.analytics import AnalyticsEngine
from agents.insights_engine import InsightsEngine
from agents.workflow_intelligence import WorkflowIntelligence
from agents.llm_service import LLMService
from models import WorkflowItem
from mock_data_service import MockDataService

# Use mock data if USE_MOCK_DATA is set
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific log levels
logging.getLogger("agents.llm_service").setLevel(logging.DEBUG)
logging.getLogger("agents.orchestrator").setLevel(logging.INFO)
logging.getLogger("agents.base_agent").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Chaser API", version="1.0.0")

logger.info("=" * 60)
logger.info("Agentic Chaser API Starting")
logger.info("=" * 60)

# CORS middleware for frontend
# Get allowed origins from environment variable (comma-separated)
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Running in MOCK DATA mode - No database connection required")
    logger.info("=" * 60)
    logger.info("All endpoints use MockDataService for data")
    logger.info("LLM Service will be initialized on-demand")


@app.get("/")
async def root():
    return {"message": "Agentic Chaser API", "version": "1.0.0"}


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    logger.info("[API] GET /api/dashboard/stats - Using mock data")
    return MockDataService.get_dashboard_stats()


@app.get("/api/chases/active")
async def get_active_chases(
    chase_type: str = None,
    priority: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get all active chases with filtering"""
    logger.info(f"[API] GET /api/chases/active - Using mock data (filters: type={chase_type}, priority={priority}, status={status})")
    result = MockDataService.get_active_chases()
    # Apply filters
    if chase_type:
        result['items'] = [item for item in result['items'] if item['chase_type'] == chase_type]
    if priority:
        result['items'] = [item for item in result['items'] if item['priority'] == priority]
    if status:
        result['items'] = [item for item in result['items'] if item['status'] == status]
    result['count'] = len(result['items'])
    return result
    
    # All data comes from mock service - no database needed
    pass


def _format_item_details(item: Dict, chase_type) -> Dict:
    """Format item-specific details"""
    if chase_type.value == 'loa':
        return {
            'provider_name': item.get('provider_name'),
            'expected_response_date': item.get('expected_response_date').isoformat() if item.get('expected_response_date') else None,
        }
    elif chase_type.value == 'client_document':
        return {
            'document_type': item.get('document_type'),
        }
    elif chase_type.value == 'post_advice':
        return {
            'item_type': item.get('item_type'),
        }
    return {}


@app.post("/api/agents/run-cycle")
async def run_autonomous_cycle(use_langgraph: bool = True, db: Session = Depends(get_db)):
    """Manually trigger an autonomous chasing cycle"""
    logger.info("=" * 60)
    logger.info(f"[API] POST /api/agents/run-cycle - Using mock data")
    logger.info("=" * 60)
    return MockDataService.run_autonomous_cycle()


@app.get("/api/clients")
async def get_clients(db: Session = Depends(get_db)):
    """Get all clients"""
    logger.info("[API] GET /api/clients - Using mock data")
    return MockDataService.get_clients()


@app.get("/api/cases")
async def get_cases(client_id: int = None, db: Session = Depends(get_db)):
    """Get all cases, optionally filtered by client"""
    logger.info(f"[API] GET /api/cases - Using mock data (client_id={client_id})")
    return MockDataService.get_cases(client_id)


@app.get("/api/communications")
async def get_communications(
    client_id: int = None,
    chase_type: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get communication history"""
    logger.info(f"[API] GET /api/communications - Using mock data")
    # Return empty list for communications - not critical for testing
    return []


@app.get("/api/analytics/bottlenecks")
async def get_predicted_bottlenecks(
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """Get predicted bottlenecks"""
    analytics = AnalyticsEngine(db)
    bottlenecks = analytics.predict_bottlenecks(days_ahead)
    return {'bottlenecks': bottlenecks, 'count': len(bottlenecks)}


@app.get("/api/analytics/case-velocity/{case_id}")
async def get_case_velocity(case_id: int, db: Session = Depends(get_db)):
    """Get case velocity metrics"""
    analytics = AnalyticsEngine(db)
    velocity = analytics.calculate_case_velocity(case_id)
    if not velocity:
        raise HTTPException(status_code=404, detail="Case not found")
    return velocity


@app.get("/api/analytics/provider-performance")
async def get_provider_performance(db: Session = Depends(get_db)):
    """Get provider performance metrics"""
    analytics = AnalyticsEngine(db)
    performance = analytics.get_provider_performance()
    return {'providers': performance}


# ========== INSIGHTS API ENDPOINTS ==========

@app.get("/api/insights/investments/underweight-equities")
async def get_underweight_equities(db: Session = Depends(get_db)):
    """Which clients are underweight in equities relative to their risk profile?"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_underweight_equities()}


@app.get("/api/insights/investments/isa-allowance")
async def get_isa_allowance_available(db: Session = Depends(get_db)):
    """Show clients with ISA allowance still available this tax year"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_isa_allowance()}


@app.get("/api/insights/investments/annual-allowance")
async def get_annual_allowance_available(db: Session = Depends(get_db)):
    """Show clients with pension annual allowance still available"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_annual_allowance()}


@app.get("/api/insights/investments/excess-cash")
async def get_excess_cash(months: float = 6.0, db: Session = Depends(get_db)):
    """Clients with cash excess above threshold months of expenditure"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_excess_cash(months_threshold=months)}


@app.get("/api/insights/investments/retirement-goals")
async def get_retirement_goals_shortfall(db: Session = Depends(get_db)):
    """Clients where current trajectory won't meet retirement income goals"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_missing_retirement_goals()}


@app.get("/api/insights/investments/protection-gaps")
async def get_protection_gaps(db: Session = Depends(get_db)):
    """Clients with protection gaps based on family circumstances"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_protection_gaps()}


@app.get("/api/insights/investments/high-withdrawal-rate")
async def get_high_withdrawal_rate(threshold: float = 4.0, db: Session = Depends(get_db)):
    """Retired clients taking more than threshold % withdrawal rate"""
    logger.info(f"[API] GET /api/insights/investments/high-withdrawal-rate (threshold: {threshold})")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.retired_clients_high_withdrawal_rate(threshold=threshold)}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/investments/interest-rate-impact")
async def get_interest_rate_impact(target_rate: float = 3.0, db: Session = Depends(get_db)):
    """Show clients who would be impacted if interest rates drop to target_rate"""
    logger.info(f"[API] GET /api/insights/investments/interest-rate-impact (target_rate: {target_rate})")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.clients_impacted_by_interest_rate_drop(target_rate=target_rate)}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/investments/market-correction-exposure")
async def get_market_correction_exposure(correction_percentage: float = 20.0, db: Session = Depends(get_db)):
    """Which clients are most exposed if we see a market correction?"""
    logger.info(f"[API] GET /api/insights/investments/market-correction-exposure ({correction_percentage}%)")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.clients_exposed_to_market_correction(correction_percentage=correction_percentage)}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/investments/long-term-care-impact/{client_name}")
async def get_long_term_care_impact(client_name: str, db: Session = Depends(get_db)):
    """Model what happens to a family's plan if one needs long-term care"""
    logger.info(f"[API] GET /api/insights/investments/long-term-care-impact/{client_name}")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        result = engine.model_long_term_care_impact(client_name)
        if not result:
            raise HTTPException(status_code=404, detail="Client not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/investments/early-retirement-cashflow/{client_name}")
async def get_early_retirement_cashflow(client_name: str, new_retirement_year: int, db: Session = Depends(get_db)):
    """Model cashflow if client retires earlier than planned"""
    logger.info(f"[API] GET /api/insights/investments/early-retirement-cashflow/{client_name} (year: {new_retirement_year})")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        result = engine.model_early_retirement_cashflow(client_name, new_retirement_year)
        if not result:
            raise HTTPException(status_code=404, detail="Client not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/proactive/due-review")
async def get_clients_due_review(months: int = 12, db: Session = Depends(get_db)):
    """Clients who haven't had a review in over threshold months"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_due_review(months_threshold=months)}


@app.get("/api/insights/proactive/business-owners-rd")
async def get_business_owners_rd(db: Session = Depends(get_db)):
    """Business owners who might benefit from R&D tax credit changes"""
    engine = InsightsEngine(db)
    return {'clients': engine.business_owners_for_rd_tax_credits()}


@app.get("/api/insights/proactive/university-planning")
async def get_university_planning(years_ahead: int = 3, db: Session = Depends(get_db)):
    """Clients with children approaching university age but no education planning"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_children_approaching_university(years_ahead=years_ahead)}


@app.get("/api/insights/proactive/hnw-no-estate-planning")
async def get_hnw_no_estate_planning(threshold: float = 500000.0, db: Session = Depends(get_db)):
    """High-net-worth clients without estate planning"""
    engine = InsightsEngine(db)
    return {'clients': engine.high_net_worth_no_estate_planning(threshold=threshold)}


@app.get("/api/insights/proactive/portfolios-no-protection")
async def get_portfolios_no_protection(db: Session = Depends(get_db)):
    """Clients with investment portfolios but no protection cover"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_with_portfolios_no_protection()}


@app.get("/api/insights/proactive/business-exit-planning")
async def get_business_exit_planning(db: Session = Depends(get_db)):
    """Business owner clients who haven't discussed exit planning"""
    engine = InsightsEngine(db)
    return {'clients': engine.business_owners_no_exit_planning()}


@app.get("/api/insights/proactive/birthdays-this-month")
async def get_birthdays_this_month(db: Session = Depends(get_db)):
    """Clients with birthdays this month"""
    logger.info("[API] GET /api/insights/proactive/birthdays-this-month")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.clients_with_birthdays_this_month()}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/proactive/similar-profiles/{client_name}")
async def get_similar_profiles(client_name: str, db: Session = Depends(get_db)):
    """Find clients with similar profiles to a reference client"""
    logger.info(f"[API] GET /api/insights/proactive/similar-profiles/{client_name}")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.find_similar_client_profiles(client_name)}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/proactive/life-events")
async def get_clients_approaching_life_events(db: Session = Depends(get_db)):
    """Identify clients approaching significant life events"""
    logger.info("[API] GET /api/insights/proactive/life-events")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.clients_approaching_life_events()}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/proactive/similar-successful-cases/{client_name}")
async def get_similar_successful_cases(client_name: str, db: Session = Depends(get_db)):
    """Show clients whose circumstances are similar to cases where we added significant value"""
    logger.info(f"[API] GET /api/insights/proactive/similar-successful-cases/{client_name}")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'clients': engine.clients_with_similar_successful_cases(client_name)}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/compliance/recommendations")
async def get_client_recommendations(client_name: str, db: Session = Depends(get_db)):
    """Pull every recommendation made to a client and rationale"""
    engine = InsightsEngine(db)
    return {'recommendations': engine.recommendations_for_client(client_name)}


@app.get("/api/insights/compliance/risk-discussion")
async def get_risk_discussion_wording(client_name: str, db: Session = Depends(get_db)):
    """Exact wording when discussing risk with a client"""
    engine = InsightsEngine(db)
    return {'discussions': engine.risk_discussion_wording(client_name)}


@app.get("/api/insights/compliance/platform-recommendations")
async def get_platform_recommendations(platform_name: str, db: Session = Depends(get_db)):
    """Show all clients where a platform was recommended and why"""
    engine = InsightsEngine(db)
    return {'clients': engine.clients_recommended_platform(platform_name)}


@app.get("/api/insights/compliance/concern-discussions")
async def get_concern_discussions(concern: str, db: Session = Depends(get_db)):
    """Client conversations that mentioned concerns about a topic"""
    engine = InsightsEngine(db)
    return {'meetings': engine.conversations_mentioning_concern(concern)}


@app.get("/api/insights/compliance/documents-waiting")
async def get_documents_waiting(db: Session = Depends(get_db)):
    """What documents are still waiting for from clients?"""
    engine = InsightsEngine(db)
    return {'documents': engine.documents_waiting_from_clients()}


@app.get("/api/insights/compliance/promises")
async def get_promises_to_clients(db: Session = Depends(get_db)):
    """What was promised to clients and when?"""
    logger.info("[API] GET /api/insights/compliance/promises")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return {'promises': engine.promises_to_clients()}
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/compliance/sustainable-investing")
async def get_sustainable_investing_discussions(db: Session = Depends(get_db)):
    """Generate summary of all discussions about sustainable investing preferences"""
    logger.info("[API] GET /api/insights/compliance/sustainable-investing")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return engine.sustainable_investing_discussions()
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/compliance/recommendation-pushback")
async def get_recommendation_pushback(db: Session = Depends(get_db)):
    """Which types of recommendations get the most pushback and why?"""
    logger.info("[API] GET /api/insights/compliance/recommendation-pushback")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return engine.analyze_recommendation_pushback()
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/business/concerns-this-month")
async def get_concerns_this_month(db: Session = Depends(get_db)):
    """Concerns clients raised in meetings this month"""
    engine = InsightsEngine(db)
    return engine.concerns_raised_this_month()


@app.get("/api/insights/business/high-value-services")
async def get_high_value_services(db: Session = Depends(get_db)):
    """Which services do highest-value clients use most?"""
    engine = InsightsEngine(db)
    return {'services': engine.highest_value_client_services()}


@app.get("/api/insights/business/conversion-rates")
async def get_conversion_rates(db: Session = Depends(get_db)):
    """Conversion rates from initial meeting to becoming a client by referral source"""
    engine = InsightsEngine(db)
    return {'rates': engine.conversion_rates_by_referral()}


@app.get("/api/insights/business/approaching-retirement")
async def get_approaching_retirement(years: int = 5, db: Session = Depends(get_db)):
    """What percentage of book is approaching retirement in next N years?"""
    engine = InsightsEngine(db)
    return engine.clients_approaching_retirement(years=years)


@app.get("/api/insights/business/most-efficient")
async def get_most_efficient_clients(db: Session = Depends(get_db)):
    """Clients generating most revenue but taking least time to service"""
    engine = InsightsEngine(db)
    return {'clients': engine.most_efficient_clients()}


@app.get("/api/insights/business/satisfied-clients")
async def get_satisfied_clients(years: int = 5, db: Session = Depends(get_db)):
    """What do most satisfied long-term clients have in common?"""
    logger.info(f"[API] GET /api/insights/business/satisfied-clients (years: {years})")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return engine.satisfied_long_term_clients(years=years)
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/business/life-events-triggering-implementation")
async def get_life_events_triggering_implementation(db: Session = Depends(get_db)):
    """What life events trigger clients to actually implement recommendations?"""
    logger.info("[API] GET /api/insights/business/life-events-triggering-implementation")
    try:
        llm_service = LLMService()
        engine = InsightsEngine(db, llm_service=llm_service)
        return engine.life_events_triggering_recommendations()
    except Exception as e:
        logger.error(f"[API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/follow-ups/draft-email")
async def draft_follow_up_email(meeting_id: int, db: Session = Depends(get_db)):
    """Draft follow-up email for a meeting with key actions"""
    engine = InsightsEngine(db)
    result = engine.draft_follow_up_email(meeting_id)
    if not result:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@app.get("/api/insights/follow-ups/waiting-on")
async def get_waiting_on_information(db: Session = Depends(get_db)):
    """Which clients are we waiting on for information or decisions?"""
    engine = InsightsEngine(db)
    return {'items': engine.waiting_on_information()}


@app.get("/api/insights/follow-ups/open-actions")
async def get_all_open_actions(db: Session = Depends(get_db)):
    """Show all open action items across client base"""
    engine = InsightsEngine(db)
    return {'items': engine.all_open_action_items()}


@app.get("/api/insights/follow-ups/overdue")
async def get_overdue_follow_ups(db: Session = Depends(get_db)):
    """Follow-ups that were committed to but are now overdue"""
    engine = InsightsEngine(db)
    return {'items': engine.overdue_follow_ups()}


@app.post("/api/insights/natural-language")
async def process_natural_language_query(query: str, db: Session = Depends(get_db)):
    """Process natural language queries using agentic architecture with tool selection"""
    logger.info(f"[API] POST /api/insights/natural-language - Query: {query[:100]}...")
    
    try:
        llm_service = LLMService()
        # Use InsightsAgent which handles both insights and chasing
        from agents.insights_agent import InsightsAgent
        agent = InsightsAgent(db, llm_service)
        result = agent.process_query(query)
        logger.info(f"[API] Query processed. Tools used: {result.get('tools_used', [])}, Results: {result.get('count', 0)}")
        return result
    except Exception as e:
        logger.error(f"[API] Error processing natural language query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== WORKFLOW MANAGEMENT API ==========

@app.post("/api/workflow/initialize/{case_id}")
async def initialize_workflow(case_id: int, db: Session = Depends(get_db)):
    """Initialize workflow items for an annual review case"""
    logger.info(f"[API] POST /api/workflow/initialize/{case_id} - Using mock data")
    return {
        'case_id': case_id,
        'workflow_stage': 'pre_meeting',
        'items_created': 3,
        'items': [
            {
                'id': 1,
                'item_name': 'Expenditure Questionnaire',
                'workflow_stage': 'pre_meeting',
                'workflow_substage': 'pack_prep',
            },
            {
                'id': 2,
                'item_name': 'ATR Questionnaire',
                'workflow_stage': 'pre_meeting',
                'workflow_substage': 'pack_prep',
            },
            {
                'id': 3,
                'item_name': 'Pack Sign-Off',
                'workflow_stage': 'pre_meeting',
                'workflow_substage': 'pack_signoff',
            }
        ]
    }


@app.get("/api/workflow/status/{case_id}")
async def get_workflow_status(case_id: int, db: Session = Depends(get_db)):
    """Get workflow status for a case"""
    logger.info(f"[API] GET /api/workflow/status/{case_id} - Using mock data")
    return {
        'case_id': case_id,
        'workflow_stage': 'pre_meeting',
        'workflow_substage': 'pack_prep',
        'status': 'in_progress',
        'can_advance': False,
        'pending_items': 2
    }


@app.get("/api/workflow/blocking-items/{case_id}")
async def get_blocking_items(case_id: int, db: Session = Depends(get_db)):
    """Get items blocking workflow progression"""
    logger.info(f"[API] GET /api/workflow/blocking-items/{case_id} - Using mock data")
    return {
        'case_id': case_id,
        'workflow_stage': 'pre_meeting',
        'blocking_items': [
            {
                'id': 1,
                'item_name': 'Expenditure Questionnaire',
                'item_type': 'questionnaire',
                'workflow_substage': 'pack_prep',
                'status': 'pending',
                'priority': 'high',
                'due_date': (datetime.utcnow() + timedelta(days=3)).isoformat(),
                'days_overdue': 0,
            }
        ]
    }


@app.post("/api/workflow/advance/{case_id}")
async def advance_workflow(case_id: int, db: Session = Depends(get_db)):
    """Manually advance workflow to next stage"""
    logger.info(f"[API] POST /api/workflow/advance/{case_id} - Using mock data")
    return {
        'case_id': case_id,
        'current_stage': 'pre_meeting',
        'advanced': False,
        'message': 'Cannot advance - pending items remain (mock data)'
    }


@app.get("/api/workflow/annual-reviews")
async def get_annual_review_workflows(
    stage: str = None,
    db: Session = Depends(get_db)
):
    """Get all annual review cases with workflow status"""
    logger.info("[API] GET /api/workflow/annual-reviews - Using mock data")
    # Return mock data for annual review workflows
    mock_cases = [
        {
            'case_id': 1,
            'client_id': 1,
            'workflow_stage': 'pre_meeting',
            'workflow_substage': 'pack_prep',
            'status': 'in_progress',
            'blocking_items_count': 2,
            'workflow_status': 'pending_items'
        },
        {
            'case_id': 2,
            'client_id': 2,
            'workflow_stage': 'meeting',
            'workflow_substage': 'fact_find_update',
            'status': 'in_progress',
            'blocking_items_count': 1,
            'workflow_status': 'in_progress'
        }
    ]
    
    if stage:
        mock_cases = [c for c in mock_cases if c['workflow_stage'] == stage]
    
    return {'cases': mock_cases, 'count': len(mock_cases)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

