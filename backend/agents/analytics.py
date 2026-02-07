"""
Predictive analytics and bottleneck detection
"""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import LOA, DocumentRequest, PostAdviceItem, Case, Client, Provider


class AnalyticsEngine:
    """Predictive analytics for bottleneck detection and case velocity"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def predict_bottlenecks(self, days_ahead: int = 7) -> List[Dict]:
        """
        Predict which items are likely to become bottlenecks in the next N days
        """
        bottlenecks = []
        now = datetime.utcnow()
        
        # Analyze LOAs
        loas = self.db.query(LOA).join(Case).join(Client).join(Provider).filter(
            LOA.status.in_(['pending', 'sent', 'acknowledged'])
        ).all()
        
        for loa in loas:
            risk_score = 0.0
            risk_factors = []
            
            # Factor 1: Provider reliability
            if loa.provider.reliability_score < 0.6:
                risk_score += 0.3
                risk_factors.append(f"Low provider reliability ({loa.provider.reliability_score:.2f})")
            
            # Factor 2: Already overdue
            if loa.expected_response_date and now > loa.expected_response_date:
                days_overdue = (now - loa.expected_response_date).days
                risk_score += min(days_overdue * 0.1, 0.4)
                risk_factors.append(f"{days_overdue} days overdue")
            
            # Factor 3: High chase count
            if loa.chase_count > 3:
                risk_score += 0.2
                risk_factors.append(f"High chase count ({loa.chase_count})")
            
            # Factor 4: Stuck score
            risk_score += loa.stuck_score * 0.3
            
            # Factor 5: Time since last chase
            if loa.last_chased_at:
                days_since = (now - loa.last_chased_at).days
                if days_since > 15:
                    risk_score += 0.15
                    risk_factors.append(f"No chase in {days_since} days")
            
            if risk_score > 0.5:  # Threshold for bottleneck prediction
                bottlenecks.append({
                    'type': 'loa',
                    'id': loa.id,
                    'case_id': loa.case_id,
                    'client_name': loa.case.client.name,
                    'provider_name': loa.provider.name,
                    'risk_score': round(risk_score, 2),
                    'risk_factors': risk_factors,
                    'current_status': loa.status,
                    'predicted_issue_date': now + timedelta(days=days_ahead),
                })
        
        # Analyze Document Requests
        doc_requests = self.db.query(DocumentRequest).join(Case).join(Client).filter(
            DocumentRequest.status.in_(['pending', 'sent'])
        ).all()
        
        for req in doc_requests:
            risk_score = 0.0
            risk_factors = []
            
            days_since_request = (now - req.requested_at).days if req.requested_at else 0
            
            # Factor 1: Time since request
            if days_since_request > 14:
                risk_score += 0.3
                risk_factors.append(f"Requested {days_since_request} days ago")
            
            # Factor 2: Client engagement
            if req.case.client.engagement_level == 'low':
                risk_score += 0.2
                risk_factors.append("Low client engagement")
            
            # Factor 3: High chase count
            if req.chase_count > 2:
                risk_score += 0.25
                risk_factors.append(f"Multiple chases ({req.chase_count})")
            
            # Factor 4: Stuck score
            risk_score += req.stuck_score * 0.25
            
            if risk_score > 0.5:
                bottlenecks.append({
                    'type': 'client_document',
                    'id': req.id,
                    'case_id': req.case_id,
                    'client_name': req.case.client.name,
                    'document_type': req.document_type,
                    'risk_score': round(risk_score, 2),
                    'risk_factors': risk_factors,
                    'current_status': req.status,
                    'predicted_issue_date': now + timedelta(days=days_ahead),
                })
        
        # Sort by risk score
        bottlenecks.sort(key=lambda x: x['risk_score'], reverse=True)
        return bottlenecks
    
    def calculate_case_velocity(self, case_id: int) -> Dict:
        """
        Calculate case velocity metrics
        """
        case = self.db.query(Case).filter_by(id=case_id).first()
        if not case:
            return None
        
        now = datetime.utcnow()
        case_age_days = (now - case.created_at).days
        
        # Count items by status
        loas = self.db.query(LOA).filter_by(case_id=case_id).all()
        doc_requests = self.db.query(DocumentRequest).filter_by(case_id=case_id).all()
        post_advice = self.db.query(PostAdviceItem).filter_by(case_id=case_id).all()
        
        total_items = len(loas) + len(doc_requests) + len(post_advice)
        completed_items = sum(1 for loa in loas if loa.status == 'received')
        completed_items += sum(1 for doc in doc_requests if doc.status == 'received')
        completed_items += sum(1 for item in post_advice if item.status == 'received')
        
        completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # Calculate average days per item
        avg_days_per_item = case_age_days / total_items if total_items > 0 else 0
        
        # Predict completion date
        remaining_items = total_items - completed_items
        predicted_days_remaining = remaining_items * avg_days_per_item if avg_days_per_item > 0 else 30
        predicted_completion = now + timedelta(days=int(predicted_days_remaining))
        
        return {
            'case_id': case_id,
            'case_age_days': case_age_days,
            'total_items': total_items,
            'completed_items': completed_items,
            'completion_rate': round(completion_rate, 1),
            'avg_days_per_item': round(avg_days_per_item, 1),
            'predicted_completion_date': predicted_completion.isoformat(),
            'velocity_score': round(completion_rate / max(case_age_days, 1), 2),  # Items completed per day
        }
    
    def get_provider_performance(self) -> List[Dict]:
        """Analyze provider performance metrics"""
        providers = self.db.query(Provider).all()
        performance = []
        
        for provider in providers:
            loas = self.db.query(LOA).filter_by(provider_id=provider.id).all()
            total_loas = len(loas)
            
            if total_loas == 0:
                continue
            
            # Calculate metrics
            completed = sum(1 for loa in loas if loa.status == 'received')
            overdue = sum(1 for loa in loas if loa.status == 'overdue')
            
            # Calculate average response time
            completed_loas = [loa for loa in loas if loa.actual_response_date and loa.sent_to_provider_at]
            if completed_loas:
                response_times = [
                    (loa.actual_response_date - loa.sent_to_provider_at).days
                    for loa in completed_loas
                ]
                avg_response_time = sum(response_times) / len(response_times)
            else:
                avg_response_time = provider.avg_response_days
            
            performance.append({
                'provider_id': provider.id,
                'provider_name': provider.name,
                'total_loas': total_loas,
                'completed': completed,
                'overdue': overdue,
                'completion_rate': round(completed / total_loas * 100, 1) if total_loas > 0 else 0,
                'overdue_rate': round(overdue / total_loas * 100, 1) if total_loas > 0 else 0,
                'avg_response_time_days': round(avg_response_time, 1),
                'reliability_score': provider.reliability_score,
            })
        
        performance.sort(key=lambda x: x['overdue_rate'], reverse=True)
        return performance

