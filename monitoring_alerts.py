"""
Monitoring and Alert System
Handles notifications, structure change detection, and logging
7. monitoring_alerts.py tracks logs, errors, and performance
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import json

import config

logger = logging.getLogger(__name__)


class AlertSystem:
    """Sends alerts via email"""
    
    def __init__(self):
        self.enabled = config.ENABLE_EMAIL_ALERTS
        self.email_config = config.EMAIL_CONFIG
        self.alerts_sent = []
    
    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        """Send email alert"""
        if not self.enabled:
            logger.info(f"Email alerts disabled. Would have sent: {subject}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])
            msg['Subject'] = subject
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(
                self.email_config['smtp_server'],
                self.email_config['smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.email_config['sender_email'],
                    self.email_config['sender_password']
                )
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            self.alerts_sent.append({
                'subject': subject,
                'timestamp': datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def alert_scraping_failure(self, source: str, error: str):
        """Send alert for scraping failure"""
        if not self.email_config['alerts_on']['scraping_failure']:
            return
        
        subject = f"🚨 Scraping Failed: {source}"
        body = f"""
Scraping job failed for: {source}

Error: {error}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for more details.
        """
        
        self.send_email(subject, body)
    
    def alert_structure_change(self, source: str, details: Dict):
        """Send alert for website structure change"""
        if not self.email_config['alerts_on']['structure_change']:
            return
        
        subject = f"⚠️ Structure Change Detected: {source}"
        body = f"""
Website structure appears to have changed for: {source}

Details:
{json.dumps(details, indent=2)}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The scraper may need to be updated with new selectors.
        """
        
        self.send_email(subject, body)
    
    def alert_completion(self, stats: Dict):
        """Send completion report"""
        if not self.email_config['alerts_on']['completion']:
            return
        
        subject = f"✅ Scraping Completed: {stats.get('name')}"
        body = f"""
Scraping job completed successfully!

Source: {stats.get('name')}
Items scraped: {stats.get('items_scraped', 0)}
Errors: {stats.get('errors', 0)}
Duration: {stats.get('duration', 0):.2f} seconds

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)
    
    def send_daily_summary(self, summary: Dict):
        """Send daily summary report"""
        subject = f"📊 Daily Scraping Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
Daily Scraping Summary Report

Total Jobs Run: {summary.get('total_jobs', 0)}
Successful: {summary.get('successful', 0)}
Failed: {summary.get('failed', 0)}
Total Items Scraped: {summary.get('total_items', 0)}
Total Errors: {summary.get('total_errors', 0)}

Average Duration: {summary.get('avg_duration', 0):.2f} seconds

Details by Source:
{json.dumps(summary.get('by_source', {}), indent=2)}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)


class StructureMonitor:
    """Monitors website structure changes"""
    
    def __init__(self):
        self.structure_history = {}
        self.tolerance = config.STRUCTURE_TOLERANCE
    
    def record_structure(self, source: str, selectors: Dict, found_counts: Dict):
        """Record current structure"""
        self.structure_history[source] = {
            'selectors': selectors,
            'found_counts': found_counts,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_change(self, source: str, current_found: Dict) -> Optional[Dict]:
        """Detect if structure has changed"""
        if source not in self.structure_history:
            return None
        
        previous = self.structure_history[source]['found_counts']
        
        # Calculate success rate
        total_selectors = len(current_found)
        working_selectors = sum(1 for count in current_found.values() if count > 0)
        
        success_rate = working_selectors / total_selectors if total_selectors > 0 else 0
        
        # Check if below tolerance
        if success_rate < self.tolerance:
            return {
                'source': source,
                'success_rate': success_rate,
                'tolerance': self.tolerance,
                'previous_counts': previous,
                'current_counts': current_found,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def get_history(self, source: str) -> Optional[Dict]:
        """Get structure history for source"""
        return self.structure_history.get(source)


class PerformanceMonitor:
    """Monitors scraping performance metrics"""
    
    def __init__(self):
        self.metrics = []
        self.current_job = None
    
    def start_job(self, source: str):
        """Start monitoring a job"""
        self.current_job = {
            'source': source,
            'start_time': datetime.now(),
            'pages_scraped': 0,
            'items_scraped': 0,
            'errors': 0,
            'error_details': []
        }
    
    def record_page(self, items_count: int):
        """Record page scraping"""
        if self.current_job:
            self.current_job['pages_scraped'] += 1
            self.current_job['items_scraped'] += items_count
    
    def record_error(self, error: Dict):
        """Record error"""
        if self.current_job:
            self.current_job['errors'] += 1
            self.current_job['error_details'].append(error)
    
    def end_job(self) -> Dict:
        """End job and calculate metrics"""
        if not self.current_job:
            return {}
        
        end_time = datetime.now()
        duration = (end_time - self.current_job['start_time']).total_seconds()
        
        self.current_job['end_time'] = end_time
        self.current_job['duration'] = duration
        
        # Calculate rates
        if duration > 0:
            self.current_job['items_per_second'] = self.current_job['items_scraped'] / duration
            self.current_job['pages_per_second'] = self.current_job['pages_scraped'] / duration
        
        # Store metrics
        self.metrics.append(self.current_job.copy())
        
        result = self.current_job
        self.current_job = None
        
        return result
    
    def get_summary(self, last_n: int = 10) -> Dict:
        """Get performance summary"""
        if not self.metrics:
            return {'message': 'No metrics available'}
        
        recent = self.metrics[-last_n:]
        
        total_jobs = len(recent)
        total_items = sum(m['items_scraped'] for m in recent)
        total_errors = sum(m['errors'] for m in recent)
        avg_duration = sum(m['duration'] for m in recent) / total_jobs
        
        return {
            'total_jobs': total_jobs,
            'total_items_scraped': total_items,
            'total_errors': total_errors,
            'average_duration': avg_duration,
            'average_items_per_job': total_items / total_jobs if total_jobs > 0 else 0,
            'success_rate': (total_jobs - sum(1 for m in recent if m['errors'] > 0)) / total_jobs if total_jobs > 0 else 0
        }
    
    def get_source_performance(self, source: str) -> Dict:
        """Get performance for specific source"""
        source_metrics = [m for m in self.metrics if m['source'] == source]
        
        if not source_metrics:
            return {'message': f'No metrics for {source}'}
        
        total_runs = len(source_metrics)
        avg_duration = sum(m['duration'] for m in source_metrics) / total_runs
        avg_items = sum(m['items_scraped'] for m in source_metrics) / total_runs
        
        return {
            'source': source,
            'total_runs': total_runs,
            'average_duration': avg_duration,
            'average_items_per_run': avg_items,
            'last_run': source_metrics[-1] if source_metrics else None
        }


class Logger:
    """Enhanced logging with structured output"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_scraping_start(self, source: str, url: str):
        """Log scraping job start"""
        self.logger.info(f"Starting scrape | Source: {source} | URL: {url}")
    
    def log_scraping_complete(self, stats: Dict):
        """Log scraping completion"""
        self.logger.info(
            f"Scraping complete | "
            f"Source: {stats.get('name')} | "
            f"Items: {stats.get('items_scraped', 0)} | "
            f"Errors: {stats.get('errors', 0)}"
        )
    
    def log_error(self, source: str, error: str, url: Optional[str] = None):
        """Log error with context"""
        msg = f"Error | Source: {source}"
        if url:
            msg += f" | URL: {url}"
        msg += f" | Error: {error}"
        
        self.logger.error(msg)
    
    def log_data_processed(self, count: int, duplicates: int):
        """Log data processing"""
        self.logger.info(
            f"Data processed | "
            f"Records: {count} | "
            f"Duplicates removed: {duplicates}"
        )
    
    def log_export(self, format_type: str, filepath: str, count: int):
        """Log data export"""
        self.logger.info(
            f"Data exported | "
            f"Format: {format_type} | "
            f"File: {filepath} | "
            f"Records: {count}"
        )
    
    def log_storage(self, operation: str, count: int, location: str):
        """Log storage operation"""
        self.logger.info(
            f"Storage {operation} | "
            f"Records: {count} | "
            f"Location: {location}"
        )


# Global instances
alert_system = AlertSystem()
structure_monitor = StructureMonitor()
performance_monitor = PerformanceMonitor()