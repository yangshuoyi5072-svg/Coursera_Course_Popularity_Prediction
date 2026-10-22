import json
import time
import os
import sys
import concurrent.futures
import threading
from bs4 import BeautifulSoup

# Try to import selenium, install if missing
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Installing selenium and webdriver-manager...")
    os.system(f"{sys.executable} -m pip install selenium webdriver-manager beautifulsoup4")
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

class CourseraIncrementalScraper:
    def __init__(self, input_file='Courses_With_Images.json', output_file='Courses_Deep_Features.json', max_workers=4):
        self.input_file = input_file
        self.output_file = output_file
        self.max_workers = max_workers
        self.data = self._load_data()
        self.results = []
        self.lock = threading.Lock()
        self.processed_count = 0
        
    def _setup_driver(self):
        options = Options()
        # options.add_argument('--headless')  # Run in headless mode for speed
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--lang=en-US')  # Try to force English
        
        # Suppress logging
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return None

    def _load_data(self):
        # Default to Courses_With_Images.json if exists, else Courses_Advanced_Features.json
        file_to_load = self.input_file
        if not os.path.exists(file_to_load):
            print(f"{file_to_load} not found, trying Courses_Advanced_Features.json...")
            file_to_load = 'Courses_Advanced_Features.json'
            
        print(f"Loading data from {file_to_load}...")
        try:
            with open(file_to_load, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data['courses']
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

    def scrape_course(self, driver, url):
        try:
            driver.get(url)
            # Scroll to bottom to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            features = {
                'instructors': [],
                'is_specialization': False,
                'is_professional_certificate': False
            }
            
            # 1. Instructor Ratings
            try:
                rating_val = None
                rating_count = None
                star_elems = soup.find_all('span', attrs={'aria-label': lambda x: x and 'stars' in x})
                
                for elem in star_elems:
                    val = elem.get_text(strip=True)[:3]
                    container = elem.find_parent()
                    if container:
                        text = container.get_text(strip=True)
                        import re
                        match = re.search(r'(\d\.\d).*?\(.*?([\d,]+)\s+ratings.*?\)', text)
                        if match:
                            rating_val = match.group(1)
                            rating_count = match.group(2)
                            break
                
                if rating_val:
                    features['instructor_rating'] = rating_val
                if rating_count:
                    features['instructor_rating_count'] = rating_count.replace(',', '')

            except Exception as e:
                pass # Silent fail for sub-features

            # 2. Instructors
            try:
                instructor_links = soup.find_all('a', attrs={'data-track-component': 'hero_instructor'})
                
                for link in instructor_links:
                    name = link.get_text(strip=True)
                    card_container = link.find_parent('div').find_parent('div')
                    
                    courses_count = None
                    learners_count = None
                    is_top_instructor = False
                    
                    if card_container:
                        courses_elem = card_container.find(string=lambda t: t and 'Courses' in t)
                        if courses_elem:
                            import re
                            match = re.search(r'(\d+)', courses_elem)
                            if match: courses_count = match.group(1)
                        
                        learners_elem = card_container.find(string=lambda t: t and 'learners' in t)
                        if learners_elem:
                            import re
                            match = re.search(r'([\d,]+)', learners_elem)
                            if match: learners_count = match.group(1)
                                
                        top_inst_elem = card_container.find(string="Top Instructor")
                        is_top_instructor = bool(top_inst_elem)
                    
                    if name:
                        inst_data = {
                            'name': name,
                            'courses_count': courses_count,
                            'learners_count': learners_count,
                            'is_top_instructor': is_top_instructor
                        }
                        features['instructors'].append(inst_data)

                # Deduplicate
                unique_inst = {i['name']: i for i in features['instructors']}.values()
                features['instructors'] = list(unique_inst)
                
            except Exception as e:
                pass

            # 3. Attributes
            page_text = soup.get_text()
            if 'Specialization' in page_text or '专项课程' in page_text:
                features['is_specialization'] = True
            if 'Professional Certificate' in page_text or '专业证书' in page_text:
                features['is_professional_certificate'] = True
            if 'Flexible schedule' in page_text or '灵活的时间表' in page_text:
                features['is_flexible_schedule'] = True
                
            # Positive Review Rate
            try:
                percent_elems = soup.find_all(string=lambda t: t and t.strip().endswith('%'))
                for p in percent_elems:
                    text = p.strip()
                    if len(text) <= 4 and text[:-1].isdigit():
                        val = int(text[:-1])
                        if 50 <= val <= 100:
                            features['positive_review_rate'] = text
                            break
            except Exception:
                pass
            
            return features
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def _worker(self, courses_chunk, worker_id):
        driver = self._setup_driver()
        if not driver:
            print(f"Worker {worker_id} failed to initialize driver.")
            return
            
        print(f"Worker {worker_id} started with {len(courses_chunk)} courses.")
        
        try:
            for course in courses_chunk:
                url = course.get('url')
                if not url: continue
                
                features = self.scrape_course(driver, url)
                
                with self.lock:
                    self.processed_count += 1
                    status = f"[{self.processed_count}/{len(self.data)}] Worker {worker_id}"
                    
                    if features:
                        # Construct result with only required fields
                        result = {
                            'id': course.get('id'),
                            'url': course.get('url'),
                            'name': course.get('name'),
                            **features
                        }
                        self.results.append(result)
                        print(f"{status} ✅ Scraped: {url} ({len(features['instructors'])} inst)")
                        
                        # Save periodically (every 10 items total)
                        if len(self.results) % 10 == 0:
                            self._save_results()
                    else:
                        print(f"{status} ❌ Failed: {url}")
                        
        except Exception as e:
            print(f"Worker {worker_id} crashed: {e}")
        finally:
            driver.quit()

    def _save_results(self):
        output_data = {'courses': self.results}
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving results: {e}")

    def run(self):
        print(f"Starting parallel scrape with {self.max_workers} workers for {len(self.data)} courses...")
        
        # Split data into chunks
        chunk_size = (len(self.data) + self.max_workers - 1) // self.max_workers
        chunks = [self.data[i:i + chunk_size] for i in range(0, len(self.data), chunk_size)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                futures.append(executor.submit(self._worker, chunk, i+1))
                
            concurrent.futures.wait(futures)
            
        self._save_results()
        print(f"\nDone. Saved {len(self.results)} courses to {self.output_file}")

if __name__ == "__main__":
    # Default to 4 workers, user can change this
    scraper = CourseraIncrementalScraper(max_workers=4)
    scraper.run()
