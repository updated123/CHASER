"""
Base agent class for autonomous chasing agents
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import ChaseType, ChaseStatus, Priority, CommunicationChannel


class BaseAgent(ABC):
    """Base class for all autonomous chasing agents"""
    
    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.llm_service = llm_service  # Optional LLM service for intelligent reasoning
        self.chase_type: ChaseType = None
        self.name: str = "BaseAgent"
    
    @abstractmethod
    def identify_chases_needed(self) -> List[Dict]:
        """Identify items that need chasing"""
        pass
    
    @abstractmethod
    def calculate_priority(self, item: Dict) -> Priority:
        """Calculate priority score for an item"""
        pass
    
    @abstractmethod
    def should_chase(self, item: Dict) -> bool:
        """Determine if an item should be chased now"""
        pass
    
    @abstractmethod
    def generate_communication(self, item: Dict) -> Dict:
        """Generate communication content for chasing"""
        pass
    
    @abstractmethod
    def select_channel(self, item: Dict) -> CommunicationChannel:
        """Select appropriate communication channel"""
        pass
    
    def calculate_stuck_score(self, item: Dict) -> float:
        """
        Calculate stuck score (0-1) for bottleneck prediction
        Higher score = more likely to be stuck
        """
        chase_count = item.get('chase_count', 0)
        days_since_last_chase = item.get('days_since_last_chase', 0)
        days_overdue = item.get('days_overdue', 0)
        status = item.get('status', 'pending')
        
        # Base score from chase count
        score = min(chase_count * 0.15, 0.5)
        
        # Add score for time since last chase
        if days_since_last_chase > 7:
            score += min((days_since_last_chase - 7) * 0.05, 0.3)
        
        # Add score for overdue items
        if days_overdue > 0:
            score += min(days_overdue * 0.1, 0.4)
        
        # Status-based adjustments
        if status == 'stuck':
            score = max(score, 0.8)
        elif status == 'overdue':
            score = max(score, 0.6)
        
        return min(score, 1.0)
    
    def calculate_urgency_score(self, item: Dict) -> float:
        """
        Calculate urgency score considering multiple factors
        Returns 0-1 score where 1 is most urgent
        """
        priority_map = {
            'urgent': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25
        }
        
        base_score = priority_map.get(item.get('priority', 'medium'), 0.5)
        
        # Boost for overdue items
        days_overdue = item.get('days_overdue', 0)
        if days_overdue > 0:
            base_score += min(days_overdue * 0.05, 0.2)
        
        # Boost for high client value
        client_value = item.get('client_value_score', 1.0)
        base_score += (client_value - 1.0) * 0.1
        
        # Boost for multiple chases
        if item.get('chase_count', 0) > 2:
            base_score += 0.15
        
        return min(base_score, 1.0)
    
    def days_between(self, date1: Optional[datetime], date2: Optional[datetime]) -> int:
        """Calculate days between two dates"""
        if not date1 or not date2:
            return 0
        return (date2 - date1).days

