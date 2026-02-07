"""
LangGraph-based orchestrator for intelligent agent workflow
"""
from typing import TypedDict, Annotated, List, Dict
from datetime import datetime
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Fallback if LangGraph not available
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from sqlalchemy.orm import Session
from agents.llm_service import LLMService
from agents.loa_agent import LOAAgent
from agents.client_doc_agent import ClientDocAgent
from agents.post_advice_agent import PostAdviceAgent
from agents.workflow_agent import WorkflowAgent
from models import Communication, CommunicationChannel, ChaseStatus


class OrchestratorState(TypedDict):
    """State for the orchestrator workflow"""
    db: Session
    items_to_analyze: List[Dict]
    analyzed_items: List[Dict]
    prioritized_items: List[Dict]
    communications_generated: List[Dict]
    actions_taken: List[Dict]
    cycle_summary: Dict


class LangGraphOrchestrator:
    """LangGraph-based orchestrator with intelligent decision making"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        # Initialize agents with LLM service for intelligent reasoning
        self.agents = {
            'loa': LOAAgent(db, llm_service=self.llm_service),
            'client_document': ClientDocAgent(db, llm_service=self.llm_service),
            'post_advice': PostAdviceAgent(db, llm_service=self.llm_service),
            'workflow_item': WorkflowAgent(db, llm_service=self.llm_service),
        }
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None  # Will use fallback method
        
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("identify_items", self._identify_items)
        workflow.add_node("analyze_items", self._analyze_items)
        workflow.add_node("prioritize_items", self._prioritize_items)
        workflow.add_node("generate_communications", self._generate_communications)
        workflow.add_node("execute_actions", self._execute_actions)
        workflow.add_node("create_summary", self._create_summary)
        
        # Define edges
        workflow.set_entry_point("identify_items")
        workflow.add_edge("identify_items", "analyze_items")
        workflow.add_edge("analyze_items", "prioritize_items")
        workflow.add_edge("prioritize_items", "generate_communications")
        workflow.add_edge("generate_communications", "execute_actions")
        workflow.add_edge("execute_actions", "create_summary")
        workflow.add_edge("create_summary", END)
        
        return workflow.compile()
    
    def _identify_items(self, state: OrchestratorState) -> OrchestratorState:
        """Identify all items needing attention"""
        items_to_analyze = []
        
        for agent_type, agent in self.agents.items():
            items = agent.identify_chases_needed()
            for item in items:
                item['agent_type'] = agent_type
                item['agent'] = agent
                items_to_analyze.append(item)
        
        state["items_to_analyze"] = items_to_analyze
        return state
    
    def _analyze_items(self, state: OrchestratorState) -> OrchestratorState:
        """Use LLM to analyze each item"""
        analyzed_items = []
        
        for item in state["items_to_analyze"]:
            agent = item['agent']
            agent_type = item['agent_type']
            
            # Build context for LLM
            item_context = {
                'client_name': item.get('client_name', 'Unknown'),
                'client_value_score': item.get('client_value_score', 1.0),
                'engagement_level': item.get('engagement_level', 'medium'),
                'days_overdue': item.get('days_overdue', 0),
                'days_since_last_chase': item.get('days_since_last_chase', 0),
                'chase_count': item.get('chase_count', 0),
                'status': item.get('status', 'pending'),
                'item_type': item.get('item_type') or item.get('document_type') or 'general',
                'item_details': str(item),
                'preferred_contact': item.get('client_preferred_contact', 'email'),
                'provider_reliability': item.get('provider_reliability', 0.7),
            }
            
            # LLM-based priority analysis
            priority_analysis = self.llm_service.analyze_priority(item_context, agent_type)
            
            # LLM-based stuck score analysis
            stuck_analysis = self.llm_service.analyze_stuck_score(item_context)
            
            # LLM-based should chase decision
            should_chase_analysis = self.llm_service.should_chase_now(item_context, agent_type)
            
            analyzed_item = {
                **item,
                'llm_priority': priority_analysis.get('priority', 'medium'),
                'llm_priority_reasoning': priority_analysis.get('reasoning', ''),
                'llm_urgency_score': priority_analysis.get('urgency_score', 0.5),
                'llm_stuck_score': stuck_analysis.get('stuck_score', 0.0),
                'llm_stuck_risk_factors': stuck_analysis.get('risk_factors', []),
                'llm_should_chase': should_chase_analysis.get('should_chase', False),
                'llm_chase_reasoning': should_chase_analysis.get('reasoning', ''),
                'llm_chase_confidence': should_chase_analysis.get('confidence', 0.5),
            }
            
            analyzed_items.append(analyzed_item)
        
        state["analyzed_items"] = analyzed_items
        return state
    
    def _prioritize_items(self, state: OrchestratorState) -> OrchestratorState:
        """Prioritize items based on LLM analysis"""
        # Filter items that should be chased
        items_to_chase = [
            item for item in state["analyzed_items"]
            if item.get('llm_should_chase', False)
        ]
        
        # Sort by LLM urgency score and stuck score
        prioritized = sorted(
            items_to_chase,
            key=lambda x: (
                -x.get('llm_urgency_score', 0),
                -x.get('llm_stuck_score', 0),
                x.get('chase_count', 0)
            )
        )
        
        state["prioritized_items"] = prioritized
        return state
    
    def _generate_communications(self, state: OrchestratorState) -> OrchestratorState:
        """Generate communications using LLM"""
        communications = []
        
        for item in state["prioritized_items"]:
            agent = item['agent']
            agent_type = item['agent_type']
            
            item_context = {
                'client_name': item.get('client_name', 'Unknown'),
                'engagement_level': item.get('engagement_level', 'medium'),
                'preferred_contact': item.get('client_preferred_contact', 'email'),
                'days_overdue': item.get('days_overdue', 0),
                'chase_count': item.get('chase_count', 0),
                'priority': item.get('llm_priority', 'medium'),
                'item_type': item.get('item_type') or item.get('document_type') or 'general',
                'item_details': str(item),
            }
            
            # LLM-based communication generation
            comm_data = self.llm_service.generate_communication(
                item_context,
                agent_type,
                item.get('chase_count', 0)
            )
            
            # LLM-based channel selection
            channel_name = self.llm_service.select_communication_channel(item_context, agent_type)
            channel = CommunicationChannel.EMAIL
            if channel_name == 'sms':
                channel = CommunicationChannel.SMS
            elif channel_name == 'phone':
                channel = CommunicationChannel.PHONE
            
            communication_record = {
                'item': item,
                'agent': agent,
                'communication_data': comm_data,
                'channel': channel,
                'llm_generated': True,
            }
            
            communications.append(communication_record)
        
        state["communications_generated"] = communications
        return state
    
    def _execute_actions(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the communications"""
        actions_taken = []
        
        for comm_record in state["communications_generated"]:
            item = comm_record['item']
            agent = comm_record['agent']
            comm_data = comm_record['communication_data']
            channel = comm_record['channel']
            
            # Create communication record in database
            communication = Communication(
                client_id=item['client_id'],
                chase_type=agent.chase_type.value,
                chase_id=item['id'],
                channel=channel.value,
                direction='outbound',
                subject=comm_data.get('subject', 'Action Required'),
                content=comm_data.get('content', 'Please contact us.'),
                sent_at=datetime.utcnow(),
            )
            
            self.db.add(communication)
            
            # Update chase metadata
            self._update_chase_metadata(item, agent.chase_type)
            
            actions_taken.append({
                'type': agent.chase_type.value,
                'item_id': item['id'],
                'client_name': item.get('client_name'),
                'channel': channel.value,
                'priority': item.get('llm_priority', 'medium'),
                'stuck_score': round(item.get('llm_stuck_score', 0), 2),
                'llm_reasoning': item.get('llm_chase_reasoning', ''),
            })
        
        self.db.commit()
        state["actions_taken"] = actions_taken
        return state
    
    def _create_summary(self, state: OrchestratorState) -> OrchestratorState:
        """Create summary of the cycle"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_items_identified': len(state["items_to_analyze"]),
            'items_analyzed': len(state["analyzed_items"]),
            'items_prioritized': len(state["prioritized_items"]),
            'communications_generated': len(state["communications_generated"]),
            'actions_taken': state["actions_taken"],
            'summary_stats': {
                'urgent_items': sum(1 for item in state["analyzed_items"] if item.get('llm_priority') == 'urgent'),
                'high_priority_items': sum(1 for item in state["analyzed_items"] if item.get('llm_priority') == 'high'),
                'high_stuck_risk': sum(1 for item in state["analyzed_items"] if item.get('llm_stuck_score', 0) > 0.7),
            }
        }
        
        state["cycle_summary"] = summary
        return state
    
    def _update_chase_metadata(self, item: Dict, chase_type):
        """Update chase count and last chased timestamp"""
        from models import LOA, DocumentRequest, PostAdviceItem
        
        if chase_type.value == 'loa':
            loa = self.db.query(LOA).filter_by(id=item['id']).first()
            if loa:
                loa.chase_count += 1
                loa.last_chased_at = datetime.utcnow()
                if loa.status == ChaseStatus.PENDING:
                    loa.status = ChaseStatus.SENT
        elif chase_type.value == 'client_document':
            req = self.db.query(DocumentRequest).filter_by(id=item['id']).first()
            if req:
                req.chase_count += 1
                req.last_chased_at = datetime.utcnow()
        elif chase_type.value == 'post_advice':
            post_item = self.db.query(PostAdviceItem).filter_by(id=item['id']).first()
            if post_item:
                post_item.chase_count += 1
                post_item.last_chased_at = datetime.utcnow()
        
        self.db.commit()
    
    def run_autonomous_cycle(self) -> Dict:
        """Run the complete autonomous cycle using LangGraph"""
        if not LANGGRAPH_AVAILABLE or not self.workflow:
            # Fallback to sequential execution
            return self._run_sequential_cycle()
        
        initial_state: OrchestratorState = {
            'db': self.db,
            'items_to_analyze': [],
            'analyzed_items': [],
            'prioritized_items': [],
            'communications_generated': [],
            'actions_taken': [],
            'cycle_summary': {},
        }
        
        # Execute workflow
        final_state = self.workflow.invoke(initial_state)
        
        return final_state["cycle_summary"]
    
    def _run_sequential_cycle(self) -> Dict:
        """Fallback sequential execution if LangGraph unavailable"""
        # Similar to traditional orchestrator but with LLM reasoning
        from agents.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator(self.db)
        return orchestrator.run_autonomous_cycle()

