"""
LLM Service using Azure OpenAI for intelligent agent reasoning
"""
import os
import logging
import json
from typing import Dict, List, Optional, Any
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered reasoning and generation"""
    
    def __init__(self):
        logger.info("Initializing LLM Service with Azure OpenAI")
        try:
            # Get credentials from environment variables only
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            
            if not api_key:
                raise ValueError("AZURE_OPENAI_API_KEY is required")
            if not azure_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT is required")
            
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version=api_version,
                api_key=api_key,
                temperature=0
            )
            logger.info("Azure OpenAI LLM initialized successfully")
            logger.info(f"Azure Endpoint: {azure_endpoint}")
            logger.info(f"Deployment: gpt-4o-mini")
            logger.info(f"API Version: 2024-02-15-preview")
            logger.info(f"Temperature: 0")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI LLM: {e}", exc_info=True)
            raise
        
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        logger.info("LLM Service initialization complete")
    
    def analyze_priority(self, item_context: Dict, agent_type: str) -> Dict:
        """
        Use LLM to intelligently analyze priority based on context
        Returns: {priority: str, reasoning: str, urgency_score: float}
        """
        logger.info(f"[analyze_priority] Starting priority analysis for {agent_type} item")
        logger.debug(f"[analyze_priority] Item context: {json.dumps(item_context, default=str, indent=2)}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert financial services operations assistant. 
            Analyze the priority of chasing items based on multiple contextual factors.
            Consider: client value, time sensitivity, case impact, relationship factors, and compliance requirements.
            Return a JSON object with: priority (urgent/high/medium/low), reasoning (brief explanation), and urgency_score (0-1)."""),
            HumanMessage(content=f"""Analyze the priority for this {agent_type} item:
            
            Client: {item_context.get('client_name', 'Unknown')}
            Client Value Score: {item_context.get('client_value_score', 1.0)}
            Engagement Level: {item_context.get('engagement_level', 'medium')}
            Days Overdue: {item_context.get('days_overdue', 0)}
            Days Since Last Chase: {item_context.get('days_since_last_chase', 0)}
            Chase Count: {item_context.get('chase_count', 0)}
            Status: {item_context.get('status', 'pending')}
            Additional Context: {item_context.get('additional_context', 'None')}
            
            Consider the full context and provide intelligent priority assessment.""")
        ])
        
        logger.debug(f"[analyze_priority] Sending request to Azure OpenAI for {agent_type} item")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            logger.info(f"[analyze_priority] Successfully received priority analysis: {result.get('priority', 'unknown')}")
            logger.debug(f"[analyze_priority] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"[analyze_priority] LLM request failed: {e}", exc_info=True)
            logger.warning(f"[analyze_priority] Falling back to rule-based priority calculation")
            fallback_result = self._fallback_priority(item_context)
            logger.info(f"[analyze_priority] Fallback priority: {fallback_result.get('priority', 'unknown')}")
            return fallback_result
    
    def should_chase_now(self, item_context: Dict, agent_type: str, last_decision: Optional[str] = None) -> Dict:
        """
        Use LLM to determine if an item should be chased now
        Returns: {should_chase: bool, reasoning: str, confidence: float}
        """
        logger.info(f"[should_chase_now] Evaluating chase decision for {agent_type} item")
        logger.debug(f"[should_chase_now] Item context: {json.dumps(item_context, default=str, indent=2)}")
        logger.debug(f"[should_chase_now] Last decision: {last_decision}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at determining optimal timing for client communications.
            Consider: client engagement patterns, time since last contact, urgency, client preferences, and relationship impact.
            Avoid over-communication that could damage relationships.
            Return JSON: {should_chase: bool, reasoning: str, confidence: float 0-1}"""),
            HumanMessage(content=f"""Should we chase this {agent_type} item now?
            
            Client: {item_context.get('client_name', 'Unknown')}
            Engagement Level: {item_context.get('engagement_level', 'medium')}
            Preferred Contact: {item_context.get('preferred_contact', 'email')}
            Days Since Last Chase: {item_context.get('days_since_last_chase', 0)}
            Days Overdue: {item_context.get('days_overdue', 0)}
            Chase Count: {item_context.get('chase_count', 0)}
            Priority: {item_context.get('priority', 'medium')}
            Last Decision: {last_decision or 'None'}
            
            Make an intelligent decision considering relationship management and effectiveness.""")
        ])
        
        logger.debug(f"[should_chase_now] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            should_chase = result.get('should_chase', False)
            logger.info(f"[should_chase_now] LLM decision: {'CHASE' if should_chase else 'DO NOT CHASE'}")
            logger.info(f"[should_chase_now] Reasoning: {result.get('reasoning', 'N/A')}")
            logger.info(f"[should_chase_now] Confidence: {result.get('confidence', 0.0)}")
            logger.debug(f"[should_chase_now] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"[should_chase_now] LLM request failed: {e}", exc_info=True)
            logger.warning(f"[should_chase_now] Falling back to rule-based decision")
            fallback_result = {
                'should_chase': item_context.get('days_since_last_chase', 0) >= 7,
                'reasoning': 'Fallback rule-based decision',
                'confidence': 0.5
            }
            logger.info(f"[should_chase_now] Fallback decision: {'CHASE' if fallback_result['should_chase'] else 'DO NOT CHASE'}")
            return fallback_result
    
    def generate_communication(self, item_context: Dict, agent_type: str, chase_count: int) -> Dict:
        """
        Generate natural, context-aware communication using LLM
        Returns: {subject: str, content: str, tone: str}
        """
        logger.info(f"[generate_communication] Generating communication for {agent_type} item (chase #{chase_count})")
        logger.debug(f"[generate_communication] Item context: {json.dumps(item_context, default=str, indent=2)}")
        
        client_name = item_context.get('client_name', 'Client')
        first_name = client_name.split()[0] if client_name else 'Client'
        
        # Build context string
        context_parts = []
        if item_context.get('days_overdue'):
            context_parts.append(f"Item is {item_context['days_overdue']} days overdue")
        if item_context.get('chase_count', 0) > 0:
            context_parts.append(f"This is chase #{item_context['chase_count']}")
        if item_context.get('engagement_level'):
            context_parts.append(f"Client engagement: {item_context['engagement_level']}")
        
        context_str = ". ".join(context_parts) if context_parts else "Initial request"
        logger.debug(f"[generate_communication] Context string: {context_str}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a professional financial adviser assistant writing client communications.
            Write natural, friendly, but professional emails/SMS that:
            - Are personalized and use the client's first name
            - Explain clearly what's needed and why
            - Maintain a positive, helpful tone
            - Escalate urgency appropriately based on chase count
            - Never sound robotic or template-like
            - Show empathy and understanding
            
            Adapt tone based on:
            - First chase: Friendly and helpful
            - Second chase: Slightly more direct, still friendly
            - Third+ chase: More urgent but still professional and respectful
            
            Return JSON: {subject: str, content: str, tone: str}"""),
            HumanMessage(content=f"""Generate communication for:
            
            Client: {first_name} {client_name.split()[-1] if len(client_name.split()) > 1 else ''}
            Item Type: {agent_type}
            Item Details: {item_context.get('item_details', 'N/A')}
            Context: {context_str}
            Chase Number: {chase_count}
            
            Generate a natural, personalized message.""")
        ])
        
        logger.debug(f"[generate_communication] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            logger.info(f"[generate_communication] Successfully generated communication")
            logger.debug(f"[generate_communication] Generated subject: {result.get('subject', 'N/A')}")
            logger.debug(f"[generate_communication] Generated tone: {result.get('tone', 'N/A')}")
            logger.debug(f"[generate_communication] Content preview: {result.get('content', '')[:100]}...")
            logger.debug(f"[generate_communication] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            
            # Ensure we have proper structure
            if isinstance(result, dict):
                return {
                    'subject': result.get('subject', 'Action Required'),
                    'content': result.get('content', 'Please contact us.'),
                    'tone': result.get('tone', 'professional')
                }
            return result
        except Exception as e:
            logger.error(f"[generate_communication] LLM request failed: {e}", exc_info=True)
            logger.warning(f"[generate_communication] Falling back to template communication")
            fallback_result = self._fallback_communication(item_context, chase_count)
            logger.info(f"[generate_communication] Fallback communication generated")
            return fallback_result
    
    def select_communication_channel(self, item_context: Dict, agent_type: str) -> str:
        """
        Intelligently select communication channel using LLM
        Returns: channel name (email/sms/phone)
        """
        logger.info(f"[select_communication_channel] Selecting channel for {agent_type} item")
        logger.debug(f"[select_communication_channel] Item context: {json.dumps(item_context, default=str, indent=2)}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at selecting optimal communication channels.
            Consider: client preference, urgency, item type, relationship stage, and communication history.
            Return JSON: {channel: str, reasoning: str}"""),
            HumanMessage(content=f"""Select the best communication channel for this {agent_type} item:
            
            Client Preference: {item_context.get('preferred_contact', 'email')}
            Engagement Level: {item_context.get('engagement_level', 'medium')}
            Days Overdue: {item_context.get('days_overdue', 0)}
            Chase Count: {item_context.get('chase_count', 0)}
            Priority: {item_context.get('priority', 'medium')}
            Item Type: {item_context.get('item_type', 'general')}
            
            Choose: email (default, good audit trail), sms (urgent, high visibility), or phone (escalation, complex issues).""")
        ])
        
        logger.debug(f"[select_communication_channel] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            channel = result.get('channel', 'email').lower()
            logger.info(f"[select_communication_channel] LLM selected channel: {channel}")
            logger.info(f"[select_communication_channel] Reasoning: {result.get('reasoning', 'N/A')}")
            logger.debug(f"[select_communication_channel] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            
            # Validate
            if channel in ['email', 'sms', 'phone']:
                return channel
            logger.warning(f"[select_communication_channel] Invalid channel '{channel}', defaulting to 'email'")
            return 'email'
        except Exception as e:
            logger.error(f"[select_communication_channel] LLM request failed: {e}", exc_info=True)
            fallback_channel = item_context.get('preferred_contact', 'email')
            logger.warning(f"[select_communication_channel] Falling back to preferred contact: {fallback_channel}")
            return fallback_channel
    
    def analyze_stuck_score(self, item_context: Dict) -> Dict:
        """
        Use LLM to analyze likelihood of item becoming stuck
        Returns: {stuck_score: float 0-1, risk_factors: List[str], recommendations: str}
        """
        logger.info(f"[analyze_stuck_score] Analyzing stuck risk for item")
        logger.debug(f"[analyze_stuck_score] Item context: {json.dumps(item_context, default=str, indent=2)}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at predicting bottlenecks in financial services workflows.
            Analyze risk factors and predict likelihood of items getting stuck.
            Return JSON: {stuck_score: float 0-1, risk_factors: List[str], recommendations: str}"""),
            HumanMessage(content=f"""Analyze stuck risk for this item:
            
            Days Overdue: {item_context.get('days_overdue', 0)}
            Chase Count: {item_context.get('chase_count', 0)}
            Days Since Last Chase: {item_context.get('days_since_last_chase', 0)}
            Status: {item_context.get('status', 'pending')}
            Client Engagement: {item_context.get('engagement_level', 'medium')}
            Provider Reliability: {item_context.get('provider_reliability', 0.7)}
            
            Assess risk and provide recommendations.""")
        ])
        
        logger.debug(f"[analyze_stuck_score] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            stuck_score = result.get('stuck_score', 0.0)
            logger.info(f"[analyze_stuck_score] LLM stuck score: {stuck_score}")
            logger.info(f"[analyze_stuck_score] Risk factors: {result.get('risk_factors', [])}")
            logger.debug(f"[analyze_stuck_score] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"[analyze_stuck_score] LLM request failed: {e}", exc_info=True)
            logger.warning(f"[analyze_stuck_score] Falling back to rule-based calculation")
            fallback_result = {
                'stuck_score': min(item_context.get('chase_count', 0) * 0.2, 1.0),
                'risk_factors': ['Fallback calculation'],
                'recommendations': 'Monitor closely'
            }
            logger.info(f"[analyze_stuck_score] Fallback stuck score: {fallback_result['stuck_score']}")
            return fallback_result
    
    def process_natural_language_query(self, query: str, available_data: Dict) -> Dict:
        """
        Process natural language queries for insights
        Returns: {intent: str, parameters: Dict, confidence: float}
        """
        logger.info(f"[process_natural_language_query] Processing query: {query[:100]}...")
        logger.debug(f"[process_natural_language_query] Available data types: {list(available_data.keys())}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at understanding financial adviser queries.
            Parse natural language questions and extract intent and parameters.
            Common query types: investment analysis, client reviews, compliance, business metrics, follow-ups.
            Return JSON: {intent: str, parameters: Dict, confidence: float, suggested_endpoint: str}"""),
            HumanMessage(content=f"""Parse this query: "{query}"
            
            Available data types: {list(available_data.keys())}
            
            Extract the intent and parameters.""")
        ])
        
        logger.debug(f"[process_natural_language_query] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.json_parser
        try:
            result = chain.invoke({})
            logger.info(f"[process_natural_language_query] Query intent: {result.get('intent', 'unknown')}")
            logger.info(f"[process_natural_language_query] Confidence: {result.get('confidence', 0.0)}")
            logger.debug(f"[process_natural_language_query] Full LLM response: {json.dumps(result, default=str, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"[process_natural_language_query] LLM request failed: {e}", exc_info=True)
            fallback_result = {
                'intent': 'unknown',
                'parameters': {},
                'confidence': 0.0,
                'suggested_endpoint': None
            }
            logger.warning(f"[process_natural_language_query] Returning fallback result")
            return fallback_result
    
    def generate_insights_summary(self, query: str, results: List[Dict]) -> str:
        """
        Generate natural language summary of insights results
        """
        logger.info(f"[generate_insights_summary] Generating summary for query: {query[:100]}...")
        logger.debug(f"[generate_insights_summary] Number of results: {len(results)}")
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at summarizing financial data insights.
            Create clear, actionable summaries that help advisers understand key findings."""),
            HumanMessage(content=f"""Query: {query}
            
            Results: {str(results[:10])}  # Limit to first 10 for context
            
            Generate a clear, actionable summary.""")
        ])
        
        logger.debug(f"[generate_insights_summary] Sending request to Azure OpenAI")
        chain = prompt | self.llm | self.str_parser
        try:
            summary = chain.invoke({})
            logger.info(f"[generate_insights_summary] Successfully generated summary ({len(summary)} chars)")
            logger.debug(f"[generate_insights_summary] Summary preview: {summary[:200]}...")
            return summary
        except Exception as e:
            logger.error(f"[generate_insights_summary] LLM request failed: {e}", exc_info=True)
            fallback_summary = f"Found {len(results)} results for your query."
            logger.warning(f"[generate_insights_summary] Returning fallback summary")
            return fallback_summary
    
    # Fallback methods
    def _fallback_priority(self, item_context: Dict) -> Dict:
        """Fallback priority calculation"""
        days_overdue = item_context.get('days_overdue', 0)
        chase_count = item_context.get('chase_count', 0)
        
        if days_overdue > 10 or chase_count > 3:
            priority = 'urgent'
        elif days_overdue > 5 or chase_count > 1:
            priority = 'high'
        elif days_overdue > 0:
            priority = 'medium'
        else:
            priority = 'low'
        
        return {
            'priority': priority,
            'reasoning': 'Rule-based fallback',
            'urgency_score': min((days_overdue * 0.1 + chase_count * 0.15), 1.0)
        }
    
    def _fallback_communication(self, item_context: Dict, chase_count: int) -> Dict:
        """Fallback communication generation"""
        client_name = item_context.get('client_name', 'Client')
        first_name = client_name.split()[0] if client_name else 'Client'
        
        if chase_count == 0:
            subject = "Action Required"
            content = f"Hi {first_name},\n\nWe need your response to proceed. Please contact us.\n\nBest regards"
            tone = "friendly"
        elif chase_count == 1:
            subject = "Reminder"
            content = f"Hi {first_name},\n\nJust a reminder about the pending item.\n\nBest regards"
            tone = "professional"
        else:
            subject = "Urgent: Action Required"
            content = f"Hi {first_name},\n\nThis is urgent. Please respond as soon as possible.\n\nBest regards"
            tone = "urgent"
        
        return {
            'subject': subject,
            'content': content,
            'tone': tone
        }

