"""
Scheduler and Main Orchestrator
 Coordinates all scraping jobs, scheduling, and data pipeline
 2. scheduler_orchestrator.py starts a scraping job
 """

import schedule
import time
import logging
from datetime import datetime
from typing import Dict, List
import threading

import config
from scraper_engine import ScraperEngine
from data_processor import DataProcessor, DataAggregator
from storage_manager import StorageManager, FileExporter
from monitoring_alerts import (
    alert_system, 
    structure_monitor, 
    performance_monitor,
    Logger
    
)

logger = Logger('Orchestrator')


class ScrapingOrchestrator:
    """Main orchestrator for scraping operations"""
    
    def __init__(self):
        self.storage = StorageManager()
        self.processor = DataProcessor()
        self.exporter = FileExporter()
        self.jobs_run = 0
        self.total_items_scraped = 0
    
    def scrape_source(self, source_name: str) -> Dict:
        """Scrape a single source"""
        if source_name not in config.SCRAPING_TARGETS:
            logger.log_error(source_name, "Source not found in configuration")
            return {'success': False, 'error': 'Source not found'}
        
        target_config = config.SCRAPING_TARGETS[source_name]
        
        # Check if enabled
        if not target_config.get('enabled', True):
            logger.logger.info(f"Source {source_name} is disabled, skipping")
            return {'success': False, 'error': 'Source disabled'}
        
        # Start monitoring
        performance_monitor.start_job(source_name)
        logger.log_scraping_start(source_name, target_config['url'])
        
        try:
            # Initialize scraper
            scraper = ScraperEngine(target_config)
            
            # Scrape data
            raw_data = scraper.scrape()
            
            if not raw_data:
                logger.log_error(source_name, "No data scraped")
                alert_system.alert_scraping_failure(source_name, "No data scraped")
                return {'success': False, 'error': 'No data scraped'}
            
            # NEW: standardize to common schema
            field_mapping = target_config.get('field_mapping')
            if field_mapping:
                raw_data = self.processor.standardize_fields(raw_data, field_mapping)


            # Record for monitoring
            performance_monitor.record_page(len(raw_data))
            
            # Process data
            logger.logger.info(f"Processing {len(raw_data)} items from {source_name}")
            processed_data = self.processor.process_batch(raw_data)
            
            logger.log_data_processed(
                len(processed_data),
                self.processor.duplicates_removed
            )


            
            # Validate data
            validation = self.processor.validate_data(processed_data)
            
            if not validation['valid']:
                logger.log_error(source_name, f"Data validation failed: {validation['issues']}")
            
            # Save to database
            if self.storage.save_data(processed_data, source_name):
                logger.log_storage('saved', len(processed_data), 'database')
            
            # Export if configured
            if config.AUTO_EXPORT and processed_data:
                export_results = self.exporter.export_all_formats(
                    processed_data,
                    f"{source_name}_data"
                )
                
                for fmt, filepath in export_results.items():
                    if filepath:
                        logger.log_export(fmt, filepath, len(processed_data))
            
            # Get stats
            stats = scraper.get_stats()
            stats['duration'] = performance_monitor.end_job()['duration']
            
            # Log history
            self.storage.log_scraping_history(stats)
            
            # Check for structure changes
            # if config.DETECT_STRUCTURE_CHANGES:
            #     found_counts = {
            #         key: len([item for item in processed_data if item.get(key)])
            #         for key in target_config['fields']
            #     }
                
            #     change_details = structure_monitor.detect_change(
            #         source_name,
            #         found_counts
            #     )
                
            #     if change_details:
            #         logger.log_error(
            #             source_name,
            #             "Structure change detected",
            #             target_config['url']
            #         )
            #         alert_system.alert_structure_change(source_name, change_details)
                
            #     # Record current structure
            #     structure_monitor.record_structure(
            #         source_name,
            #         target_config['selectors'],
            #         found_counts
            #     )
            
            # Check for structure changes (skip for API sources)
            
            if (
                config.DETECT_STRUCTURE_CHANGES
                and target_config.get('type') != 'api'
                and 'selectors' in target_config
            ):
                found_counts = {
                    key: len([item for item in processed_data if item.get(key)])
                    for key in target_config['fields']
                }

                change_details = structure_monitor.detect_change(
                    source_name,
                    found_counts
                )

                if change_details:
                    logger.log_error(
                        source_name,
                        "Structure change detected",
                        target_config['url']
                    )
                    alert_system.alert_structure_change(source_name, change_details)

                # Record expected structure
                structure_monitor.record_structure(
                    source_name,
                    target_config['selectors'],
                    found_counts
                )    
            
            # Send completion alert if configured
            alert_system.alert_completion(stats)
            
            logger.log_scraping_complete(stats)
            
            self.jobs_run += 1
            self.total_items_scraped += len(processed_data)
            
            return {
                'success': True,
                'items_scraped': len(processed_data),
                'stats': stats
            }
            
        except Exception as e:
            logger.log_error(source_name, str(e))
            alert_system.alert_scraping_failure(source_name, str(e))
            performance_monitor.record_error({
                'source': source_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def scrape_all_sources(self) -> Dict:
        """Scrape all enabled sources"""
        logger.logger.info("Starting scrape of all sources")
        
        results = {}
        
        for source_name, config_data in config.SCRAPING_TARGETS.items():
            if config_data.get('enabled', True):
                result = self.scrape_source(source_name)
                results[source_name] = result
                
                # Add delay between sources
                time.sleep(config.REQUEST_DELAY)
        
        # Generate summary
        summary = self._generate_summary(results)
        logger.logger.info(f"Completed scraping all sources: {summary}")
        
        return summary
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of scraping results"""
        total_jobs = len(results)
        successful = sum(1 for r in results.values() if r.get('success'))
        failed = total_jobs - successful
        total_items = sum(r.get('items_scraped', 0) for r in results.values())
        
        return {
            'total_jobs': total_jobs,
            'successful': successful,
            'failed': failed,
            'total_items': total_items,
            'by_source': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_aggregated_data(self) -> DataAggregator:
        """Get all data as aggregator"""
        all_data = []
        
        for source_name in config.SCRAPING_TARGETS.keys():
            data = self.storage.get_data(source_name)
            all_data.extend(data)
        
        import pandas as pd
        df = pd.DataFrame(all_data)
        
        return DataAggregator(df)
    
    def cleanup(self):
        """Cleanup resources"""
        self.storage.close()


class ScrapingScheduler:
    """Manages scheduled scraping jobs"""
    
    def __init__(self):
        self.orchestrator = ScrapingOrchestrator()
        self.running = False
    
    def setup_schedules(self):
        """Setup all scheduled jobs"""
        logger.logger.info("Setting up schedules")
        
        # Schedule by frequency
        daily_sources = []
        weekly_sources = []
        hourly_sources = []
        
        for source_name, config_data in config.SCRAPING_TARGETS.items():
            if not config_data.get('enabled', True):
                continue
            
            schedule_type = config_data.get('schedule', 'daily')
            
            if schedule_type == 'daily':
                daily_sources.append(source_name)
            elif schedule_type == 'weekly':
                weekly_sources.append(source_name)
            elif schedule_type == 'hourly':
                hourly_sources.append(source_name)
        
        # Setup daily jobs
        if daily_sources:
            time_str = config.SCHEDULE_CONFIG['daily']
            for source in daily_sources:
                schedule.every().day.at(time_str).do(
                    self._run_job,
                    source
                ).tag('daily', source)
            logger.logger.info(f"Scheduled {len(daily_sources)} daily jobs at {time_str}")
        
        # Setup weekly jobs
        if weekly_sources:
            day, time_str = config.SCHEDULE_CONFIG['weekly'].split()
            for source in weekly_sources:
                getattr(schedule.every(), day).at(time_str).do(
                    self._run_job,
                    source
                ).tag('weekly', source)
            logger.logger.info(f"Scheduled {len(weekly_sources)} weekly jobs")
        
        # Setup hourly jobs
        if hourly_sources:
            for source in hourly_sources:
                schedule.every().hour.do(
                    self._run_job,
                    source
                ).tag('hourly', source)
            logger.logger.info(f"Scheduled {len(hourly_sources)} hourly jobs")
    
    def _run_job(self, source_name: str):
        """Run a scheduled job"""
        logger.logger.info(f"Running scheduled job: {source_name}")
        result = self.orchestrator.scrape_source(source_name)
        return result
    
    def run_now(self, source_name: str = None):
        """Run job immediately"""
        if source_name:
            return self.orchestrator.scrape_source(source_name)
        else:
            return self.orchestrator.scrape_all_sources()
    
    def start(self):
        """Start the scheduler"""
        self.setup_schedules()
        self.running = True
        
        logger.logger.info("Scheduler started")
        logger.logger.info(f"Pending jobs: {len(schedule.jobs)}")
        
        # Run scheduler loop
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_background(self):
        """Start scheduler in background thread"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        logger.logger.info("Scheduler started in background")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.logger.info("Scheduler stopped")
    
    def get_schedule_info(self) -> List[Dict]:
        """Get information about scheduled jobs"""
        jobs_info = []
        
        for job in schedule.jobs:
            jobs_info.append({
                'tags': list(job.tags),
                'next_run': str(job.next_run),
                'interval': str(job.interval),
                'unit': job.unit
            })
        
        return jobs_info
    
    def clear_schedule(self):
        """Clear all scheduled jobs"""
        schedule.clear()
        logger.logger.info("All schedules cleared")


# Main execution function
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Scraping System')
    parser.add_argument(
        '--mode',
        choices=['schedule', 'run-once', 'run-source'],
        default='schedule',
        help='Execution mode'
    )
    parser.add_argument(
        '--source',
        help='Specific source to scrape (for run-source mode)'
    )
    
    args = parser.parse_args()
    
    scheduler = ScrapingScheduler()
    
    try:
        if args.mode == 'schedule':
            # Run as scheduled service
            logger.logger.info("Starting in schedule mode")
            scheduler.start()
            
        elif args.mode == 'run-once':
            # Run all sources once
            logger.logger.info("Running all sources once")
            result = scheduler.run_now()
            print(f"\nResults: {result}")
            
        elif args.mode == 'run-source':
            # Run specific source
            if not args.source:
                print("Error: --source required for run-source mode")
                return
            
            logger.logger.info(f"Running source: {args.source}")
            result = scheduler.run_now(args.source)
            print(f"\nResults: {result}")
    
    except KeyboardInterrupt:
        logger.logger.info("Received interrupt signal")
        scheduler.stop()
        scheduler.orchestrator.cleanup()
    
    except Exception as e:
        logger.log_error('main', str(e))
        raise
    
    finally:
        logger.logger.info("Shutdown complete")


if __name__ == '__main__':
    main()