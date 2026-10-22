"""
Coursera Subject Scraper
Scrapes products by subject/topic to add subject information to each course.
Uses topic facet filter to categorize courses by subject area.
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


class CourseraSubjectScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.base_url = "https://www.coursera.org"
        self.graphql_endpoint = f"{self.base_url}/graphql-gateway?opname=Search"
        self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'apollographql-client-name': 'seo-entity-page',
            'apollographql-client-version': 'f2b799a8cfa7057c04a463edf3050fdde4949006',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/courses',
        })
        
        self.url_to_subject = {}
        self.graphql_query = self._get_graphql_query()
        
        # Subject mapping (as provided by user)
        self.subjects = {
            "Business": 4587,
            "Computer Science": 4080,
            "Information Technology": 3129,
            "Data Science": 2231,
            "Health": 1129,
            "Physical Science and Engineering": 1062,
            "Social Sciences": 880,
            "Arts and Humanities": 630,
            "Personal Development": 424,
            "Language Learning": 250,
            "Math and Logic": 128
        }
    
    def _get_graphql_query(self) -> str:
        """Get GraphQL query statement"""
        return """query Search($requests: [Search_Request!]!) {
  SearchResult {
    search(requests: $requests) {
      ...SearchResult
      __typename
    }
    __typename
  }
}

fragment SearchResult on Search_Result {
  elements {
    ...SearchHit
    __typename
  }
  pagination {
    cursor
    totalElements
    __typename
  }
  totalPages
  __typename
}

fragment SearchHit on Search_Hit {
  ...SearchProductHit
  __typename
}

fragment SearchProductHit on Search_ProductHit {
  id
  url
  __typename
}"""
    
    def search_by_subject(self, subject: str, cursor: str = "0", limit: int = 100) -> Optional[Dict]:
        """
        Call GraphQL Search API filtered by subject/topic
        
        Args:
            subject: Subject name (e.g., "Business", "Computer Science")
            cursor: Pagination cursor
            limit: Products per page
        """
        variables = {
            "requests": [
                {
                    "entityType": "PRODUCTS",
                    "limit": limit,
                    "facets": ["topic", "productTypeDescription"],
                    "sortBy": "BEST_MATCH",
                    "enableAutoAppliedFilters": False,
                    "facetFilters": [["topic:" + subject]],
                    "maxValuesPerFacet": 1000,
                    "cursor": str(cursor),
                    "query": ""
                }
            ]
        }
        
        payload = [{
            "operationName": "Search",
            "variables": variables,
            "query": self.graphql_query
        }]
        
        try:
            response = self.session.post(
                self.graphql_endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            return None
    
    def extract_urls(self, response_data: Dict) -> List[str]:
        """Extract product URLs from API response"""
        urls = []
        
        try:
            if isinstance(response_data, list) and len(response_data) > 0:
                data = response_data[0]
            else:
                data = response_data
            
            search_result = data.get('data', {}).get('SearchResult', {})
            search_results = search_result.get('search', [])
            
            if not search_results:
                return urls
            
            products_result = search_results[0]
            elements = products_result.get('elements', [])
            
            for element in elements:
                url = element.get('url')
                if url:
                    if url.startswith('/'):
                        full_url = f"{self.base_url}{url}"
                    elif url.startswith('http'):
                        full_url = url
                    else:
                        full_url = f"{self.base_url}/{url}"
                    urls.append(full_url)
            
        except Exception as e:
            pass
        
        return urls
    
    def get_pagination_info(self, response_data: Dict) -> Dict:
        """Extract pagination info"""
        info = {
            'nextCursor': None,
            'hasMore': False
        }
        
        try:
            if isinstance(response_data, list) and len(response_data) > 0:
                data = response_data[0]
            else:
                data = response_data
            
            search_result = data.get('data', {}).get('SearchResult', {})
            search_results = search_result.get('search', [])
            
            if search_results:
                products_result = search_results[0]
                pagination = products_result.get('pagination', {})
                info['nextCursor'] = pagination.get('cursor')
                info['hasMore'] = info['nextCursor'] is not None
                
        except Exception as e:
            pass
        
        return info
    
    def scrape_subject(self, subject: str, delay: float = 0.5) -> List[str]:
        """Scrape all URLs for a specific subject"""
        print(f"Scraping: {subject}...", end=" ", flush=True)
        
        urls = []
        cursor = "0"
        
        while True:
            response_data = self.search_by_subject(subject, cursor=cursor)
            
            if not response_data:
                print("Failed")
                break
            
            page_urls = self.extract_urls(response_data)
            urls.extend(page_urls)
            
            pagination_info = self.get_pagination_info(response_data)
            next_cursor = pagination_info['nextCursor']
            
            if not pagination_info['hasMore'] or not next_cursor or next_cursor == cursor:
                print(f"{len(urls)} URLs")
                break
            
            cursor = next_cursor
            
            if delay > 0:
                time.sleep(delay)
        
        return urls
    
    def scrape_all_subjects(self):
        """Scrape all subjects and create URL to subject mapping"""
        print("Starting subject scraping...\n")
        
        for subject in self.subjects.keys():
            urls = self.scrape_subject(subject)
            
            # Map each URL to its subject
            for url in urls:
                self.url_to_subject[url] = subject
            
            time.sleep(1)  # Delay between subjects
        
        print(f"\nComplete. Mapped {len(self.url_to_subject)} URLs to subjects")
    
    def save_subject_mapping(self, filename: str = "url_to_subject_mapping.json"):
        """Save URL to subject mapping"""
        output_path = Path(filename)
        
        data = {
            "total_mappings": len(self.url_to_subject),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "subjects": self.subjects,
            "mappings": self.url_to_subject
        }
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(self.url_to_subject)} URL-to-subject mappings to {filename}")


def main():
    """Main function"""
    scraper = CourseraSubjectScraper()
    scraper.scrape_all_subjects()
    
    if scraper.url_to_subject:
        scraper.save_subject_mapping()
    else:
        print("No mappings created")


if __name__ == "__main__":
    main()

