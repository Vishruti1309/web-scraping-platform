"""
Quick Start Example - Web Scraping System
Simple examples to get you started quickly
8. examples.py demonstrates how to run/test parts of the system
"""

# EXAMPLE 1: Run a Single Scraping Job

def example_1_simple_scrape():
    """Run a simple scrape of one source"""
    print("=" * 60)
    print("EXAMPLE 1: Simple Single-Source Scraping")   
    print("=" * 60)
    
    from scheduler_orchestrator import ScrapingOrchestrator
    
    # Initialize orchestrator
    orchestrator = ScrapingOrchestrator()
    
    # Scrape the 'quotes' source
    result = orchestrator.scrape_source('quotes')
    
    print(f"\n Scraping completed!")
    print(f"Success: {result['success']}")
    print(f"Items scraped: {result.get('items_scraped', 0)}")
    
    if result['success']:
        print(f"\n Stats:")
        for key, value in result['stats'].items():
            print(f"  {key}: {value}")
    
    # Cleanup
    orchestrator.cleanup()


# EXAMPLE 2: Scrape All Sources

def example_2_scrape_all():
    """Scrape all configured sources"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Scrape All Sources")
    print("=" * 60)
    
    from scheduler_orchestrator import ScrapingOrchestrator
    
    orchestrator = ScrapingOrchestrator()
    
    # Scrape all enabled sources
    summary = orchestrator.scrape_all_sources()
    
    print(f"\n All scraping completed!")
    print(f"Total jobs: {summary['total_jobs']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Total items: {summary['total_items']}")
    
    print(f"\n Results by source:")
    for source, result in summary['by_source'].items():
        status = "" if result['success'] else ""
        items = result.get('items_scraped', 0)
        print(f"  {status} {source}: {items} items")
    
    orchestrator.cleanup()


# EXAMPLE 3: Access Stored Data
def example_3_access_data():
    """Retrieve and display stored data"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Access Stored Data")
    print("=" * 60)
    
    from storage_manager import StorageManager
    import pandas as pd
    
    storage = StorageManager()
    
    # Get data from specific source
    quotes_data = storage.get_data('quotes', limit=10)
    
    print(f"\n Retrieved {len(quotes_data)} items from 'quotes' source")
    
    if quotes_data:
        # Convert to DataFrame for display
        df = pd.DataFrame(quotes_data)
        print("\n Sample data:")
        print(df.head())
        
        print(f"\n Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
    
    # Get scraping history
    history = storage.get_history(limit=5)
    
    print(f"\n Recent scraping history:")
    for record in history:
        print(f"  {record['timestamp']}: {record['source']} - "
              f"{record['items_scraped']} items, {record['errors']} errors")
    
    storage.close()


# EXAMPLE 4: Export Data

def example_4_export_data():
    """Export data to various formats"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Export Data")
    print("=" * 60)
    
    from storage_manager import StorageManager, FileExporter
    
    storage = StorageManager()
    exporter = FileExporter()
    
    # Get data
    data = storage.get_data('quotes', limit=100)
    
    if not data:
        print("No data to export")
        return
    
    print(f" Exporting {len(data)} items...")
    
    # Export to all formats
    results = exporter.export_all_formats(data, 'quotes_export')
    
    print("\nExport complete!")
    for format_type, filepath in results.items():
        if filepath:
            print(f"  {format_type.upper()}: {filepath}")
    
    storage.close()


# EXAMPLE 5: Data Processing Pipeline

def example_5_data_pipeline():
    """Complete data processing pipeline"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Data Processing Pipeline")
    print("=" * 60)
    
    from scraper_engine import ScraperEngine
    from data_processor import DataProcessor
    from storage_manager import StorageManager
    import config
    
    # Get configuration
    target_config = config.SCRAPING_TARGETS['quotes']
    
    print(f"\n1. Scraping: {target_config['name']}")
    scraper = ScraperEngine(target_config)
    raw_data = scraper.scrape()
    print(f"    Scraped {len(raw_data)} items")
    
    print(f"\n2. Processing data...")
    processor = DataProcessor()
    processed_data = processor.process_batch(raw_data)
    print(f"   Processed {len(processed_data)} items")
    print(f"   Removed {processor.duplicates_removed} duplicates")
    
    print(f"\n3. Validating data...")
    validation = processor.validate_data(processed_data)
    print(f"   Valid: {validation['valid']}")
    print(f"   Total records: {validation['total_records']}")
    if validation['warnings']:
        print(f"  Warnings:")
        for warning in validation['warnings']:
            print(f"      - {warning}")
    
    print(f"\n4. Saving to database...")
    storage = StorageManager()
    success = storage.save_data(processed_data, 'quotes')
    print(f"    Saved to database" if success else "    Save failed")
    
    print(f"\n5. Getting statistics...")
    stats = processor.get_statistics()
    print(f"   Total records processed: {stats['total_records']}")
    print(f"   Duplicates removed: {stats['duplicates_removed']}")
    
    # Cleanup
    scraper.cleanup()
    storage.close()


# EXAMPLE 6: Monitor Performance

def example_6_performance_monitoring():
    """Monitor scraping performance"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Performance Monitoring")
    print("=" * 60)
    
    from monitoring_alerts import performance_monitor
    from scheduler_orchestrator import ScrapingOrchestrator
    
    orchestrator = ScrapingOrchestrator()
    
    # Run some scraping jobs
    print("\n Running scraping jobs...")
    orchestrator.scrape_source('quotes')
    orchestrator.scrape_source('books')
    
    # Get performance summary
    print("\n Performance Summary:")
    summary = performance_monitor.get_summary()
    
    print(f"  Total jobs: {summary.get('total_jobs', 0)}")
    print(f"  Total items: {summary.get('total_items_scraped', 0)}")
    print(f"  Success rate: {summary.get('success_rate', 0)*100:.1f}%")
    print(f"  Average duration: {summary.get('average_duration', 0):.2f}s")
    print(f"  Average items/job: {summary.get('average_items_per_job', 0):.0f}")
    
    # Get source-specific performance
    print("\n Source Performance:")
    for source in ['quotes', 'books']:
        perf = performance_monitor.get_source_performance(source)
        if 'total_runs' in perf:
            print(f"  {source}:")
            print(f"    Runs: {perf['total_runs']}")
            print(f"    Avg duration: {perf['average_duration']:.2f}s")
            print(f"    Avg items: {perf['average_items_per_run']:.0f}")
    
    orchestrator.cleanup()


# EXAMPLE 7: Custom Data Aggregation

def example_7_data_aggregation():
    """Aggregate and analyze data"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Data Aggregation & Analysis")
    print("=" * 60)
    
    from scheduler_orchestrator import ScrapingOrchestrator
    
    orchestrator = ScrapingOrchestrator()
    
    # Get aggregated data
    print("\n Aggregating data from all sources...")
    aggregator = orchestrator.get_aggregated_data()
    
    # Get summary
    summary = aggregator.get_summary()
    
    print(f"\n Data Summary:")
    print(f"  Total records: {summary.get('total_records', 0)}")
    print(f"  Date range: {summary.get('date_range', {})}")
    print(f"  Sources: {summary.get('sources', {})}")
    
    # Group by source
    grouped = aggregator.group_by_source()
    
    print(f"\n Data by Source:")
    for source, df in grouped.items():
        print(f"  {source}: {len(df)} records")
    
    orchestrator.cleanup()


# EXAMPLE 8: Test Configuration

def example_8_test_configuration():
    """Test your configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Configuration Test")
    print("=" * 60)
    
    import config
    from pathlib import Path
    
    # Check directories
    print("\n Directory Check:")
    dirs = {
        'Base': config.BASE_DIR,
        'Data': config.DATA_DIR,
        'Logs': config.LOG_DIR,
        'Exports': config.EXPORT_DIR
    }
    
    for name, path in dirs.items():
        exists = Path(path).exists()
        status = "" if exists else ""
        print(f"  {status} {name}: {path}")
    
    # Check scraping targets
    print("\n Scraping Targets:")
    for source_name, config_data in config.SCRAPING_TARGETS.items():
        enabled = "" if config_data.get('enabled') else ""
        print(f"  {enabled} {source_name}")
        print(f"      URL: {config_data['url']}")
        print(f"      Type: {config_data['type']}")
        print(f"      Schedule: {config_data.get('schedule', 'N/A')}")
    
    # Check database
    print(f"\n Database:")
    print(f"  Type: {config.DATABASE_TYPE}")
    if config.DATABASE_TYPE == 'sqlite':
        db_exists = Path(config.SQLITE_DB).exists()
        status = "" if db_exists else "📝 (will be created)"
        print(f"  {status} {config.SQLITE_DB}")
    
    # Check email alerts
    print(f"\n Email Alerts:")
    enabled = " Enabled" if config.ENABLE_EMAIL_ALERTS else " Disabled"
    print(f"  {enabled}")
    if config.ENABLE_EMAIL_ALERTS:
        print(f"  Server: {config.EMAIL_CONFIG['smtp_server']}")
        print(f"  From: {config.EMAIL_CONFIG['sender_email']}")
    
    # Check export formats
    print(f"\n Export Formats:")
    for fmt in config.EXPORT_FORMATS:
        print(f"   {fmt.upper()}")


# EXAMPLE 9: Add Custom Source (Interactive)

def example_9_add_custom_source():
    """Interactive guide to add a new source"""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Add Custom Source (Interactive)")
    print("=" * 60)
    
    print("\n This will guide you through adding a new scraping source")
    print("You'll need to provide selectors from the target website\n")
    
    # Get user input
    name = input("Enter source name (e.g., 'mynewsite'): ").strip()
    display_name = input("Enter display name (e.g., 'My New Site'): ").strip()
    url = input("Enter URL: ").strip()
    
    print("\nIs the site's content loaded with JavaScript?")
    site_type = input("Type 'dynamic' or 'static' [static]: ").strip() or 'static'
    
    print("\nProvide CSS selectors for data extraction:")
    container = input("Container selector (e.g., '.item'): ").strip()
    
    selectors = {'container': container}
    fields = []
    
    while True:
        field_name = input("\nField name (or press Enter to finish): ").strip()
        if not field_name:
            break
        
        selector = input(f"Selector for '{field_name}': ").strip()
        selectors[field_name] = selector
        fields.append(field_name)
    
    # Generate configuration
    config_text = f"""
# Add this to SCRAPING_TARGETS in config.py:

'{name}': {{
    'name': '{display_name}',
    'url': '{url}',
    'type': '{site_type}',
    'enabled': True,
    'schedule': 'daily',
    'selectors': {selectors},
    'fields': {fields + ['scraped_at']},
    'pagination': False
}},
"""
    
    print("\n" + "=" * 60)
    print(" Configuration generated!")
    print("=" * 60)
    print(config_text)
    print("\n Copy the above configuration to config.py")
    print("Then test with:")
    print(f"  python scheduler_orchestrator.py --mode run-source --source {name}")


# MAIN MENU

def main():
    """Interactive menu for examples"""
    
    examples = {
        '1': ('Simple Single-Source Scraping', example_1_simple_scrape),
        '2': ('Scrape All Sources', example_2_scrape_all),
        '3': ('Access Stored Data', example_3_access_data),
        '4': ('Export Data', example_4_export_data),
        '5': ('Data Processing Pipeline', example_5_data_pipeline),
        '6': ('Performance Monitoring', example_6_performance_monitoring),
        '7': ('Data Aggregation & Analysis', example_7_data_aggregation),
        '8': ('Test Configuration', example_8_test_configuration),
        '9': ('Add Custom Source (Interactive)', example_9_add_custom_source),
    }
    
    print("\n" + "=" * 70)
    print("        WEB SCRAPING SYSTEM - QUICK START EXAMPLES")
    print("=" * 70)
    
    print("\nChoose an example to run:\n")
    
    for key, (title, _) in examples.items():
        print(f"  [{key}] {title}")
    
    print(f"  [0] Run All Examples (sequentially)")
    print(f"  [Q] Quit")
    
    choice = input("\nEnter your choice: ").strip().upper()
    
    if choice == 'Q':
        print("\n👋 Goodbye!")
        return
    
    if choice == '0':
        print("\n Running all examples...")
        for key in sorted(examples.keys()):
            _, func = examples[key]
            try:
                func()
                print("\n" + "-" * 70)
                input("Press Enter to continue to next example...")
            except Exception as e:
                print(f"\n Error in example: {e}")
                import traceback
                traceback.print_exc()
    
    elif choice in examples:
        _, func = examples[choice]
        try:
            func()
        except Exception as e:
            print(f"\n Error: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("\n Invalid choice")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        import traceback
        traceback.print_exc()