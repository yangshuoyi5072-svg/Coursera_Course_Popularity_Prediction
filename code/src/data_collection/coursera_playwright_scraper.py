"""
Coursera Web Scraper using Playwright
Early attempt to scrape course URLs by navigating through web pages.

Note: This approach was abandoned due to page limitations (only 84 pages visible,
approximately 1,008 courses out of 14,012 total). We switched to GraphQL API instead.
"""

from playwright.sync_api import sync_playwright
import json
import time
from pathlib import Path


class CourseraPlaywrightScraper:
    def __init__(self, headless=False):
        """
        Initialize the Playwright scraper
        
        Args:
            headless: Run browser in headless mode (False = show browser window)
        """
        self.base_url = "https://www.coursera.org"
        self.course_urls = []
        self.headless = headless
    
    def scrape_courses(self):
        """Scrape course URLs by navigating through web pages"""
        print("=" * 80)
        print("🚀 Starting web scraping with Playwright")
        print("=" * 80)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(locale='en-US')
            page = context.new_page()
            
            # Set headers
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Navigate to courses page
            url = f"{self.base_url}/courses?productTypeDescription=Courses&sortBy=BEST_MATCH&locale=en"
            print(f"\n📍 Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            # Get total pages (limited to 84 pages)
            total_pages = self._get_total_pages(page)
            print(f"\n📄 Total pages available: {total_pages}")
            print(f"⚠️  Note: Only {total_pages} pages are visible, missing many courses")
            
            # Scrape each page
            for page_num in range(1, min(total_pages + 1, 85)):  # Limit to 84 pages
                print(f"\n📄 Scraping page {page_num}/{total_pages}...")
                
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Extract course URLs from current page
                urls = self._extract_urls(page)
                self.course_urls.extend(urls)
                
                print(f"   ✅ Extracted: {len(urls)} URLs")
                print(f"   📊 Total so far: {len(self.course_urls)} URLs")
                
                # Navigate to next page if not last
                if page_num < total_pages:
                    if not self._click_next_page(page):
                        print("   ⚠️  Cannot navigate to next page, stopping")
                        break
                    time.sleep(2)
            
            browser.close()
        
        print(f"\n" + "=" * 80)
        print(f"🎉 Scraping complete!")
        print(f"   📊 Total URLs extracted: {len(self.course_urls)}")
        print(f"   ⚠️  Limitation: Only ~{len(self.course_urls)} courses available via web scraping")
        print(f"   💡 Solution: Use GraphQL API to get all {14012} courses")
        print("=" * 80)
    
    def _get_total_pages(self, page) -> int:
        """Extract total page count from pagination"""
        try:
            # Try to find pagination buttons
            pagination_selectors = [
                "button[aria-label*='page']",
                "[class*='Pagination'] button",
            ]
            
            max_page = 1
            for selector in pagination_selectors:
                try:
                    buttons = page.query_selector_all(selector)
                    for btn in buttons:
                        text = btn.inner_text().strip()
                        if text.isdigit():
                            page_num = int(text)
                            if page_num > max_page:
                                max_page = page_num
                except:
                    continue
            
            return max_page if max_page > 1 else 84
        except:
            return 84  # Default fallback
    
    def _extract_urls(self, page) -> list:
        """Extract course URLs from current page"""
        urls = []
        
        try:
            # Find course cards
            card_selector = "li.cds-grid-item"
            cards = page.query_selector_all(card_selector)
            
            for card in cards:
                links = card.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/learn/" in href:
                        # Convert to full URL
                        if href.startswith("/"):
                            full_url = f"{self.base_url}{href.split('?')[0].split('#')[0]}"
                        elif href.startswith("http"):
                            full_url = href.split("?")[0].split("#")[0]
                        else:
                            continue
                        
                        if full_url not in urls:
                            urls.append(full_url)
        except Exception as e:
            print(f"   ⚠️  Error extracting URLs: {e}")
        
        return urls
    
    def _click_next_page(self, page) -> bool:
        """Click next page button"""
        try:
            # Find next button
            buttons = page.query_selector_all("button.cds-iconButton-small")
            enabled_buttons = [
                btn for btn in buttons
                if "cds-iconButton-disabled" not in (btn.get_attribute("class") or "")
            ]
            
            # Find next button by aria-label
            for btn in enabled_buttons:
                aria_label = btn.get_attribute("aria-label") or ""
                if "next" in aria_label.lower():
                    btn.click()
                    page.wait_for_load_state("networkidle")
                    return True
            
            # Fallback: click last enabled button
            if len(enabled_buttons) >= 2:
                enabled_buttons[-1].click()
                page.wait_for_load_state("networkidle")
                return True
            
            return False
        except:
            return False
    
    def save_urls(self, filename: str = "course_urls_playwright.json"):
        """Save scraped URLs to file"""
        output_path = Path(filename)
        
        data = {
            "total_count": len(self.course_urls),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scraped_method": "Playwright Web Scraping",
            "limitation": "Only 84 pages visible (~1,008 courses out of 14,012 total)",
            "base_url": self.base_url,
            "urls": sorted(list(set(self.course_urls)))
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved {len(self.course_urls)} URLs to {filename}")


def main():
    """Main function"""
    scraper = CourseraPlaywrightScraper(headless=False)
    scraper.scrape_courses()
    
    if scraper.course_urls:
        scraper.save_urls()
        print(f"\n🎉 Success! Scraped {len(scraper.course_urls)} course URLs")
    else:
        print("\n⚠️  No URLs scraped")


if __name__ == "__main__":
    main()

