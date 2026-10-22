"""
Coursera Full Data Scraper
Fetches all product types (Courses, Specializations, Professional Certificates, etc.)
and saves complete product information
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional


class CourseraFullScraper:
    def __init__(self):
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
        
        self.products = []
        self.graphql_query = self._get_graphql_query()
    
    def _get_graphql_query(self) -> str:
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
    
    def search_products(self, cursor: str = "0", limit: int = 100) -> Optional[Dict]:

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
                    "facetFilters": [],  # Empty = all product types
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
                print(f"⚠️  API request failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Request error: {e}")
            return None
    
    def extract_products(self, response_data: Dict) -> List[Dict]:
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
                # Convert relative URL to full URL
                url = element.get('url')
                if url:
                    if url.startswith('/'):
                        element['url'] = f"{self.base_url}{url}"
                    elif not url.startswith('http'):
                        element['url'] = f"{self.base_url}/{url}"
                
                products.append(element)
            
        except Exception as e:
            print(f"⚠️  Error extracting products: {e}")
        
        return products
    
    def get_pagination_info(self, response_data: Dict) -> Dict:
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
            print(f"⚠️  Error parsing pagination: {e}")
        
        return info
    
    def scrape_all_products(self, max_limit: int = 100, delay: float = 0.5):

        print("=" * 80)
        print("🚀 Starting full product data scraping via GraphQL API")
        print("=" * 80)
        
        cursor = "0"
        page_num = 1
        total_products = None
        
        while True:
            print(f"\n📄 Fetching page {page_num} (cursor={cursor})...")
            
            response_data = self.search_products(cursor=cursor, limit=max_limit)
            
            if not response_data:
                print("   ❌ Failed to fetch data, stopping")
                break
            

            page_products = self.extract_products(response_data)
            

            self.products.extend(page_products)
            
            print(f"   ✅ Extracted: {len(page_products)} products")
            print(f"   📊 Total so far: {len(self.products)} products")
            

            pagination_info = self.get_pagination_info(response_data)
            
            if pagination_info['totalElements']:
                if total_products is None:
                    total_products = pagination_info['totalElements']
                    print(f"\n   🎯 Total products in database: {total_products:,}")
            

            next_cursor = pagination_info['nextCursor']
            
            if not pagination_info['hasMore'] or not next_cursor or next_cursor == cursor:
                print("\n   ✅ Reached last page")
                break
            
            cursor = next_cursor
            page_num += 1
            
            if delay > 0:
                time.sleep(delay)
        
        print(f"\n" + "=" * 80)
        print(f"🎉 Scraping complete!")
        print(f"   📊 Total products: {len(self.products)}")
        if total_products:
            coverage = (len(self.products) / total_products * 100) if total_products > 0 else 0
            print(f"   📈 Database total: {total_products:,}")
            print(f"   📊 Coverage: {coverage:.2f}%")
        print("=" * 80)
    
    def save_products(self, filename: str = "coursera_all_products.json"):
        output_path = Path(filename)
        
        data = {
            "total_count": len(self.products),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scraped_method": "GraphQL API - All Product Types",
            "base_url": self.base_url,
            "products": self.products
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved {len(self.products)} products to {filename}")
        
        self._save_summary()
    
    def _save_summary(self):
        summary = {}
        
        for product in self.products:
            product_type = product.get('productType', 'UNKNOWN')
            if product_type not in summary:
                summary[product_type] = 0
            summary[product_type] += 1
        
        summary_file = Path("product_type_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary_by_type": summary,
                "total": len(self.products)
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved product type summary to {summary_file}")
        print(f"\n📊 Product types breakdown:")
        for ptype, count in sorted(summary.items()):
            print(f"   {ptype}: {count}")


def main():
    scraper = CourseraFullScraper()
    scraper.scrape_all_products(max_limit=100, delay=0.5)
    
    if scraper.products:
        scraper.save_products()
        print(f"\n🎉 Success! Scraped {len(scraper.products)} products with full data")
    else:
        print("\n⚠️  No products scraped")


if __name__ == "__main__":
    main()

