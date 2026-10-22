"""
通过 GraphQL API 获取所有 Coursera 课程 URL
绕过网页的 84 页限制，直接调用 API 获取所有课程
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional


class CourseraGraphQLScraper:
    def __init__(self):
        """初始化 GraphQL 爬虫"""
        self.base_url = "https://www.coursera.org"
        self.graphql_endpoint = f"{self.base_url}/graphql-gateway?opname=Search"
        self.session = requests.Session()
        
        # 设置默认请求头（模拟浏览器）
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'apollographql-client-name': 'seo-entity-page',
            'apollographql-client-version': 'f2b799a8cfa7057c04a463edf3050fdde4949006',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/courses',
        })
        
        self.course_urls = []
        self.graphql_query = self._get_graphql_query()
    
    def _get_graphql_query(self) -> str:
        """获取 GraphQL 查询语句"""
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
  facets {
    ...SearchFacets
    __typename
  }
  pagination {
    cursor
    totalElements
    __typename
  }
  totalPages
  source {
    indexName
    recommender {
      context
      hash
      __typename
    }
    __typename
  }
  autoAppliedFilters
  __typename
}

fragment SearchHit on Search_Hit {
  ...SearchArticleHit
  ...SearchProductHit
  ...SearchSuggestionHit
  __typename
}

fragment SearchArticleHit on Search_ArticleHit {
  aeName
  careerField
  category
  createdByName
  firstPublishedAt
  id
  internalContentEpic
  internalProductLine
  internalTargetKw
  introduction
  islocalized
  lastPublishedAt
  localizedCountryCd
  localizedLanguageCd
  name
  subcategory
  topics
  url
  skill: skills
  __typename
}

fragment SearchProductHit on Search_ProductHit {
  avgProductRating
  cobrandingEnabled
  completions
  duration
  id
  imageUrl
  isCourseFree
  isCreditEligible
  isNewContent
  isPartOfCourseraPlus
  name
  numProductRatings
  partners
  productCard {
    ...SearchProductCard
    __typename
  }
  productDifficultyLevel
  productDuration
  productType
  skills
  url
  __typename
}

fragment SearchSuggestionHit on Search_SuggestionHit {
  id
  name
  score
  __typename
}

fragment SearchProductCard on ProductCard_ProductCard {
  id
  canonicalType
  marketingProductType
  badges
  productTypeAttributes {
    ... on ProductCard_Specialization {
      ...SearchProductCardSpecialization
      __typename
    }
    ... on ProductCard_Course {
      ...SearchProductCardCourse
      __typename
    }
    __typename
  }
  __typename
}

fragment SearchProductCardSpecialization on ProductCard_Specialization {
  isPathwayContent
  __typename
}

fragment SearchProductCardCourse on ProductCard_Course {
  isPathwayContent
  rating
  reviewCount
  __typename
}

fragment SearchFacets on Search_Facet {
  name
  nameDisplay
  valuesAndCounts {
    ...ValuesAndCounts
    __typename
  }
  __typename
}

fragment ValuesAndCounts on Search_FacetValueAndCount {
  count
  value
  valueDisplay
  __typename
}"""
    
    def _get_csrf_token(self) -> Optional[str]:
        """获取 CSRF token（从主页）"""
        try:
            response = self.session.get(f"{self.base_url}/courses")
            # CSRF token 通常在 cookies 或页面中
            # 这里简化处理，实际可能需要解析页面
            return None
        except:
            return None
    
    def search_courses(self, cursor: str = "0", limit: int = 100) -> Optional[Dict]:
        """
        调用 GraphQL Search API 搜索课程
        
        Args:
            cursor: 分页游标（从 "0" 开始）
            limit: 每页返回的课程数量
            
        Returns:
            API 响应数据，或 None 如果失败
        """
        variables = {
            "requests": [
                {
                    "entityType": "PRODUCTS",
                    "limit": limit,
                    "facets": [
                        "cost",
                        "topic",
                        "skills",
                        "productDifficultyLevel",
                        "productDuration",
                        "productTypeDescription",
                        "partners",
                        "language",
                        "subtitleLanguage"
                    ],
                    "sortBy": "BEST_MATCH",
                    "enableAutoAppliedFilters": False,
                    "facetFilters": [["productTypeDescription:Courses"]],
                    "maxValuesPerFacet": 1000,
                    "cursor": str(cursor),
                    "query": ""
                },
                {
                    "entityType": "SUGGESTIONS",
                    "limit": 10,
                    "maxValuesPerFacet": 1000,
                    "facetFilters": [],
                    "cursor": "0",
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
                data = response.json()
                return data
            else:
                print(f"⚠️  API 请求失败: HTTP {response.status_code}")
                print(f"   响应: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"⚠️  请求出错: {e}")
            return None
    
    def extract_course_urls(self, response_data: Dict) -> List[str]:
        """从 API 响应中提取课程 URL"""
        urls = []
        
        try:
            # 解析响应结构
            if isinstance(response_data, list) and len(response_data) > 0:
                data = response_data[0]
            else:
                data = response_data
            
            search_result = data.get('data', {}).get('SearchResult', {})
            search_results = search_result.get('search', [])
            
            if not search_results:
                return urls
            
            # 第一个结果应该是产品搜索结果
            products_result = search_results[0]
            elements = products_result.get('elements', [])
            
            for element in elements:
                # 只提取课程（productType 应该是 "COURSE"）
                url = element.get('url')
                if url:
                    # 确保是完整的 URL
                    if url.startswith('/'):
                        full_url = f"{self.base_url}{url}"
                    elif url.startswith('http'):
                        full_url = url
                    else:
                        full_url = f"{self.base_url}/{url}"
                    
                    # 只添加 /learn/ 路径的课程
                    if '/learn/' in full_url:
                        urls.append(full_url)
            
        except Exception as e:
            print(f"⚠️  提取 URL 时出错: {e}")
        
        return urls
    
    def get_pagination_info(self, response_data: Dict) -> Dict:
        """从响应中提取分页信息"""
        info = {
            'totalElements': None,
            'totalPages': None,
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
                info['totalPages'] = products_result.get('totalPages')
                info['hasMore'] = info['nextCursor'] is not None and info['nextCursor'] != '0'
                
        except Exception as e:
            print(f"⚠️  解析分页信息时出错: {e}")
        
        return info
    
    def scrape_all_courses(self, max_limit: int = 100, delay: float = 1.0):
        """
        爬取所有课程
        
        Args:
            max_limit: 每页最大返回数量（API 可能有上限）
            delay: 每次请求之间的延迟（秒）
        """
        print("=" * 80)
        print("🚀 开始通过 GraphQL API 获取所有课程 URL")
        print("=" * 80)
        
        cursor = "0"
        page_num = 1
        total_courses = None
        
        while True:
            print(f"\n📄 正在获取第 {page_num} 页 (cursor={cursor})...")
            
            # 调用 API
            response_data = self.search_courses(cursor=cursor, limit=max_limit)
            
            if not response_data:
                print("   ❌ 无法获取数据，停止爬取")
                break
            
            # 提取课程 URL
            page_urls = self.extract_course_urls(response_data)
            
            # 去重并添加
            new_urls = []
            for url in page_urls:
                if url not in self.course_urls:
                    self.course_urls.append(url)
                    new_urls.append(url)
            
            print(f"   ✅ 本页提取: {len(page_urls)} 个 URL，新增: {len(new_urls)} 个")
            print(f"   📊 累计总数: {len(self.course_urls)} 个课程 URL")
            
            # 获取分页信息
            pagination_info = self.get_pagination_info(response_data)
            
            if pagination_info['totalElements']:
                if total_courses is None:
                    total_courses = pagination_info['totalElements']
                    print(f"\n   🎯 发现总课程数: {total_courses:,} 门课程")
            
            # 检查是否还有更多数据
            next_cursor = pagination_info['nextCursor']
            
            if not pagination_info['hasMore'] or not next_cursor or next_cursor == cursor:
                print("\n   ✅ 已到达最后一页")
                break
            
            cursor = next_cursor
            page_num += 1
            
            # 延迟，避免请求过快
            if delay > 0:
                time.sleep(delay)
        
        print(f"\n" + "=" * 80)
        print(f"🎉 爬取完成！")
        print(f"   📊 总共获取: {len(self.course_urls)} 个课程 URL")
        if total_courses:
            print(f"   📈 数据库总数: {total_courses:,} 门课程")
            coverage = (len(self.course_urls) / total_courses * 100) if total_courses > 0 else 0
            print(f"   📊 覆盖率: {coverage:.2f}%")
        print("=" * 80)
    
    def save_urls(self, filename: str = "course_urls_graphql.json"):
        """保存课程 URL 到文件"""
        output_path = Path(filename)
        
        data = {
            "total_count": len(self.course_urls),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scraped_method": "GraphQL API",
            "base_url": self.base_url,
            "urls": sorted(list(set(self.course_urls)))
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已保存 {len(self.course_urls)} 个课程 URL 到 {filename}")
        
        # 同时保存为文本文件
        txt_path = Path("course_urls_graphql.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            for url in sorted(set(self.course_urls)):
                f.write(url + "\n")
        print(f"✅ 已保存为文本格式: {txt_path}")


def main():
    """主函数"""
    scraper = CourseraGraphQLScraper()
    
    # 尝试较大的 limit 值来减少请求次数
    # 如果 API 有限制，会自动回退
    scraper.scrape_all_courses(max_limit=100, delay=0.5)
    
    if scraper.course_urls:
        scraper.save_urls()
        print(f"\n🎉 成功！共获取 {len(scraper.course_urls)} 个课程 URL")
    else:
        print("\n⚠️  未获取到任何课程 URL")


if __name__ == "__main__":
    main()

