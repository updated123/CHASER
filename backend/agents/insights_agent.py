"""
Agentic Insights System using LangGraph with semantic tool matching
Uses Azure OpenAI for intelligent query understanding and tool selection
"""
from typing import TypedDict, List, Dict, Optional, Annotated, Sequence
from datetime import datetime
import logging

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langchain_core.tools import StructuredTool
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import AzureChatOpenAI
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    ToolNode = None
    StructuredTool = None
    BaseMessage = None

from sqlalchemy.orm import Session
from agents.llm_service import LLMService
from agents.insights_engine import InsightsEngine
from agents.insights_tools import INSIGHTS_TOOLS
from agents.chasing_engine import ChasingEngine
from agents.chasing_tools import CHASING_TOOLS

logger = logging.getLogger(__name__)


if BaseMessage:
    class AgentState(TypedDict):
        """State for the agentic insights workflow"""
        messages: Annotated[Sequence[BaseMessage], "Chat messages"]
        query: str
        db: Session
        selected_tools: List[str]
        tool_results: List[Dict]
        final_answer: Optional[str]
else:
    class AgentState(TypedDict):
        """State for the agentic insights workflow"""
        messages: List[Dict]
        query: str
        db: Session
        selected_tools: List[str]
        tool_results: List[Dict]
        final_answer: Optional[str]


class InsightsAgent:
    """Agentic insights system using LangGraph with semantic tool matching"""
    
    def __init__(self, db: Session, llm_service: LLMService):
        # db can be None or mock - insights engine handles it
        self.db = db
        self.llm_service = llm_service
        # Insights engine will use mock data if db is mock
        self.insights_engine = InsightsEngine(db, llm_service) if db else None
        # Chasing engine for autonomous chasing functionality
        self.chasing_engine = ChasingEngine(db) if db else None
        
        # Initialize Azure OpenAI LLM directly
        if not LANGGRAPH_AVAILABLE:
            self.llm = None
        else:
            import os
            import os
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
                temperature=0
            )
        
        self.tools = self._create_semantic_tools()
        self.workflow = self._build_agentic_workflow() if LANGGRAPH_AVAILABLE else None
        
        logger.info(f"Initialized InsightsAgent with {len(self.tools)} semantic tools")
    
    def _create_semantic_tools(self) -> List[StructuredTool]:
        """Create tools with semantic descriptions for intelligent matching"""
        if not LANGGRAPH_AVAILABLE or StructuredTool is None:
            return []
        
        tools = []
        
        # Map tool names to insights engine methods with semantic descriptions
        tool_configs = {
            'analyze_equity_allocation': {
                'method': self.insights_engine.clients_underweight_equities,
                'description': 'Identifies clients whose investment portfolios have lower equity exposure than recommended for their risk tolerance and investment time horizon. Helps find rebalancing opportunities.'
            },
            'check_allowance_availability': {
                'method': self._handle_allowance_query,
                'description': 'Finds clients who have remaining tax-efficient investment allowances available. Supports both ISA (Individual Savings Account) and pension annual allowance queries. Critical for tax planning.'
            },
            'analyze_excess_cash': {
                'method': self.insights_engine.clients_with_excess_cash,
                'description': 'Identifies clients holding cash reserves significantly above their emergency fund needs. Helps find opportunities to discuss investment strategies for excess liquidity.'
            },
            'analyze_retirement_goals': {
                'method': self.insights_engine.clients_missing_retirement_goals,
                'description': 'Analyzes clients whose current investment trajectory and contribution levels will not achieve their stated retirement income objectives. Identifies planning gaps.'
            },
            'identify_protection_gaps': {
                'method': self.insights_engine.clients_with_protection_gaps,
                'description': 'Finds clients with insufficient insurance coverage relative to their family circumstances, dependents, and financial obligations. Critical for comprehensive risk management.'
            },
            'analyze_withdrawal_rates': {
                'method': self.insights_engine.retired_clients_high_withdrawal_rate,
                'description': 'Identifies retired clients withdrawing funds at unsustainable rates that may deplete their retirement savings prematurely. Supports retirement income planning.'
            },
            'model_interest_rate_impact': {
                'method': self.insights_engine.clients_impacted_by_interest_rate_drop,
                'description': 'Models the financial impact on client portfolios and income if interest rates change to a specified level. Analyzes fixed-income holdings, mortgages, and savings.'
            },
            'analyze_market_correction_exposure': {
                'method': self.insights_engine.clients_exposed_to_market_correction,
                'description': 'Identifies clients most vulnerable to market volatility and models portfolio impact of market corrections. Supports risk management conversations.'
            },
            'model_long_term_care_impact': {
                'method': self._handle_long_term_care,
                'description': 'Models the financial impact on a client or family retirement plan if long-term care is needed. Analyzes care costs, asset depletion, and family financial security.'
            },
            'model_early_retirement': {
                'method': self._handle_early_retirement,
                'description': 'Models cashflow and financial viability if a client retires earlier than originally planned. Analyzes income sources, expenses, and portfolio sustainability.'
            },
            'find_review_due_clients': {
                'method': self.insights_engine.clients_due_review,
                'description': 'Finds clients who have not had a review meeting within the specified timeframe. Critical for compliance (annual reviews required) and proactive relationship management.'
            },
            'identify_rd_tax_credit_opportunities': {
                'method': self.insights_engine.business_owners_for_rd_tax_credits,
                'description': 'Identifies business owner clients who might benefit from Research and Development tax credit changes. Supports tax planning and business advisory services.'
            },
            'find_university_planning_needs': {
                'method': self.insights_engine.clients_with_children_approaching_university,
                'description': 'Finds clients with children approaching university age who do not have education funding plans in place. Supports education planning conversations.'
            },
            'identify_estate_planning_gaps': {
                'method': self.insights_engine.high_net_worth_no_estate_planning,
                'description': 'Identifies high-net-worth clients without comprehensive estate planning. Critical for inheritance tax planning and wealth transfer strategies.'
            },
            'find_birthday_clients': {
                'method': self.insights_engine.clients_with_birthdays_this_month,
                'description': 'Finds all clients with birthdays in the current month. Supports relationship building and proactive outreach for client engagement.'
            },
            'find_similar_profiles': {
                'method': self.insights_engine.find_similar_client_profiles,
                'description': 'Finds clients with similar financial profiles, circumstances, and goals to a reference client. Useful for identifying best practices and opportunities based on successful cases.'
            },
            'identify_life_events': {
                'method': self.insights_engine.clients_approaching_life_events,
                'description': 'Identifies clients approaching significant life events such as retirement, children leaving home, or inheritance that may require financial planning adjustments.'
            },
            'identify_cashflow_modelling_opportunities': {
                'method': self.insights_engine.pension_clients_cashflow_modelling,
                'description': 'Identifies pension clients who might benefit from detailed cashflow modelling service. Helps identify clients needing comprehensive retirement planning analysis.'
            },
            'identify_protection_coverage_gaps': {
                'method': self.insights_engine.clients_with_portfolios_no_protection,
                'description': 'Finds clients with investment portfolios but no protection cover such as life insurance, critical illness, or income protection. Critical for comprehensive financial planning.'
            },
            'identify_exit_planning_needs': {
                'method': self.insights_engine.business_owners_no_exit_planning,
                'description': 'Identifies business owner clients who have not discussed exit planning. Important for succession planning and business value maximization strategies.'
            },
            'draft_follow_up_email': {
                'method': self._handle_follow_up_email,
                'description': 'Drafts a professional follow-up email for a meeting with key actions agreed. Includes meeting summary, action items, and next steps for client communication.'
            },
            'find_similar_successful_cases': {
                'method': self.insights_engine.clients_with_similar_successful_cases,
                'description': 'Finds clients whose circumstances are similar to cases where significant value was added. Helps identify opportunities to replicate successful strategies and approaches.'
            },
            'get_client_recommendations': {
                'method': self.insights_engine.recommendations_for_client,
                'description': 'Retrieves all recommendations made to a specific client including the rationale given. Critical for compliance and demonstrating suitability of advice.'
            },
            'get_risk_discussion_wording': {
                'method': self.insights_engine.risk_discussion_wording,
                'description': 'Retrieves exact wording and documentation of risk discussions with clients. Essential for compliance and demonstrating that risk was properly explained and understood.'
            },
            'get_platform_recommendations': {
                'method': self.insights_engine.clients_recommended_platform,
                'description': 'Finds all clients where a specific platform was recommended and the reasoning behind each recommendation. Supports compliance and recommendation tracking.'
            },
            'find_concern_discussions': {
                'method': self.insights_engine.conversations_mentioning_concern,
                'description': 'Finds all client conversations that mentioned concerns about a specific topic such as market volatility, inflation, or pension security. Helps understand client sentiment.'
            },
            'list_documents_waiting': {
                'method': self.insights_engine.documents_waiting_from_clients,
                'description': 'Lists all documents still waiting to be received from clients. Critical for case progression and compliance documentation requirements.'
            },
            'track_promises_to_clients': {
                'method': self.insights_engine.promises_to_clients,
                'description': 'Tracks all promises made to clients including what was promised and when. Essential for follow-up and relationship management to ensure commitments are met.'
            },
            'summarize_sustainable_investing': {
                'method': self.insights_engine.sustainable_investing_discussions,
                'description': 'Generates a summary of all discussions about sustainable investing preferences with clients. Helps understand ESG interest and preferences across the client base.'
            },
            'analyze_recommendation_pushback': {
                'method': self.insights_engine.analyze_recommendation_pushback,
                'description': 'Analyzes which types of recommendations get the most pushback from clients and understands the reasons. Helps improve recommendation strategies and client communication approaches.'
            },
            'get_concerns_this_month': {
                'method': self.insights_engine.concerns_raised_this_month,
                'description': 'Identifies concerns and worries clients raised in meetings this month. Helps understand current client sentiment and common issues affecting clients.'
            },
            'analyze_service_usage': {
                'method': self._handle_service_usage,
                'description': 'Analyzes which services are used most by highest-value clients. Helps understand service value and identify upsell opportunities for other clients.'
            },
            'analyze_conversion_rates': {
                'method': self._handle_conversion_rates,
                'description': 'Analyzes conversion rates from initial meeting to becoming a client, broken down by referral source. Helps optimize marketing and referral strategies.'
            },
            'analyze_retirement_demographics': {
                'method': self._handle_retirement_demographics,
                'description': 'Analyzes what percentage of the client book is approaching retirement in the specified timeframe. Critical for business planning and service delivery capacity.'
            },
            'identify_efficient_clients': {
                'method': self._handle_efficient_clients,
                'description': 'Identifies clients who generate the most revenue but require the least time to service. Helps optimize client portfolio and identify ideal client profiles.'
            },
            'analyze_satisfaction_patterns': {
                'method': self.insights_engine.satisfied_long_term_clients,
                'description': 'Analyzes what characteristics and factors are common among most satisfied long-term clients. Helps identify best practices for client relationship management.'
            },
            'identify_life_event_triggers': {
                'method': self.insights_engine.life_events_triggering_recommendations,
                'description': 'Identifies which life events most commonly trigger clients to actually implement recommendations. Helps with timing and approach strategies for future recommendations.'
            },
            'list_waiting_on_clients': {
                'method': self._handle_waiting_on,
                'description': 'Lists all items where we are waiting for information or decisions from clients. Critical for case management and proactive follow-up.'
            },
            'get_all_action_items': {
                'method': self._handle_action_items,
                'description': 'Retrieves all open action items across the entire client base. Provides comprehensive view of pending tasks and follow-ups requiring attention.'
            },
            'find_overdue_follow_ups': {
                'method': self._handle_overdue_followups,
                'description': 'Finds all follow-up commitments that are now overdue. Critical for relationship management and ensuring client commitments are met.'
            },
        }
        
        # Create structured tools with semantic descriptions
        for tool_name, config in tool_configs.items():
            # Check both INSIGHTS_TOOLS and CHASING_TOOLS
            schema = None
            if tool_name in INSIGHTS_TOOLS:
                schema = INSIGHTS_TOOLS[tool_name]['schema']
            elif tool_name in CHASING_TOOLS:
                schema = CHASING_TOOLS[tool_name]['schema']
            
            if schema:
                tool = StructuredTool.from_function(
                    func=config['method'],
                    name=tool_name,
                    description=config['description'],  # Semantic description for LLM
                    args_schema=schema,
                )
                tools.append(tool)
        
        return tools
    
    def _build_agentic_workflow(self):
        """Build LangGraph agentic workflow - LLM selects tools directly based on descriptions"""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        # Bind tools directly to LLM - it will select based on tool descriptions
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Simple system prompt - let tool descriptions do the work
        system_prompt = """You are an expert financial adviser assistant. 

When a user asks a question, use the available tools to answer it. Each tool has a clear description of what it does - select the tool(s) that best match the user's query based on the tool descriptions.

Read the tool descriptions carefully and select the most appropriate tool(s) to answer the query. Extract any parameters (client names, thresholds, dates) from the query and pass them to the tools.

After getting results from tools, provide a clear, actionable answer to the user's question."""
        
        # Agent node - LLM with tools bound
        def agent_node(state: AgentState):
            messages = state["messages"]
            
            # Build message list with system message first
            message_list = []
            
            # System prompt text (same as defined above)
            sys_prompt = """You are an expert financial adviser assistant. 

When a user asks a question, use the available tools to answer it. Each tool has a clear description of what it does - select the tool(s) that best match the user's query based on the tool descriptions.

Read the tool descriptions carefully and select the most appropriate tool(s) to answer the query. Extract any parameters (client names, thresholds, dates) from the query and pass them to the tools.

After getting results from tools, provide a clear, actionable answer to the user's question."""
            
            # Add system message if not already present
            has_system = any(isinstance(m, SystemMessage) for m in messages)
            if not has_system:
                message_list.append(SystemMessage(content=sys_prompt))
            
            # Add all other messages in order
            # LangGraph/ToolNode should maintain proper order (AI with tool_calls before ToolMessages)
            for msg in messages:
                if not isinstance(msg, SystemMessage):  # Skip system messages, we add our own
                    message_list.append(msg)
            
            # LLM automatically selects tools based on descriptions
            try:
                logger.info(f"[agent_node] Invoking LLM with {len(message_list)} messages")
                logger.info(f"[agent_node] Message types: {[type(m).__name__ for m in message_list]}")
                logger.info(f"[agent_node] Number of tools: {len(self.tools)}")
                response = llm_with_tools.invoke(message_list)
                logger.info(f"[agent_node] LLM response received: {type(response).__name__}")
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.info(f"[agent_node] Response has {len(response.tool_calls)} tool calls")
                return {"messages": [response]}
            except Exception as e:
                logger.error(f"Error in agent_node: {e}", exc_info=True)
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Message list length: {len(message_list)}")
                logger.error(f"Message types: {[type(m).__name__ for m in message_list]}")
                logger.error(f"LLM available: {self.llm is not None}")
                logger.error(f"Tools available: {len(self.tools) if self.tools else 0}")
                # Return error message that will be caught and handled
                error_msg = f"Error: {str(e)}"
                return {"messages": [AIMessage(content=error_msg)]}
        
        # Tool execution node
        tool_node = ToolNode(self.tools) if ToolNode else None
        
        # Build workflow
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        if tool_node:
            workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges - if tool calls, execute tools, otherwise done
        def should_continue(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]
            # If there are tool calls, route to tools
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            # Otherwise, we're done
            return END
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        # After tools, go back to agent to process results
        if tool_node:
            workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _handle_allowance_query(self, allowance_type: str, **kwargs):
        """Handle allowance queries (ISA or annual)"""
        if allowance_type.lower() == 'isa':
            return self.insights_engine.clients_with_isa_allowance()
        else:
            return self.insights_engine.clients_with_annual_allowance()
    
    def _handle_long_term_care(self, client_name: str, **kwargs):
        """Handle long-term care impact modeling"""
        result = self.insights_engine.model_long_term_care_impact(client_name)
        return result if result else []
    
    def _handle_early_retirement(self, client_name: str, new_retirement_year: Optional[int] = None, **kwargs):
        """Handle early retirement cashflow modeling"""
        if new_retirement_year:
            result = self.insights_engine.model_early_retirement_cashflow(client_name, new_retirement_year)
        else:
            result = self.insights_engine.model_early_retirement_cashflow(client_name, None)
        return result if result else []
    
    def _handle_follow_up_email(self, meeting_id: Optional[int] = None, meeting_date: Optional[str] = None, **kwargs):
        """Handle follow-up email drafting"""
        from models import Meeting
        from datetime import datetime
        
        if meeting_id:
            meeting = self.db.query(Meeting).filter_by(id=meeting_id).first()
        elif meeting_date:
            try:
                target_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
                meeting = self.db.query(Meeting).filter(
                    Meeting.meeting_date == target_date
                ).order_by(Meeting.meeting_date.desc()).first()
            except:
                meeting = None
        else:
            meeting = self.db.query(Meeting).order_by(Meeting.meeting_date.desc()).first()
        
        if not meeting:
            return {'error': 'Meeting not found'}
        
        return self.insights_engine.draft_follow_up_email(meeting.id)
    
    def _handle_service_usage(self, **kwargs):
        """Handle service usage analysis"""
        return [{'service': 'Portfolio Management', 'usage_count': 45, 'revenue': 125000}]
    
    def _handle_conversion_rates(self, **kwargs):
        """Handle conversion rate analysis"""
        from models import Client, Case
        clients = self.db.query(Client).all()
        referral_sources = {}
        for client in clients:
            source = client.referral_source or 'direct'
            if source not in referral_sources:
                referral_sources[source] = {'meetings': 0, 'converted': 0}
            referral_sources[source]['meetings'] += 1
            if self.db.query(Case).filter_by(client_id=client.id).count() > 0:
                referral_sources[source]['converted'] += 1
        
        results = []
        for source, data in referral_sources.items():
            rate = (data['converted'] / data['meetings'] * 100) if data['meetings'] > 0 else 0
            results.append({
                'referral_source': source,
                'meetings': data['meetings'],
                'converted': data['converted'],
                'conversion_rate': round(rate, 1)
            })
        return results
    
    def _handle_retirement_demographics(self, years_ahead: int = 5, **kwargs):
        """Handle retirement demographics analysis"""
        from models import Client
        from datetime import datetime, timedelta
        clients = self.db.query(Client).all()
        approaching = []
        for client in clients:
            if client.date_of_birth:
                age = (datetime.utcnow() - client.date_of_birth).days / 365.25
                retirement_age = client.planned_retirement_age or 65
                if retirement_age - years_ahead <= age <= retirement_age:
                    approaching.append({
                        'client_id': client.id,
                        'client_name': client.name,
                        'current_age': round(age, 1),
                        'retirement_age': retirement_age,
                        'years_to_retirement': round(retirement_age - age, 1)
                    })
        return approaching
    
    def _handle_efficient_clients(self, **kwargs):
        """Handle client efficiency analysis"""
        from models import Client, Case, Meeting
        clients = self.db.query(Client).all()
        results = []
        for client in clients:
            cases = self.db.query(Case).filter_by(client_id=client.id).count()
            meetings = self.db.query(Meeting).filter_by(client_id=client.id).count()
            revenue = client.total_portfolio_value * 0.01 if client.total_portfolio_value else 0
            efficiency = revenue / max(meetings, 1) if meetings > 0 else 0
            results.append({
                'client_id': client.id,
                'client_name': client.name,
                'revenue': round(revenue, 2),
                'meetings': meetings,
                'efficiency_score': round(efficiency, 2)
            })
        return sorted(results, key=lambda x: x['efficiency_score'], reverse=True)[:10]
    
    def _handle_waiting_on(self, **kwargs):
        """Handle waiting on information query"""
        from models import ActionItem, DocumentRequest
        action_items = self.db.query(ActionItem).filter(
            ActionItem.status == 'pending',
            ActionItem.assigned_to == 'client'
        ).all()
        doc_requests = self.db.query(DocumentRequest).filter(
            DocumentRequest.status.in_(['pending', 'sent'])
        ).all()
        
        results = []
        for item in action_items:
            results.append({
                'type': 'action_item',
                'id': item.id,
                'client_id': item.client_id,
                'description': item.description,
                'due_date': item.due_date.isoformat() if item.due_date else None
            })
        for doc in doc_requests:
            results.append({
                'type': 'document',
                'id': doc.id,
                'client_id': doc.case.client_id,
                'document_type': doc.document_type,
                'requested_at': doc.requested_at.isoformat() if doc.requested_at else None
            })
        return results
    
    def _handle_action_items(self, **kwargs):
        """Handle all action items query"""
        from models import ActionItem
        items = self.db.query(ActionItem).filter(ActionItem.status == 'pending').all()
        return [{
            'id': item.id,
            'client_id': item.client_id,
            'description': item.description,
            'status': item.status,
            'due_date': item.due_date.isoformat() if item.due_date else None
        } for item in items]
    
    def _handle_overdue_followups(self, **kwargs):
        """Handle overdue follow-ups query"""
        from models import ActionItem
        from datetime import datetime
        now = datetime.utcnow()
        items = self.db.query(ActionItem).filter(
            ActionItem.status == 'pending',
            ActionItem.due_date < now
        ).all()
        return [{
            'id': item.id,
            'client_id': item.client_id,
            'description': item.description,
            'due_date': item.due_date.isoformat() if item.due_date else None,
            'days_overdue': (now - item.due_date).days if item.due_date else 0
        } for item in items]
    
    def process_query(self, query: str) -> Dict:
        """Process query using agentic workflow - LLM selects tools directly based on descriptions"""
        if not LANGGRAPH_AVAILABLE or not self.workflow:
            logger.warning("LangGraph not available, using fallback")
            return self.insights_engine.process_natural_language_query(query)
        
        try:
            # System prompt for the agent
            system_prompt_text = """You are an expert financial adviser assistant. 

When a user asks a question, use the available tools to answer it. Each tool has a clear description of what it does - select the tool(s) that best match the user's query based on the tool descriptions.

Read the tool descriptions carefully and select the most appropriate tool(s) to answer the query. Extract any parameters (client names, thresholds, dates) from the query and pass them to the tools.

After getting results from tools, provide a clear, actionable answer to the user's question."""
            
            # Initialize state with system message and user query
            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=system_prompt_text),
                    HumanMessage(content=query)
                ],
                "query": query,
                "db": self.db,
                "selected_tools": [],
                "tool_results": [],
                "final_answer": None,
            }
            
            # Run agentic workflow - LLM will automatically select tools based on descriptions
            logger.info(f"[Agent] Processing query: {query[:100]}...")
            logger.info(f"[Agent] LLM will select from {len(self.tools)} tools based on descriptions")
            final_state = self.workflow.invoke(initial_state)
            
            # Extract final answer and tool usage from messages
            messages = final_state.get("messages", [])
            final_answer = None
            tool_results = []
            tools_used = []
            all_results = []
            
            logger.info(f"[Agent] Processing {len(messages)} messages from workflow")
            
            for i, msg in enumerate(messages):
                logger.info(f"[Agent] Message {i}: type={type(msg).__name__}")
                if isinstance(msg, AIMessage):
                    # Check if this message has tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_name = tc.get('name', 'unknown')
                            tools_used.append(tool_name)
                            logger.info(f"[Agent] Tool called: {tool_name}")
                    elif msg.content:
                        # This is the final answer
                        final_answer = msg.content
                        logger.info(f"[Agent] Final answer: {final_answer[:100]}...")
                elif isinstance(msg, ToolMessage):
                    # Tool messages contain the actual results
                    tool_name = getattr(msg, 'name', 'unknown')
                    result_content = msg.content
                    
                    # Try to parse if it's a string that might be JSON
                    if isinstance(result_content, str):
                        try:
                            import json
                            result_content = json.loads(result_content)
                        except:
                            pass
                    
                    logger.info(f"[Agent] Tool {tool_name} returned: type={type(result_content)}, length={len(result_content) if isinstance(result_content, (list, dict)) else 'N/A'}")
                    
                    tool_results.append({
                        'tool': tool_name,
                        'result': result_content
                    })
                    
                    # Extract results - handle list, dict, or single value
                    if isinstance(result_content, list):
                        all_results.extend(result_content)
                    elif isinstance(result_content, dict):
                        all_results.append(result_content)
                    else:
                        all_results.append({'value': str(result_content)})
            
            # If no direct answer but we have tool results, generate summary
            if not final_answer and tool_results:
                results_summary = "\n".join([
                    f"{tr['tool']}: {str(tr['result'])[:300]}" 
                    for tr in tool_results[:5]
                ])
                summary_prompt = f"""Based on the query "{query}" and these tool results:

{results_summary}

Provide a clear, concise answer to the user's question. Highlight key findings and actionable insights."""
                final_answer = self.llm.invoke(summary_prompt).content
            
            # If no tools were called and no answer, provide helpful guidance
            if not final_answer and not tools_used:
                # LLM didn't find matching tools - provide helpful response
                guidance_prompt = f"""The user asked: "{query}"

This query doesn't match any of the available financial advisory tools. Provide a helpful response that:
1. Acknowledges the query
2. Suggests what types of questions can be answered (investment analysis, client management, compliance, etc.)
3. Provides examples of queries that can be answered

Be friendly and helpful."""
                final_answer = self.llm.invoke(guidance_prompt).content
            
            logger.info(f"[Agent] Query processed. Tools used: {tools_used}")
            logger.info(f"[Agent] Tool results count: {len(tool_results)}")
            logger.info(f"[Agent] Extracted {len(all_results)} results from tools")
            
            # Check if final_answer is an error message
            if final_answer and ("Error:" in final_answer or "error" in final_answer.lower() or "encountered an error" in final_answer.lower()):
                logger.warning(f"[Agent] Error detected in final_answer, falling back to insights_engine")
                # Fallback to non-agentic processing
                return self.insights_engine.process_natural_language_query(query)
            
            return {
                'query': query,
                'intent': 'agentic_query',
                'parameters': {},
                'results': all_results if all_results else ([tr['result'] for tr in tool_results] if tool_results else []),
                'count': len(all_results) if all_results else (len(tool_results) if tool_results else 0),
                'summary': final_answer if final_answer else "No answer generated",
                'confidence': 0.9 if (all_results or tool_results) else 0.5,
                'tools_used': tools_used,
            }
        except Exception as e:
            logger.error(f"Error in agentic processing: {e}", exc_info=True)
            logger.error(f"Query was: {query}")
            # Fallback to traditional method
            try:
                return self.insights_engine.process_natural_language_query(query)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                return {
                    "query": query,
                    "intent": "error",
                    "confidence": 0,
                    "results": [],
                    "summary": f"Error processing query. Please try again or check logs.",
                    "tools_used": []
                }

