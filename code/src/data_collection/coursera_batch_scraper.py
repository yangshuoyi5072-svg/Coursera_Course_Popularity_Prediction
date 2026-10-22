"""
Coursera Batch Scraper
Fetches products by different filter conditions to bypass 10,000 limit.
Each filter batch should have < 10,000 products to get complete data.
Then merges all results together.
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Set


class CourseraBatchScraper:
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
        
        self.all_products = []
        self.seen_ids: Set[str] = set()
        self.graphql_query = self._get_graphql_query()
    
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
  name
  url
  productType
  avgProductRating
  numProductRatings
  partners
  partnerLogos
  productDifficultyLevel
  productDuration
  duration
  isCourseFree
  isPartOfCourseraPlus
  isNewContent
  isCreditEligible
  skills
  imageUrl
  tagline
  videosInLesson
  productCard {
    id
    canonicalType
    marketingProductType
    badges
    productTypeAttributes {
      ... on ProductCard_Specialization {
        isPathwayContent
        __typename
      }
      ... on ProductCard_Course {
        isPathwayContent
        rating
        reviewCount
        __typename
      }
      __typename
    }
    __typename
  }
  cobrandingEnabled
  completions
  translatedName
  translatedSkills
  parentCourseName
  parentLessonName
  fullyTranslatedLanguages
  subtitlesOnlyLanguages
  __typename
}"""
    
    def search_products(self, facet_filters: List[List[str]], cursor: str = "0", limit: int = 100) -> Optional[Dict]:
        """
        Call GraphQL Search API with custom filters
        
        Args:
            facet_filters: Filter conditions, e.g. [["productTypeDescription:Courses"]]
            cursor: Pagination cursor
            limit: Products per page
        """
        variables = {
            "requests": [
                {
                    "entityType": "PRODUCTS",
                    "limit": limit,
                    "facets": [
                        "cost", "topic", "skills", "productDifficultyLevel",
                        "productDuration", "productTypeDescription", "partners",
                        "language", "subtitleLanguage"
                    ],
                    "sortBy": "BEST_MATCH",
                    "enableAutoAppliedFilters": False,
                    "facetFilters": facet_filters,
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
    
    def extract_products(self, response_data: Dict) -> List[Dict]:
        """Extract products from API response"""
        products = []
        
        try:
            if isinstance(response_data, list) and len(response_data) > 0:
                data = response_data[0]
            else:
                data = response_data
            
            search_result = data.get('data', {}).get('SearchResult', {})
            search_results = search_result.get('search', [])
            
            if not search_results:
                return products
            
            products_result = search_results[0]
            elements = products_result.get('elements', [])
            
            for element in elements:
                url = element.get('url')
                if url:
                    if url.startswith('/'):
                        element['url'] = f"{self.base_url}{url}"
                    elif not url.startswith('http'):
                        element['url'] = f"{self.base_url}/{url}"
                
                products.append(element)
            
        except Exception as e:
            pass
        
        return products
    
    def get_pagination_info(self, response_data: Dict) -> Dict:
        """Extract pagination info"""
        info = {
            'totalElements': None,
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
                
                info['totalElements'] = pagination.get('totalElements')
                info['nextCursor'] = pagination.get('cursor')
                info['hasMore'] = info['nextCursor'] is not None
                
        except Exception as e:
            pass
        
        return info
    
    def scrape_with_filter(self, filter_name: str, facet_filters: List[List[str]], max_limit: int = 100, delay: float = 0.5) -> List[Dict]:
        """
        Scrape products with a specific filter
        
        Returns:
            List of products (may be capped at 10,000)
        """
        print(f"Scraping: {filter_name}...", end=" ", flush=True)
        
        products = []
        cursor = "0"
        page_num = 1
        
        while True:
            response_data = self.search_products(facet_filters, cursor=cursor, limit=max_limit)
            
            if not response_data:
                print("Failed")
                break
            
            page_products = self.extract_products(response_data)
            products.extend(page_products)
            
            pagination_info = self.get_pagination_info(response_data)
            next_cursor = pagination_info['nextCursor']
            
            if not pagination_info['hasMore'] or not next_cursor or next_cursor == cursor:
                print(f"{len(products)} products")
                break
            
            cursor = next_cursor
            page_num += 1
            
            if delay > 0:
                time.sleep(delay)
        
        return products
    
    def add_products_deduplicated(self, new_products: List[Dict]):
        """Add products to main list, avoiding duplicates by ID"""
        added_count = 0
        
        for product in new_products:
            product_id = product.get('id')
            if product_id and product_id not in self.seen_ids:
                self.seen_ids.add(product_id)
                self.all_products.append(product)
                added_count += 1
        
        return added_count
    
    def scrape_all_batches(self):
        """Scrape products in batches using different filters"""
        print("Starting batch scraping...\n")
        
        # Define filter batches
        # Courses are split by difficulty level since they exceed 10,000
        # Other types don't exceed 10,000, so we can get them all at once
        filter_batches = [
            # Courses split by difficulty level
            # Format: Each inner array represents AND conditions
            {
                "name": "Courses - Beginner",
                "filters": [
                    ["productTypeDescription:Courses"],
                    ["productDifficultyLevel:BEGINNER"]
                ]
            },
            {
                "name": "Courses - Intermediate",
                "filters": [
                    ["productTypeDescription:Courses"],
                    ["productDifficultyLevel:INTERMEDIATE"]
                ]
            },
            {
                "name": "Courses - Advanced",
                "filters": [
                    ["productTypeDescription:Courses"],
                    ["productDifficultyLevel:ADVANCED"]
                ]
            },
            {
                "name": "Courses - Mixed",
                "filters": [
                    ["productTypeDescription:Courses"],
                    ["productDifficultyLevel:MIXED"]
                ]
            },
            # Other product types (no need to split)
            {
                "name": "Specializations",
                "filters": [["productTypeDescription:Specializations"]]
            },
            {
                "name": "Professional Certificates",
                "filters": [["productTypeDescription:Professional Certificates"]]
            },
            {
                "name": "Guided Projects",
                "filters": [["productTypeDescription:Guided Projects"]]
            },
            {
                "name": "Projects",
                "filters": [["productTypeDescription:Projects"]]
            },
            {
                "name": "Degrees",
                "filters": [["productTypeDescription:Degrees"]]
            },
        ]
        
        batch_results = {}
        
        for batch in filter_batches:
            products = self.scrape_with_filter(
                batch["name"],
                batch["filters"],
                max_limit=100,
                delay=0.5
            )
            
            added = self.add_products_deduplicated(products)
            batch_results[batch["name"]] = {
                "scraped": len(products),
                "added": added,
                "duplicates": len(products) - added
            }
            
            time.sleep(1)  # Delay between batches
        
        print(f"\nComplete. Total unique products: {len(self.all_products)}")
        
        return batch_results
    
    def save_products(self, filename: str = "coursera_all_products_batch.json"):
        """Save all products to file"""
        output_path = Path(filename)
        
        data = {
            "total_count": len(self.all_products),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scraped_method": "GraphQL API - Batch Scraping (bypass 10K limit)",
            "base_url": self.base_url,
            "products": self.all_products
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(self.all_products)} products to {filename}")
        
        # Save summary by product type
        self._save_summary()
    
    def _save_summary(self):
        """Save summary statistics"""
        summary = {}
        
        for product in self.all_products:
            product_type = product.get('productType', 'UNKNOWN')
            if product_type not in summary:
                summary[product_type] = 0
            summary[product_type] += 1
        
        summary_file = Path("product_type_summary_batch.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary_by_type": summary,
                "total": len(self.all_products)
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Saved summary to {summary_file}")


def main():
    """Main function"""
    scraper = CourseraBatchScraper()
    scraper.scrape_all_batches()
    
    if scraper.all_products:
        scraper.save_products()
    else:
        print("No products scraped")


if __name__ == "__main__":
    main()

