"""
Data Processor Module
Handles data cleaning, normalization, deduplication, and aggregation
4. data_processor.py cleans and validates the raw data
"""

import re
import hashlib
import logging
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes and cleans scraped data"""
    

    def __init__(self):
        self.cleaning_rules = config.CLEANING_RULES
        self.processed_data = []
        self.duplicates_removed = 0
        self.seen_hashes = set()
    
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not isinstance(text, str):
            return text
        
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    
    def _strip_whitespace(self, text: str) -> str:
        """Remove extra whitespace"""
        if not isinstance(text, str):
            return text
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _remove_special_chars(self, text: str) -> str:
        """Remove special characters"""
        if not isinstance(text, str):
            return text
        
        # Keep only alphanumeric, spaces, and basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text
    
    def _standardize_date(self, date_str: str) -> str:
        """Standardize date format"""
        if not isinstance(date_str, str):
            return date_str
        
        # Try common date formats
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y',
            '%B %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str
    
    
    def standardize_fields(
        self,
        data: List[Dict],
        field_mapping: Dict[str, str]
    ) -> List[Dict]:
        """
        Map source-specific field names to global standardized field names.

        Example:
            field_mapping = {'name': 'title', 'price': 'price_current'}
        """
        if not field_mapping or not data:
            return data

        standardized = []

        for item in data:
            new_item = item.copy()

            for src_field, dst_field in field_mapping.items():
                if src_field in item and item[src_field] is not None:
                    # Don't overwrite if dst already exists (just in case)
                    if dst_field not in new_item:
                        new_item[dst_field] = item[src_field]

            standardized.append(new_item)

        return standardized


#to remove space or empty entries
    def _is_bad_item(self, item: Dict) -> bool:
        """
        Decide if an item is 'bad' (no useful data).
        We ignore metadata fields like scraped_at, source, id.
        """
        if not item:
            return True

        has_value = False

        for key, value in item.items():
            if key in ['scraped_at', 'source', 'id']:
                continue

            if value is None:
                continue

            if isinstance(value, str) and value.strip() == '':
                continue

            # Found at least one meaningful value
            has_value = True
            break

        return not has_value


    def _normalize_price(self, price_str: str) -> float:
        """Extract and normalize price"""
        if not isinstance(price_str, str):
            return 0.0
        
        # Remove currency symbols and extract number
        price_str = re.sub(r'[^\d.,]', '', price_str)
        price_str = price_str.replace(',', '')
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    def _generate_hash(self, item: Dict, fields: List[str]) -> str:
        """Generate hash for duplicate detection"""
        # Concatenate specified fields
        hash_string = ''
        for field in fields:
            value = item.get(field, '')
            if value:
                hash_string += str(value).lower().strip()
        
        # Generate MD5 hash
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def clean_item(self, item: Dict) -> Dict:
        """Clean a single data item"""
        cleaned = item.copy()
        
        for key, value in cleaned.items():
            # Skip metadata fields
            if key in ['scraped_at', 'source', 'id']:
                continue
            
            if not value:
                continue
            
            # Remove HTML tags
            if self.cleaning_rules.get('remove_html_tags'):
                value = self._remove_html_tags(value)
            
            # Strip whitespace
            if self.cleaning_rules.get('strip_whitespace'):
                value = self._strip_whitespace(value)
            
            # Remove special characters
            if self.cleaning_rules.get('remove_special_chars'):
                value = self._remove_special_chars(value)
            
            # Lowercase specific fields
            if key in self.cleaning_rules.get('lowercase_fields', []):
                if isinstance(value, str):
                    value = value.lower()
            
            # Standardize dates
            if self.cleaning_rules.get('standardize_dates'):
                if 'date' in key.lower() or key in ['created', 'updated', 'published']:
                    value = self._standardize_date(value)
            
            # Normalize prices
            if 'price' in key.lower() or 'cost' in key.lower():
                value = self._normalize_price(value)
            
            cleaned[key] = value
        
        return cleaned
    
    def is_duplicate(self, item: Dict) -> bool:
        """Check if item is duplicate"""
        if not self.cleaning_rules.get('remove_duplicates'):
            return False
        
        check_fields = self.cleaning_rules.get('duplicate_check_fields', [])
        if not check_fields:
            return False
        
        # Generate hash
        item_hash = self._generate_hash(item, check_fields)
        
        # Check if seen before
        if item_hash in self.seen_hashes:
            return True
        
        self.seen_hashes.add(item_hash)
        return False
    
    def process_batch(self, data: List[Dict]) -> List[Dict]:
        """Process a batch of items"""
        logger.info(f"Processing {len(data)} items")
        
        processed = []
        duplicates = 0
        bad_items = 0
        
        for item in data:
            # Clean item
            cleaned = self.clean_item(item)
            
            # Drop completely empty / bad rows
            if self._is_bad_item(cleaned):
                bad_items += 1
                continue

            # Check for duplicates
            if self.is_duplicate(cleaned):
                duplicates += 1
                continue
            
            processed.append(cleaned)
        
        self.duplicates_removed += duplicates
        self.processed_data.extend(processed)
        
        logger.info(f"Processed: {len(processed)} items," 
                    f"Removed: {duplicates} duplicates"
                     f"Dropped: {bad_items} bad entries")
        
        return processed
    
    def merge_sources(self, datasets: Dict[str, List[Dict]]) -> pd.DataFrame:
        """Merge data from multiple sources"""
        logger.info(f"Merging {len(datasets)} data sources")
        
        all_data = []
        
        for source_name, data in datasets.items():
            # Add source identifier
            for item in data:
                item['source'] = source_name
            all_data.extend(data)
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(all_data)
        
        # Remove duplicates in DataFrame
        if not df.empty and self.cleaning_rules.get('remove_duplicates'):
            check_fields = self.cleaning_rules.get('duplicate_check_fields', [])
            existing_fields = [f for f in check_fields if f in df.columns]
            
            if existing_fields:
                original_len = len(df)
                df = df.drop_duplicates(subset=existing_fields, keep='first')
                removed = original_len - len(df)
                logger.info(f"Removed {removed} duplicate rows after merge")
        
        return df
    
    def validate_data(self, data: List[Dict]) -> Dict:
        """Validate data quality"""
        if not data:
            return {
                'valid': False,
                'issues': ['No data to validate']
            }
        
        issues = []
        warnings = []
        
        # Check for empty values
        total_fields = len(data[0].keys())
        empty_counts = {key: 0 for key in data[0].keys()}
        
        for item in data:
            for key, value in item.items():
                if not value or value == '' or value == 'None':
                    empty_counts[key] += 1
        
        # Report fields with high empty rate
        for field, count in empty_counts.items():
            empty_rate = count / len(data)
            if empty_rate > 0.5:
                warnings.append(f"Field '{field}' is empty in {empty_rate*100:.1f}% of records")
        
        # Check data consistency
        df = pd.DataFrame(data)
        
        # Check for outliers in numeric fields
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if df[col].std() > df[col].mean() * 2:
                warnings.append(f"High variance detected in '{col}'")
        
        return {
            'valid': len(issues) == 0,
            'total_records': len(data),
            'total_fields': total_fields,
            'issues': issues,
            'warnings': warnings,
            'empty_field_rates': {k: v/len(data) for k, v in empty_counts.items()}
        }
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        if not self.processed_data:
            return {'message': 'No data processed yet'}
        
        df = pd.DataFrame(self.processed_data)
        
        stats = {
            'total_records': len(self.processed_data),
            'duplicates_removed': self.duplicates_removed,
            'unique_sources': len(df['source'].unique()) if 'source' in df.columns else 0,
            'fields': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }
        
        return stats
    
    def reset(self):
        """Reset processor state"""
        self.processed_data = []
        self.duplicates_removed = 0
        self.seen_hashes = set()
        logger.info("Data processor reset")


class DataAggregator:
    """Aggregates and analyzes processed data"""
    
    def __init__(self, data: pd.DataFrame):
        self.df = data
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if self.df.empty:
            return {'message': 'No data available'}
        
        summary = {
            'total_records': len(self.df),
            'date_range': {
                'earliest': self.df['scraped_at'].min() if 'scraped_at' in self.df.columns else None,
                'latest': self.df['scraped_at'].max() if 'scraped_at' in self.df.columns else None
            },
            'sources': self.df['source'].value_counts().to_dict() if 'source' in self.df.columns else {},
            'numeric_stats': self.df.describe().to_dict()
        }
        
        return summary
    
    def group_by_source(self) -> Dict[str, pd.DataFrame]:
        """Group data by source"""
        if 'source' not in self.df.columns:
            return {'all': self.df}
        
        return {name: group for name, group in self.df.groupby('source')}
    
    def get_trends(self, field: str, time_field: str = 'scraped_at') -> pd.DataFrame:
        """Analyze trends over time"""
        if field not in self.df.columns or time_field not in self.df.columns:
            return pd.DataFrame()
        
        df_copy = self.df.copy()
        df_copy[time_field] = pd.to_datetime(df_copy[time_field])
        
        # Group by date
        trends = df_copy.groupby(df_copy[time_field].dt.date)[field].agg(['count', 'mean', 'sum'])
        return trends