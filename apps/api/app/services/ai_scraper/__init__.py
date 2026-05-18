"""CustomerFlow Official Crawler Service.

File layout (per spec):
    fetcher.py        — fetch_page()
    cleaner.py        — clean_content()
    link_extractor.py — extract_links()
    parser.py         — URL generation from patterns
    batcher.py        — batch_content()
    ai_processor.py   — process_batch()
    task_runner.py    — store_result(), insert_lead(), ARQ entry
    crawler.py        — crawl_task()  (main orchestrator)
"""
