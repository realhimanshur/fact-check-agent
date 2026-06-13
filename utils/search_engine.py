"""
Search Engine Module
Handles live web search using Tavily API
"""

import os
import logging
from typing import List, Dict, Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Live web search handler using Tavily API
    Falls back to alternative APIs if primary fails
    """
    
    def __init__(self):
        """Initialize search engine with API credentials"""
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
        
        # Determine available search engine
        if self.tavily_api_key:
            self.engine = 'tavily'
            logger.info("Using Tavily Search API")
        elif self.serper_api_key:
            self.engine = 'serper'
            logger.info("Using Serper API")
        elif self.brave_api_key:
            self.engine = 'brave'
            logger.info("Using Brave Search API")
        else:
            raise ValueError(
                "No search API key found. Please set one of: "
                "TAVILY_API_KEY, SERPER_API_KEY, or BRAVE_API_KEY"
            )
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the web for information
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        try:
            if self.engine == 'tavily':
                return self._search_tavily(query, max_results)
            elif self.engine == 'serper':
                return self._search_serper(query, max_results)
            elif self.engine == 'brave':
                return self._search_brave(query, max_results)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def _search_tavily(self, query: str, max_results: int) -> List[Dict]:
        """Search using Tavily API"""
        try:
            url = "https://api.tavily.com/search"
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('content', '')
                })
            
            # Add answer if available
            if data.get('answer'):
                results.insert(0, {
                    'title': 'AI Summary',
                    'url': '',
                    'snippet': data['answer']
                })
            
            logger.info(f"Tavily search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            raise
    
    def _search_serper(self, query: str, max_results: int) -> List[Dict]:
        """Search using Serper API"""
        try:
            url = "https://google.serper.dev/search"
            
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': max_results
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # Add answer box if available
            if data.get('answerBox'):
                answer = data['answerBox']
                results.append({
                    'title': answer.get('title', 'Answer'),
                    'url': answer.get('link', ''),
                    'snippet': answer.get('answer', answer.get('snippet', ''))
                })
            
            # Add organic results
            for item in data.get('organic', [])[:max_results]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
            
            logger.info(f"Serper search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Serper search error: {str(e)}")
            raise
    
    def _search_brave(self, query: str, max_results: int) -> List[Dict]:
        """Search using Brave Search API"""
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            
            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'q': query,
                'count': max_results
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            for item in data.get('web', {}).get('results', [])[:max_results]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('description', '')
                })
            
            logger.info(f"Brave search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Brave search error: {str(e)}")
            raise