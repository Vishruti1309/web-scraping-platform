"""
Core Scraping Engine
Handles both static and dynamic website scraping with error handling
3. scraper_engine.py collects raw data
"""

import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime

import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperEngine:
    """Main scraping engine with retry logic and error handling"""

    def __init__(self, target_config: Dict):
        self.config = target_config
        self.name = target_config['name']
        self.url = target_config['url']
        self.type = target_config['type']
        self.session = requests.Session()
        self.driver = None
        self.data = []
        self.errors = []
        self.robots_parser = None

        # Setup robots.txt parser
        if config.RESPECT_ROBOTS_TXT:
            self._setup_robots_parser()


    def _resolve_json_path(self, data, path: str):
        """Resolve a simple dot-separated JSON path on a Python dict.

        - '$' means 'use the whole data'
        - 'data.items' means data['data']['items']
        """
        if path == '$' or not path:
            return data

        current = data
        for part in path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _setup_robots_parser(self):
        try:
            parsed_url = urlparse(self.url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()

            logger.info(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}")
            self.robots_parser = None

    def _can_fetch(self, url: str) -> bool:
        if not config.RESPECT_ROBOTS_TXT or not self.robots_parser:
            return True

        user_agent = random.choice(config.USER_AGENTS)
        can_fetch = self.robots_parser.can_fetch(user_agent, url)

        if not can_fetch:
            logger.warning(f"Robots.txt disallows fetching: {url}")

        return can_fetch

    def _get_headers(self) -> Dict:
        return {
            'User-Agent': random.choice(config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def _get_proxy(self) -> Optional[Dict]:
        if config.USE_PROXIES and config.PROXY_LIST:
            proxy = random.choice(config.PROXY_LIST)
            return {'http': proxy, 'https': proxy}
        return None


    # STATIC SCRAPING ()
    def _fetch_static(self, url: str) -> Optional[BeautifulSoup]:
        if not self._can_fetch(url):
            return None

        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1})")

                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies=self._get_proxy(),
                    timeout=config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                time.sleep(config.REQUEST_DELAY)
                return BeautifulSoup(response.content, 'html.parser')

            except requests.RequestException as e:
                logger.error(f"Static request failed: {e}")
                if attempt == config.RETRY_ATTEMPTS - 1:
                    self.errors.append({"url": url, "error": str(e)})
                else:
                    time.sleep(config.RETRY_DELAY)
        return None

   

# TO FETCH THE API (FOR API)
    def _fetch_api(self, url: str) -> List[Dict]:
        """Fetch JSON API and return list[Dict] items."""
        if not self._can_fetch(url):
            return []

        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                logger.info(f"Fetching API {url} (attempt {attempt + 1})")

                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies=self._get_proxy(),
                    timeout=config.REQUEST_TIMEOUT
                )
                response.raise_for_status()

                data = response.json()  # assume JSON API

                api_cfg = self.config.get('api_config', {})
                json_path = api_cfg.get('json_path', '$')
                raw_items = self._resolve_json_path(data, json_path)

                if raw_items is None:
                    logger.warning(f"JSON path '{json_path}' not found in API response")
                    return []

                if isinstance(raw_items, dict):
                    # Some APIs return {"items": {...}} — wrap in list
                    raw_items = [raw_items]

                if not isinstance(raw_items, list):
                    logger.warning("API items are not a list, skipping")
                    return []

                field_mapping = api_cfg.get('field_mapping', {})
                items: List[Dict] = []

                for obj in raw_items:
                    if not isinstance(obj, dict):
                        continue

                    item = {}
                    # Map fields
                    for out_field, json_key in field_mapping.items():
                        item[out_field] = obj.get(json_key)

                    # Metadata
                    item['scraped_at'] = datetime.now().isoformat()
                    item['source'] = self.name

                    items.append(item)

                return items

            except Exception as e:
                logger.error(f"API request failed on attempt {attempt + 1}: {e}")
                if attempt < config.RETRY_ATTEMPTS - 1:
                    time.sleep(config.RETRY_DELAY)
                else:
                    self.errors.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now()
                    })
                    return []


    def _setup_selenium(self):
        if self.driver:
            return

        try:
            logger.info("Initializing undetected Chrome driver…")

            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--window-size=1920,1080")

            # REMOVE THESE → NOT SUPPORTED ANYMORE
            # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # chrome_options.add_experimental_option('useAutomationExtension', False)

            # Use random user agent
            chrome_options.add_argument(f'user-agent={random.choice(config.USER_AGENTS)}')

            # Headless mode toggle
            if config.USE_HEADLESS:
                chrome_options.add_argument("--headless=new")

            # Launch UC with simplified flags
            self.driver = uc.Chrome(options=chrome_options)

            # Stealth: remove webdriver property
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
            """)

            self.driver.set_page_load_timeout(90)
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)

            logger.info("Undetected Chrome initialized successfully")

        except Exception as e:
            logger.error(f"Selenium setup failed: {e}")
            raise



    # UPDATED SCROLLING
    def _scroll_page(self):
        """Deep scrolling for React/JS lazy-loaded sites"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for i in range(10):
                logger.info(f"Dynamic scroll: {i+1}/10")
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(random.uniform(2, 4))

                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height

        except Exception as e:
            logger.warning(f"Scroll failed: {e}")


    #UPDATED DYNAMIC FETCHER    
    def _fetch_dynamic(self, url: str) -> Optional[BeautifulSoup]:
        if not self._can_fetch(url):
            return None

        try:
            self._setup_selenium()

            logger.info(f"Loading dynamic page: {url}")
            time.sleep(random.uniform(2, 4))
            self.driver.get(url)

            # Try dismissing cookie popup if present
            try:
                cookie_btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
                )
                cookie_btn.click()
                logger.info("Cookie popup dismissed")
            except:
                pass

            # Wait until the main container is visible
            container_selector = self.config["selectors"]["container"]
            logger.info(f"Waiting for selector: {container_selector}")

            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, container_selector))
            )

            logger.info("Dynamic content detected — starting deep scroll")
            self._scroll_page()

            time.sleep(random.uniform(2, 5))

            html = self.driver.page_source
            if len(html) < 1000:
                logger.warning("Dynamic HTML content appears too small")

            return BeautifulSoup(html, "html.parser")

        except Exception as e:
            logger.error(f"Dynamic fetch failed: {e}")
            self.errors.append({"url": url, "error": str(e)})
            return None


    # EXTRACTION ()


    def _extract_data(self, soup: BeautifulSoup) -> List[Dict]:
        items = []
        selectors = self.config['selectors']

        try:
            containers = soup.select(selectors['container'])
            if not containers:
                logger.warning(f"No items found for selector: {selectors['container']}")
                return []

            logger.info(f"Extracting from {len(containers)} items")

            for container in containers:
                item = {}
                for field, selector in selectors.items():
                    if field == "container":
                        continue

                    try:
                        element = container.select_one(selector)
                        if not element:
                            item[field] = None
                            continue

                        if field in ['link', 'href', 'url']:
                            item[field] = element.get("href", "")
                        elif field in ['image', 'img', 'src']:
                            item[field] = element.get("src", "")
                        else:
                            if field == "title":
                                item[field] = element.get("title") or element.get_text(strip=True)
                            elif field in ['link', 'href', 'url']:
                                item[field] = element.get("href", "")
                            elif field in ['image', 'img', 'src']:
                                item[field] = element.get("src", "")
                            else:
                                item[field] = element.get_text(strip=True)

                    except:
                        item[field] = None

                item["scraped_at"] = datetime.now().isoformat()
                item["source"] = self.name
                items.append(item)

            return items

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return items


    # PAGINATION ()


    def _get_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        if not self.config.get("pagination", False):
            return None

        try:
            selector = self.config.get("pagination_selector")
            next_link = soup.select_one(selector)
            if next_link:
                href = next_link.get("href")
                if href:
                    return urljoin(current_url, href)
        except:
            pass

        return None


    # SCRAPE LOOP 


    # def scrape(self) -> List[Dict]:
    #     logger.info(f"Starting scrape: {self.name}")

    #     try:
    #         current_url = self.url
    #         pages_scraped = 0

    #         while current_url and pages_scraped < config.MAX_PAGES_PER_SITE:

    #             if self.type == "dynamic":
    #                 soup = self._fetch_dynamic(current_url)
    #             else:
    #                 soup = self._fetch_static(current_url)

    #             if not soup:
    #                 break

    #             items = self._extract_data(soup)
    #             self.data.extend(items)
    #             pages_scraped += 1

    #             logger.info(f"Page {pages_scraped}: {len(items)} items")

    #             current_url = self._get_next_page(soup, current_url)

    #         return self.data

    #     finally:
    #         self.cleanup()
    
    def scrape(self) -> List[Dict]:
        """Main scraping method"""
        logger.info(f"Starting scrape: {self.name}")
        start_time = time.time()

        try:
            current_url = self.url
            pages_scraped = 0

            # Special case for API-based sources (usually one call per run)
            if self.type == 'api':
                items = self._fetch_api(current_url)
                self.data.extend(items)
                pages_scraped = 1

                logger.info(f"API scrape completed: {len(items)} items")
                return self.data

            # Existing logic for static & dynamic HTML
            while current_url and pages_scraped < config.MAX_PAGES_PER_SITE:
                # Fetch page
                if self.type == 'dynamic':
                    soup = self._fetch_dynamic(current_url)
                else:
                    soup = self._fetch_static(current_url)

                if not soup:
                    logger.error(f"Failed to fetch: {current_url}")
                    break

                # Extract data
                items = self._extract_data(soup)
                self.data.extend(items)
                pages_scraped += 1

                logger.info(f"Page {pages_scraped}: Extracted {len(items)} items")

                # Get next page
                current_url = self._get_next_page(soup, current_url)

            elapsed = time.time() - start_time
            logger.info(f"Scrape completed: {len(self.data)} items in {elapsed:.2f}s")

            return self.data

        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            return self.data

        finally:
            self.cleanup()


    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium closed")
            except:
                pass

        self.session.close()

    def get_stats(self):
        return {
            'name': self.name,
            'items_scraped': len(self.data),
            'errors': len(self.errors),
            'error_details': self.errors
        }
