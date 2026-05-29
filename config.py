"""
Configuration file for Web Scraping & Data Aggregation System
Defines all scraping targets, settings, and system parameters
1. config.py defines which websites/APIs to scrape
"""

import os
from datetime import datetime


# SYSTEM CONFIGURATION
# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
EXPORT_DIR = os.path.join(BASE_DIR, 'exports')

# Create directories if they don't exist
for directory in [DATA_DIR, LOG_DIR, EXPORT_DIR]:
    os.makedirs(directory, exist_ok=True)


# SCRAPING CONFIGURATION
# User agents for rotation (appears as different browsers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Request settings
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds between retries
REQUEST_DELAY = 8  # seconds between requests to same domain

# Proxy configuration (add your proxies here)
USE_PROXIES = False
PROXY_LIST = [
    # 'http://proxy1.example.com:8080',
    # 'http://proxy2.example.com:8080',
]

# Selenium/Browser settings
USE_HEADLESS = False  # Run browser in background
BROWSER_TIMEOUT = 90
IMPLICIT_WAIT = 20  


# SCRAPING TARGETS
SCRAPING_TARGETS = {
    # 'quotes': {
    #     'name': 'Quotes to Scrape',
    #     'url': 'http://quotes.toscrape.com',
    #     # 'url': 'http://quotes.toscrape.com',
    #     'type': 'static',  # static or dynamic
    #     'enabled': True,
    #     'schedule': 'daily',  # daily, weekly, hourly
    #     'selectors': {
    #         'container': '.quote',
    #         'text': '.text',
    #         'author': '.author',
    #         'tags': '.tag'
    #     },
    #     'fields': ['text', 'author', 'tags', 'scraped_at'],
    #     'pagination': True,
    #     'pagination_selector': '.next a',
    #       # NEW
    #     'field_mapping': {
    #         'text': 'title',
    #         'author': 'author_name',
    #         'tags': 'tags'
    #     }
    # },
    
    
    'books': {
        'name': 'Books to Scrape',
        'url': 'http://books.toscrape.com',
        'type': 'static',
        'enabled': True,
        'schedule': 'daily',
        'selectors': {
            'container': 'article.product_pod',
            'title': 'h3 a',
            'price': '.price_color',
            'availability': '.availability',
            'rating': 'p.star-rating'
        },
        'fields': ['title', 'price', 'availability', 'rating', 'scraped_at'],
        'pagination': True,
        'pagination_selector': '.next a',
        # NEW
        'field_mapping': {
            'title': 'title',
            'price': 'price_current',
            'availability': 'availability',
            'rating': 'rating'
        }
    },
    
    # 'myntra_tops': {
    #     'name': 'Myntra Women Tops',
    #     'url': 'https://www.myntra.com/women-tops',
    #     'type': 'dynamic',  
    #     'enabled': True,
    #     'schedule': 'daily',
    #     'selectors': {
    #         'container': 'li.product-base',
    #         'brand': 'h3.product-brand',
    #         'name': 'h4.product-product',
    #         'price': 'span.product-discountedPrice',
    #         'original_price': 'span.product-strike',
    #         'discount': 'span.product-discountPercentage',
    #         'rating': 'div.product-rating span',
    #         'image': 'img.img-responsive',
    #         'link': 'a'
    #     },
    #     'fields': ['brand', 'name', 'price', 'original_price', 'discount', 'rating', 'image', 'link', 'scraped_at'],
    #     'pagination': False,
    #     'pagination_selector': None, # Next page button

    #       # NEW
    #     'field_mapping': {
    #         'name': 'title',
    #         'brand': 'brand',
    #         'price': 'price_current',
    #         'original_price': 'price_original',
    #         'discount': 'discount_percent',
    #         'rating': 'rating',
    #         'image': 'image_url',
    #         'link': 'product_url'
    #     }
    # },


    # BY API
        'json_placeholder_posts': {
        'name': 'JSONPlaceholder Posts API',
        'url': 'https://jsonplaceholder.typicode.com/posts',
        'type': 'api',          
        'enabled': True,
        'schedule': 'daily',

        # How to interpret the API response
        'api_config': {
            # 'json_path': '$' means the response itself is the list of items
            # If your API is like {"data": {"items": [...]}} you could use "data.items"
            'json_path': '$',

            # Map fields from API JSON to our internal item fields
            'field_mapping': {
                'title': 'title',
                'body': 'content',
                'userId': 'user_id',
                'id': 'external_id'
            }
        },

        # Fields we care about in the final data
        'fields': ['title', 'body', 'user_id', 'scraped_at'],

        # Most APIs won’t use HTML pagination
        'pagination': False
    },

    'myntra_mens_shoes': {
    'name': 'Myntra Men Shoes',
    'url': 'https://www.myntra.com/men-shoes',
    'type': 'dynamic',
    'enabled': True,
    'schedule': 'daily',
    'selectors': {
        'container': 'li.product-base',
        'brand': 'h3.product-brand',
        'name': 'h4.product-product',
        'price': 'span.product-discountedPrice',
        'original_price': 'span.product-strike',
        'discount': 'span.product-discountPercentage',
        'rating': 'div.product-rating span',
        'image': 'img.img-responsive',
        'link': 'a'
    },
    'fields': ['brand',
        'name',
        'price',
        'original_price',
        'discount',
        'rating',
        'image',
        'link',
        'scraped_at'],
    'pagination': True,
    'pagination_selector': 'a.pagination-next',

    # optional: field standardization
    'field_mapping': {
        'name': 'title',
        'price': 'price_current',
        'original_price': 'price_original',
        'discount': 'discount_percent',
        'image': 'image_url',
        'link': 'product_url'
    }
},


}




# DATABASE CONFIGURATION
DATABASE_TYPE = 'sqlite'
SQLITE_DB = os.path.join(DATA_DIR, 'scraped_data.db')

# PostgreSQL (uncomment and configure if using)
# DATABASE_TYPE = 'postgresql'
# POSTGRES_CONFIG = {
#     'host': 'localhost',
#     'port': 5432,
#     'database': 'scraper_db',
#     'user': 'your_user',
#     'password': 'your_password'
# }

# MongoDB (uncomment and configure if using)
# DATABASE_TYPE = 'mongodb'
# MONGODB_CONFIG = {
#     'host': 'localhost',
#     'port': 27017,
#     'database': 'scraper_db'
# }



# DATA CLEANING RULES
CLEANING_RULES = {
    'remove_html_tags': True,
    'strip_whitespace': True,
    'lowercase_fields': [],  # fields to convert to lowercase
    'remove_special_chars': False,
    'standardize_dates': True,
    'remove_duplicates': True,
    'duplicate_check_fields': ['name','text', 'title']  # fields to check for duplicates
}


# EXPORT SETTINGS
EXPORT_FORMATS = ['csv', 'json', 'excel']
AUTO_EXPORT = True
EXPORT_TIMESTAMP = True  # add timestamp to export filenames


# MONITORING & ALERTS
# Email configuration for alerts
ENABLE_EMAIL_ALERTS = False
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'your_email@gmail.com',
    'sender_password': 'your_app_password',
    'recipient_emails': ['admin@example.com'],
    'alerts_on': {
        'scraping_failure': True,
        'structure_change': True,
        'completion': False
    }
}

# Logging configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOG_DIR, f'scraper_{datetime.now().strftime("%Y%m%d")}.log')

# Structure change detection
DETECT_STRUCTURE_CHANGES = True
STRUCTURE_TOLERANCE = 0.5  # 50% of selectors must work


# SCHEDULER SETTINGS
SCHEDULE_CONFIG = {
    'daily': '02:00',  # Run at 2 AM
    'weekly': 'monday 02:00',  # Run every Monday at 2 AM
    'hourly': '00'  # Run at the top of every hour
}


# ROBOTS.TXT COMPLIANCE
RESPECT_ROBOTS_TXT = False
CRAWL_DELAY = 2  # seconds (overridden by robots.txt if stricter)


# PERFORMANCE SETTINGS
MAX_WORKERS = 5  # for parallel scraping
BATCH_SIZE = 100  # records to process at once
MAX_PAGES_PER_SITE = 3  # limit for pagination