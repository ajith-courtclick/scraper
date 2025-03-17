import logging
import random
import time
from typing import Optional, Dict, Any, List

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.exceptions import RequestException
from tqdm import tqdm

from config.settings import (
    USER_AGENTS,
    REQUEST_TIMEOUT,
    RETRY_TIMES,
    RATE_LIMIT,
    PROXY_ENABLED,
    PROXY_API_KEY
)

class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent = UserAgent()
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for the scraper."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_headers(self) -> Dict[str, str]:
        """Generate request headers with rotating user agent."""
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration if enabled."""
        if PROXY_ENABLED and PROXY_API_KEY:
            return {
                'http': f'http://{PROXY_API_KEY}@proxy.scraperapi.com:8001',
                'https': f'http://{PROXY_API_KEY}@proxy.scraperapi.com:8001'
            }
        return None

    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Make an HTTP request with retry logic and rate limiting.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if all retries fail
        """
        for attempt in range(RETRY_TIMES):
            try:
                # Apply rate limiting
                time.sleep(RATE_LIMIT['min_time_between_requests'])
                
                # Prepare request
                kwargs['headers'] = kwargs.get('headers', self.get_headers())
                kwargs['proxies'] = kwargs.get('proxies', self.get_proxy())
                kwargs['timeout'] = kwargs.get('timeout', REQUEST_TIMEOUT)
                
                # Make request
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == RETRY_TIMES - 1:
                    self.logger.error(f"All retry attempts failed for {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html_content, 'lxml')

    def scrape_urls(self, urls: List[str], parser_func: callable) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with progress bar.
        
        Args:
            urls: List of URLs to scrape
            parser_func: Function to parse each response
            
        Returns:
            List of parsed results
        """
        results = []
        
        for url in tqdm(urls, desc="Scraping URLs"):
            response = self.make_request(url)
            if response:
                try:
                    parsed_data = parser_func(response)
                    if parsed_data:
                        results.append(parsed_data)
                except Exception as e:
                    self.logger.error(f"Error parsing {url}: {str(e)}")
                    
        return results 