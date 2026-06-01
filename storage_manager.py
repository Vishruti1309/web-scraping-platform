"""
Storage Manager
Handles data storage to databases and file exports
5. storage_manager.py saves clean data into SQLite also exports CSV/JSON/Excel
"""

import sqlite3
import json
import csv
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

import config

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages data storage and retrieval"""
    
    def __init__(self):
        self.db_type = config.DATABASE_TYPE
        self.connection = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage based on configuration"""
        if self.db_type == 'sqlite':
            self._init_sqlite()
        elif self.db_type == 'postgresql':
            self._init_postgresql()
        elif self.db_type == 'mongodb':
            self._init_mongodb()
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        try:
            # self.connection = sqlite3.connect(config.SQLITE_DB)
            self.connection = sqlite3.connect(config.SQLITE_DB, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite: {config.SQLITE_DB}")
            
            # Create tables
            self._create_tables()
            
        except Exception as e:
            logger.error(f"SQLite initialization failed: {e}")
            raise
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn_params = config.POSTGRES_CONFIG
            self.connection = psycopg2.connect(
                host=conn_params['host'],
                port=conn_params['port'],
                database=conn_params['database'],
                user=conn_params['user'],
                password=conn_params['password']
            )
            self.connection.cursor_factory = RealDictCursor
            logger.info("Connected to PostgreSQL")
            
            self._create_tables()
            
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            from pymongo import MongoClient
            
            mongo_config = config.MONGODB_CONFIG
            client = MongoClient(
                host=mongo_config['host'],
                port=mongo_config['port']
            )
            self.connection = client[mongo_config['database']]
            logger.info("Connected to MongoDB")
            
        except Exception as e:
            logger.error(f"MongoDB initialization failed: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        if self.db_type == 'sqlite':
            cursor = self.connection.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price TEXT,
                availability TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            # Main data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Scraping history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items_scraped INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    duration REAL,
                    error_details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source 
                ON scraped_data(source)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scraped_at 
                ON scraped_data(scraped_at)
            ''')
            
            self.connection.commit()
            logger.info("Database tables created")
    
    def save_data(self, data: List[Dict], source: str) -> bool:
        """Save scraped data to database"""
        if not data:
            logger.warning("No data to save")
            return False
        
        try:
            if self.db_type == 'sqlite':
                return self._save_to_sqlite(data, source)
            elif self.db_type == 'mongodb':
                return self._save_to_mongodb(data, source)
            elif self.db_type == 'postgresql':
                return self._save_to_postgresql(data, source)
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False
    
    def _save_to_sqlite(self, data: List[Dict], source: str) -> bool:
        """Save data to SQLite"""
        cursor = self.connection.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO scraped_data (source, data_json, scraped_at)
                VALUES (?, ?, ?)
            ''', (
                source,
                json.dumps(item),
                item.get('scraped_at', datetime.now().isoformat())
            ))
        
        self.connection.commit()
        logger.info(f"Saved {len(data)} records to SQLite")
        return True
    
    def _save_to_mongodb(self, data: List[Dict], source: str) -> bool:
        """Save data to MongoDB"""
        collection = self.connection[source]
        
        # Add metadata
        for item in data:
            item['_saved_at'] = datetime.now()
        
        result = collection.insert_many(data)
        logger.info(f"Saved {len(result.inserted_ids)} records to MongoDB")
        return True
    
    def _save_to_postgresql(self, data: List[Dict], source: str) -> bool:
        """Save data to PostgreSQL"""
        cursor = self.connection.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO scraped_data (source, data_json, scraped_at)
                VALUES (%s, %s, %s)
            ''', (
                source,
                json.dumps(item),
                item.get('scraped_at', datetime.now().isoformat())
            ))
        
        self.connection.commit()
        logger.info(f"Saved {len(data)} records to PostgreSQL")
        return True
    
    def get_data(self, source: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Retrieve data from database"""
        try:
            if self.db_type == 'sqlite':
                return self._get_from_sqlite(source, limit)
            elif self.db_type == 'mongodb':
                return self._get_from_mongodb(source, limit)
            elif self.db_type == 'postgresql':
                return self._get_from_postgresql(source, limit)
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return []
    
    def _get_from_sqlite(self, source: Optional[str], limit: int) -> List[Dict]:
        """Get data from SQLite"""
        cursor = self.connection.cursor()
        
        if source:
            cursor.execute('''
                SELECT * FROM scraped_data 
                WHERE source = ?
                ORDER BY scraped_at DESC
                LIMIT ?
            ''', (source, limit))
        else:
            cursor.execute('''
                SELECT * FROM scraped_data 
                ORDER BY scraped_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        
        # Parse JSON data
        data = []
        for row in rows:
            item = json.loads(row['data_json'])
            item['_id'] = row['id']
            data.append(item)
        
        return data
    
    def _get_from_mongodb(self, source: Optional[str], limit: int) -> List[Dict]:
        """Get data from MongoDB"""
        if source:
            collection = self.connection[source]
            data = list(collection.find().limit(limit))
        else:
            # Get from all collections
            data = []
            for collection_name in self.connection.list_collection_names():
                collection = self.connection[collection_name]
                data.extend(list(collection.find().limit(limit)))
        
        return data
    
    def log_scraping_history(self, stats: Dict):
        """Log scraping job history"""
        if self.db_type != 'sqlite':
            return
        
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_history 
            (source, status, items_scraped, errors, duration, error_details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            stats.get('name'),
            'success' if stats.get('errors', 0) == 0 else 'partial',
            stats.get('items_scraped', 0),
            stats.get('errors', 0),
            stats.get('duration', 0),
            json.dumps(stats.get('error_details', []))
        ))
        
        self.connection.commit()
        logger.info("Logged scraping history")
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get scraping history"""
        if self.db_type != 'sqlite':
            return []
        
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM scraping_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days"""
        if self.db_type == 'sqlite':
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM scraped_data 
                WHERE scraped_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted = cursor.rowcount
            self.connection.commit()
            logger.info(f"Cleaned up {deleted} old records")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            if self.db_type in ['sqlite', 'postgresql']:
                self.connection.close()
            logger.info("Database connection closed")

    def save_saved_job(self, job):
        cursor = self.connection.cursor()

        cursor.execute('''
            INSERT INTO saved_jobs (title, price, availability)
            VALUES (?, ?, ?)
        ''', (
            job.get("title"),
            job.get("price"),
            job.get("availability")
        ))

        self.connection.commit()
class FileExporter:
    """Exports data to various file formats"""
    

    
    def __init__(self):
        self.export_dir = Path(config.EXPORT_DIR)
        self.export_dir.mkdir(exist_ok=True)
    
       
        
       
    def _get_filename(self, base_name: str, extension: str) -> str:
        """Generate filename with optional timestamp"""
        if config.EXPORT_TIMESTAMP:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{base_name}_{timestamp}.{extension}"
        else:
            filename = f"{base_name}.{extension}"
        
        return str(self.export_dir / filename)
    
    def export_to_csv(self, data: List[Dict], filename: str = 'export') -> str:
        """Export data to CSV"""
        try:
            df = pd.DataFrame(data)
            filepath = self._get_filename(filename, 'csv')
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return None
    
    def export_to_json(self, data: List[Dict], filename: str = 'export') -> str:
        """Export data to JSON"""
        try:
            filepath = self._get_filename(filename, 'json')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return None
    
    def export_to_excel(self, data: List[Dict], filename: str = 'export') -> str:
        """Export data to Excel"""
        try:
            df = pd.DataFrame(data)
            filepath = self._get_filename(filename, 'xlsx')
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            
            logger.info(f"Exported to Excel: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return None
    
    def export_all_formats(self, data: List[Dict], base_name: str = 'export') -> Dict[str, str]:
        """Export to all configured formats"""
        results = {}
        
        for fmt in config.EXPORT_FORMATS:
            if fmt == 'csv':
                results['csv'] = self.export_to_csv(data, base_name)
            elif fmt == 'json':
                results['json'] = self.export_to_json(data, base_name)
            elif fmt == 'excel':
                results['excel'] = self.export_to_excel(data, base_name)
        
        return results