"""
Agent Orchestrator - coordinates all autonomous agents
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Communication, ChaseStatus, CommunicationChannel
from agents.loa_agent import LOAAgent
from agents.client_doc_agent import ClientDocAgent
from agents.post_advice_agent import PostAdviceAgent
from agents.workflow_agent import WorkflowAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates all autonomous chasing agents"""
    
    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.llm_service = llm_service
        logger.info("Initializing AgentOrchestrator")
        logger.info(f"LLM Service provided: {llm_service is not None}")
        self.agents = {
            'loa': LOAAgent(db, llm_service=llm_service),
            'client_document': ClientDocAgent(db, llm_service=llm_service),
            'post_advice': PostAdviceAgent(db, llm_service=llm_service),
            'workflow_item': WorkflowAgent(db, llm_service=llm_service),
        }
        logger.info(f"Initialized {len(self.agents)} agents: {list(self.agents.keys())}")
    
    def run_autonomous_cycle(self) -> Dict:
        """
        Run a complete autonomous chasing cycle
        Returns summary of actions taken
        """
        logger.info("=" * 60)
        logger.info("Starting autonomous cycle")
        logger.info("=" * 60)
        
        all_chases = []
        actions_taken = []
        
        # Get all items needing chase from each agent
        logger.info("Phase 1: Identifying items needing chase")
        for agent_type, agent in self.agents.items():
            logger.info(f"Processing {agent_type} agent...")
            items = agent.identify_chases_needed()
            logger.info(f"  Found {len(items)} items for {agent_type}")
            
            for item in items:
                # Calculate priority and stuck score
                logger.debug(f"  Analyzing item {item.get('id')} (client: {item.get('client_name', 'Unknown')})")
                priority = agent.calculate_priority(item)
                stuck_score = agent.calculate_stuck_score(item)
                logger.debug(f"    Priority: {priority.value}, Stuck Score: {stuck_score:.2f}")
                
                # Update item with calculated scores
                self._update_item_scores(item, priority, stuck_score, agent.chase_type)
                
                # Check if should chase
                should_chase = agent.should_chase(item)
                logger.debug(f"    Should chase: {should_chase}")
                
                if should_chase:
                    all_chases.append({
                        'agent': agent,
                        'item': item,
                        'priority': priority,
                        'stuck_score': stuck_score,
                    })
                    logger.info(f"    ✓ Item {item.get('id')} added to chase queue")
        
        logger.info(f"Phase 1 complete: {len(all_chases)} items identified for chasing")
        
        # Sort by priority and urgency
        logger.info("Phase 2: Sorting items by priority and urgency")
        all_chases.sort(key=lambda x: (
            self._priority_to_int(x['priority']),
            -x['stuck_score'],  # Higher stuck score = more urgent
        ))
        logger.info("Sorting complete")
        
        # Execute chases
        logger.info("Phase 3: Executing chases")
        for idx, chase in enumerate(all_chases, 1):
            agent = chase['agent']
            item = chase['item']
            
            logger.info(f"  [{idx}/{len(all_chases)}] Processing chase for item {item.get('id')} "
                       f"(Client: {item.get('client_name', 'Unknown')}, "
                       f"Priority: {chase['priority'].value}, "
                       f"Stuck Score: {chase['stuck_score']:.2f})")
            
            # Generate communication
            logger.debug("    Generating communication...")
            comm_data = agent.generate_communication(item)
            logger.debug(f"    Communication generated: {comm_data.get('subject', 'N/A')}")
            
            channel = agent.select_channel(item)
            logger.info(f"    Selected channel: {channel.value}")
            
            # Create communication record
            logger.debug("    Creating communication record...")
            communication = self._create_communication(
                item, agent.chase_type, channel, comm_data
            )
            logger.info(f"    ✓ Communication created (ID: {communication.id})")
            
            # Update chase count and last chased timestamp
            logger.debug("    Updating chase metadata...")
            self._update_chase_metadata(item, agent.chase_type)
            
            actions_taken.append({
                'type': agent.chase_type.value,
                'item_id': item['id'],
                'client_name': item.get('client_name'),
                'channel': channel.value,
                'priority': chase['priority'].value,
                'stuck_score': round(chase['stuck_score'], 2),
            })
        
        logger.info("=" * 60)
        logger.info(f"Autonomous cycle completed")
        logger.info(f"  Total items identified: {len(all_chases)}")
        logger.info(f"  Actions taken: {len(actions_taken)}")
        logger.info("=" * 60)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_items_identified': len(all_chases),
            'actions_taken': actions_taken,
        }
    
    def _update_item_scores(self, item: Dict, priority, stuck_score, chase_type):
        """Update priority and stuck score on the actual database record"""
        if chase_type.value == 'loa':
            loa = self.db.query(item['loa'].__class__).filter_by(id=item['id']).first()
            if loa:
                loa.priority = priority.value
                loa.stuck_score = stuck_score
        elif chase_type.value == 'client_document':
            req = self.db.query(item['request'].__class__).filter_by(id=item['id']).first()
            if req:
                req.priority = priority.value
                req.stuck_score = stuck_score
        elif chase_type.value == 'post_advice':
            post_item = self.db.query(item['item'].__class__).filter_by(id=item['id']).first()
            if post_item:
                post_item.priority = priority.value
                post_item.stuck_score = stuck_score
        
        self.db.commit()
    
    def _create_communication(self, item: Dict, chase_type, channel: CommunicationChannel, comm_data: Dict) -> Communication:
        """Create communication record"""
        communication = Communication(
            client_id=item['client_id'],
            chase_type=chase_type.value,
            chase_id=item['id'],
            channel=channel.value,
            direction='outbound',
            subject=comm_data.get('subject'),
            content=comm_data.get('content'),
            sent_at=datetime.utcnow(),
        )
        
        self.db.add(communication)
        self.db.commit()
        return communication
    
    def _update_chase_metadata(self, item: Dict, chase_type):
        """Update chase count and last chased timestamp"""
        if chase_type.value == 'loa':
            loa = self.db.query(item['loa'].__class__).filter_by(id=item['id']).first()
            if loa:
                loa.chase_count += 1
                loa.last_chased_at = datetime.utcnow()
                # Update status if needed
                if loa.status == ChaseStatus.PENDING:
                    loa.status = ChaseStatus.SENT
        elif chase_type.value == 'client_document':
            req = self.db.query(item['request'].__class__).filter_by(id=item['id']).first()
            if req:
                req.chase_count += 1
                req.last_chased_at = datetime.utcnow()
        elif chase_type.value == 'post_advice':
            post_item = self.db.query(item['item'].__class__).filter_by(id=item['id']).first()
            if post_item:
                post_item.chase_count += 1
                post_item.last_chased_at = datetime.utcnow()
        
        self.db.commit()
    
    def _priority_to_int(self, priority) -> int:
        """Convert priority to integer for sorting"""
        priority_map = {
            'urgent': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
        }
        return priority_map.get(priority.value, 2)
    
    def get_dashboard_data(self) -> Dict:
        """Get aggregated data for dashboard"""
        stats = {
            'total_active_chases': 0,
            'overdue_items': 0,
            'items_needing_chase': 0,
            'high_priority_items': 0,
            'predicted_bottlenecks': 0,
            'avg_days_stuck': 0.0,
        }
        
        all_items = []
        
        for agent_type, agent in self.agents.items():
            items = agent.identify_chases_needed()
            all_items.extend(items)
        
        if all_items:
            overdue_count = sum(1 for item in all_items if item.get('days_overdue', 0) > 0)
            high_priority_count = sum(1 for item in all_items if item.get('priority') in ['high', 'urgent'])
            bottleneck_count = sum(1 for item in all_items if agent.calculate_stuck_score(item) > 0.7)
            
            stuck_scores = [agent.calculate_stuck_score(item) for item in all_items]
            avg_stuck = sum(stuck_scores) / len(stuck_scores) if stuck_scores else 0
            
            stats.update({
                'total_active_chases': len(all_items),
                'overdue_items': overdue_count,
                'items_needing_chase': sum(1 for item in all_items if agent.should_chase(item)),
                'high_priority_items': high_priority_count,
                'predicted_bottlenecks': bottleneck_count,
                'avg_days_stuck': round(avg_stuck, 2),
            })
        
        return stats

