"""
API-based AI topic classification module.

Provides AI topic detection using LLM APIs with keyword-based fallback.
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

                                           
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass                                                          

from logger import get_logger

                   
logger = get_logger(__name__)

                           
try:
    import openai
    OPENAI_AVAILABLE = True
    logger.info("OpenAI library available for API-based classification")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    logger.info("Anthropic library available for API-based classification")
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not available")


@dataclass
class AITopicResult:
    """Result of AI topic classification."""
    is_ai_topic: bool
    confidence: float
    topic: Optional[str]
    explanation: str
    keywords: List[str]


class APIBasedAITopicClassifier:
    """API-based AI topic classifier using LLM APIs."""
    
    def __init__(self):
        """Initialize the API-based AI topic classifier."""
        self.logger = get_logger(__name__)
        
        self.ai_topics = [
            "AI Research and Development",
            "AI Ethics and Regulations", 
            "AI Safety and Governance",
            "AI Business and Industry",
            "AI Language Models and NLP",
            "AI Robotics and Automation",
            "AI Healthcare and Medical",
            "AI Education and Training",
            "AI Cybersecurity and Privacy",
            "AI Computer Vision",
            "AI Data Science and Analytics",
            "AI Neural Networks and Deep Learning",
            "AI Applications and Deployment",
            "AI Technology and Infrastructure"
        ]
        
                                
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_api_clients()
        
        self.logger.info("API-based AI topic classifier initialized")
    
    def _initialize_api_clients(self):
        """Initialize API clients if API keys are available."""
                                         
        openai_api_key = os.getenv('OPENAI_API_KEY')
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        self.logger.info(f"API Key Check - OPENAI_API_KEY present: {bool(openai_api_key and openai_api_key.strip())}, "
                        f"ANTHROPIC_API_KEY present: {bool(anthropic_api_key and anthropic_api_key.strip())}")
        
        if openai_api_key and openai_api_key.strip() and OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key.strip())
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI client: {e}")
        
                                            
        if anthropic_api_key and anthropic_api_key.strip() and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key.strip())
                self.logger.info("Anthropic client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        if not self.openai_client and not self.anthropic_client:
            self.logger.warning("No API clients available - will use fallback classification")
            if not openai_api_key or not openai_api_key.strip():
                self.logger.warning("OPENAI_API_KEY is missing or empty in environment")
            if not anthropic_api_key or not anthropic_api_key.strip():
                self.logger.debug("ANTHROPIC_API_KEY is missing or empty (this is OK if not using Anthropic)")
    
    def classify_article(self, text: str, title: str = "") -> AITopicResult:
        """
        Classify whether an article is about AI topics using API-based LLM analysis.
        
        Args:
            text: Full article text content
            title: Article title (optional, used for additional context)
            
        Returns:
            AITopicResult with classification results
        """
                                            
        if self.openai_client:
            return self._classify_with_openai(text, title)
        elif self.anthropic_client:
            return self._classify_with_anthropic(text, title)
        else:
            return self._classify_with_fallback(text, title)
    
    def _classify_with_openai(self, text: str, title: str = "") -> AITopicResult:
        """Classify article using OpenAI API."""
        try:
            full_text = f"Title: {title}\n\nContent: {text}".strip()
            
            prompt = f"""Analyze this article and determine if it is primarily about artificial intelligence (AI) or not.

Article to analyze:
{full_text}

Please provide your analysis in the following JSON format:
{{
    "is_ai_topic": true/false,
    "confidence": 0.0-1.0,
    "topic": "specific AI topic or null",
    "explanation": "brief explanation of your reasoning",
    "keywords": ["key", "ai-related", "terms", "found"]
}}

AI Topics to consider:
- AI Research and Development
- AI Ethics and Regulations
- AI Business and Industry  
- AI Language Models and NLP
- AI Robotics and Automation
- AI Healthcare and Medical
- AI Computer Vision
- AI Technology and Infrastructure

An article should be considered AI-related if it primarily discusses artificial intelligence, machine learning, AI companies, AI applications, AI research, or AI technology. Articles that only mention AI briefly or in passing should be considered non-AI.

Respond only with the JSON format."""

                             
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are an expert AI researcher who can accurately classify whether articles are about artificial intelligence topics or not."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    return AITopicResult(
                        is_ai_topic=result_data.get('is_ai_topic', False),
                        confidence=result_data.get('confidence', 0.5),
                        topic=result_data.get('topic'),
                        explanation=f"OpenAI: {result_data.get('explanation', 'AI classification completed')}",
                        keywords=result_data.get('keywords', [])
                    )
                except json.JSONDecodeError:
                    pass
            
            return self._parse_openai_response(response_text, full_text)
            
        except Exception as e:
            self.logger.error(f"OpenAI classification failed: {e}")
            return self._classify_with_fallback(text, title)
    
    def _classify_with_anthropic(self, text: str, title: str = "") -> AITopicResult:
        """Classify article using Anthropic API."""
        try:
                                    
            full_text = f"Title: {title}\n\nContent: {text}".strip()
            
                                                          
            prompt = f"""Analyze this article and determine if it is primarily about artificial intelligence (AI) or not.

Article to analyze:
{full_text}

Please analyze whether this article is primarily about artificial intelligence topics. Consider:
- AI Research and Development
- AI Ethics and Regulations  
- AI Business and Industry
- AI Language Models and NLP
- AI Robotics and Automation
- AI Healthcare and Medical
- AI Computer Vision
- AI Technology and Infrastructure

Respond in JSON format:
{{
    "is_ai_topic": true/false,
    "confidence": 0.0-1.0,
    "topic": "specific AI topic or null",
    "explanation": "brief explanation",
    "keywords": ["key", "terms"]
}}"""

                                
            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
                                
            response_text = response.content[0].text.strip()
            
                                                   
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    return AITopicResult(
                        is_ai_topic=result_data.get('is_ai_topic', False),
                        confidence=result_data.get('confidence', 0.5),
                        topic=result_data.get('topic'),
                        explanation=f"Claude: {result_data.get('explanation', 'AI classification completed')}",
                        keywords=result_data.get('keywords', [])
                    )
                except json.JSONDecodeError:
                    pass
            
                                                       
            return self._parse_anthropic_response(response_text, full_text)
            
        except Exception as e:
            self.logger.error(f"Anthropic classification failed: {e}")
                                               
            return self._classify_with_fallback(text, title)
    
    def _parse_openai_response(self, response_text: str, full_text: str) -> AITopicResult:
        """Parse OpenAI response manually if JSON parsing fails."""
        response_lower = response_text.lower()
        
                                                 
        is_ai_topic = any(indicator in response_lower for indicator in [
            'true', 'yes', 'ai-related', 'artificial intelligence', 'primarily about ai'
        ])
        
        confidence = 0.8 if is_ai_topic else 0.7
        topic = self._extract_topic_from_response(response_text) if is_ai_topic else None
        keywords = self._extract_keywords_from_text(full_text)
        
        return AITopicResult(
            is_ai_topic=is_ai_topic,
            confidence=confidence,
            topic=topic,
            explanation=f"OpenAI manual parsing: {response_text[:100]}...",
            keywords=keywords
        )
    
    def _parse_anthropic_response(self, response_text: str, full_text: str) -> AITopicResult:
        """Parse Anthropic response manually if JSON parsing fails."""
        response_lower = response_text.lower()
        
                                                 
        is_ai_topic = any(indicator in response_lower for indicator in [
            'true', 'yes', 'ai-related', 'artificial intelligence', 'primarily about ai'
        ])
        
        confidence = 0.8 if is_ai_topic else 0.7
        topic = self._extract_topic_from_response(response_text) if is_ai_topic else None
        keywords = self._extract_keywords_from_text(full_text)
        
        return AITopicResult(
            is_ai_topic=is_ai_topic,
            confidence=confidence,
            topic=topic,
            explanation=f"Claude manual parsing: {response_text[:100]}...",
            keywords=keywords
        )
    
    def _extract_topic_from_response(self, response_text: str) -> str:
        """Extract AI topic from the response text."""
        response_lower = response_text.lower()
        
        for topic in self.ai_topics:
            if topic.lower() in response_lower:
                return topic
        
        return "AI Technology and Infrastructure"           
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract AI-related keywords from the text."""
        text_lower = text.lower()
        
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'openai', 'chatgpt', 'gpt', 'claude', 'transformer', 'llm', 
            'large language model', 'natural language processing', 'computer vision',
            'generative ai', 'ai model', 'ai system'
        ]
        
        found_keywords = []
        for keyword in ai_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:5]
    
    def _classify_with_fallback(self, text: str, title: str = "") -> AITopicResult:
        """Fallback classification using keyword matching."""
        full_text = f"{title} {text}"
        text_lower = full_text.lower()
        
        core_ai_terms = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'openai', 'chatgpt', 'gpt-4', 'gpt4', 'claude', 'transformer', 'llm', 
            'large language model', 'natural language processing', 'computer vision',
            'generative ai', 'ai model', 'ai system', 'ai research', 'ai technology'
        ]
        
        ai_count = sum(1 for term in core_ai_terms if term in text_lower)
        is_ai_topic = ai_count >= 3
        confidence = min(0.8, 0.4 + (ai_count * 0.1))
        
        topic = None
        if is_ai_topic:
            if any(term in text_lower for term in ['chatgpt', 'gpt', 'claude', 'llm']):
                topic = "AI Language Models and NLP"
            elif any(term in text_lower for term in ['openai', 'anthropic']):
                topic = "AI Business and Industry"
            else:
                topic = "AI Technology and Infrastructure"
        
        keywords = self._extract_keywords_from_text(full_text)
        
        explanation = f"Fallback classification: {ai_count} AI terms found"
        if not is_ai_topic:
            explanation += " - not sufficient for AI classification"
        
        return AITopicResult(
            is_ai_topic=is_ai_topic,
            confidence=confidence,
            topic=topic,
            explanation=explanation,
            keywords=keywords
        )


def classify_articles_ai_topics(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classify a list of articles for AI topics using API-based processing.
    """
    classifier = APIBasedAITopicClassifier()
    logger = get_logger(__name__)
    
    logger.info(f"Starting API-based AI topic classification for {len(articles)} articles")
    
    classified_articles = []
    
                                                        
    for i, article in enumerate(articles, 1):
        try:
                                        
            text = article.get('text', '')
            title = article.get('title', '')
            
            logger.info(f"Processing article {i}/{len(articles)}: '{title[:50]}...'")
            
            if not text:
                logger.warning(f"Article {article.get('url', 'unknown')} has no text content")
                article['ai_topic_analysis'] = {
                    'is_ai_topic': False,
                    'confidence': 0.0,
                    'topic': None,
                    'explanation': 'No text content available',
                    'keywords': []
                }
                classified_articles.append(article)
                continue
            
                                                      
            result = classifier.classify_article(text, title)
            
                                              
            article['ai_topic_analysis'] = {
                'is_ai_topic': result.is_ai_topic,
                'confidence': result.confidence,
                'topic': result.topic,
                'explanation': result.explanation,
                'keywords': result.keywords
            }
            
            logger.info(f"Article '{title[:50]}...' classified as AI: {result.is_ai_topic} (confidence: {result.confidence:.2f})")
            
            classified_articles.append(article)
            
                                                          
            if classifier.openai_client or classifier.anthropic_client:
                time.sleep(0.1)                                 
            
        except Exception as e:
            logger.error(f"Error classifying article {article.get('url', 'unknown')}: {e}")
                                  
            article['ai_topic_analysis'] = {
                'is_ai_topic': False,
                'confidence': 0.0,
                'topic': None,
                'explanation': f'Classification failed: {str(e)}',
                'keywords': []
            }
            classified_articles.append(article)
    
                       
    ai_count = sum(1 for article in classified_articles 
                   if article.get('ai_topic_analysis', {}).get('is_ai_topic', False))
    
    logger.info(f"API-based AI topic classification completed: {ai_count}/{len(articles)} articles are AI-related")
    
    return classified_articles


def get_ai_topic_summary(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a summary of AI topic classification results.
    """
    ai_articles = [article for article in articles 
                   if article.get('ai_topic_analysis', {}).get('is_ai_topic', False)]
    
    if not ai_articles:
        return {
            'total_articles': len(articles),
            'ai_articles': 0,
            'ai_percentage': 0.0,
            'topics': {},
            'keywords': []
        }
    
                  
    topics = {}
    all_keywords = []
    
    for article in ai_articles:
        analysis = article.get('ai_topic_analysis', {})
        topic = analysis.get('topic')
        keywords = analysis.get('keywords', [])
        
        if topic:
            topics[topic] = topics.get(topic, 0) + 1
        
        all_keywords.extend(keywords)
    
                              
    from collections import Counter
    keyword_counts = Counter(all_keywords)
    top_keywords = [keyword for keyword, count in keyword_counts.most_common(10)]
    
    return {
        'total_articles': len(articles),
        'ai_articles': len(ai_articles),
        'ai_percentage': len(ai_articles) / len(articles) * 100,
        'topics': topics,
        'keywords': top_keywords
    }