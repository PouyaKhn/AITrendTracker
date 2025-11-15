                                           
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass                                                          

import fetcher
import processor
from ai_classifier import classify_articles_ai_topics, get_ai_topic_summary
from database import get_database, init_database
from logger import get_logger
from config import load_config
from datetime import datetime
from pathlib import Path
from typing import Set

from summaries import (
    load_danish_summary_cache,
    save_danish_summary_cache,
    translate_summary_to_danish,
)

                   
logger = get_logger(__name__)


def _is_danish_article(article) -> bool:
    """
    Determine if an article is Danish based on domain and language.
    
    Args:
        article: Article dictionary with 'domain' and 'language' fields
        
    Returns:
        bool: True if the article is Danish, False otherwise
    """
    domain = article.get('domain', '').lower()
    language = article.get('language', 'en').lower()
    
    danish_domains = [
                                                  
        'journalisten.dk', 'dr.dk', 'tv2.dk', 'berlingske.dk', 'jyllands-posten.dk', 
        'ekstrabladet.dk', 'bt.dk', 'information.dk', 'weekendavisen.dk', 
        'kristeligt-dagblad.dk', 'kforum.dk', 'medietrends.dk', 'mediawatch.dk', 
        'markedsforing.dk', 'bureaubiz.dk', 'ekkofilm.dk', 'digitalfoto.dk', 
        'soundvenue.dk', 'ddc.dk', 'computerworld.dk', 'version2.dk', 'elektronista.dk',
        'politiken.dk', 'arbejderen.dk', 'avisen.dk', 'nordjyske.dk', 'sn.dk', 'fyens.dk'
    ]
    
    return any(danish_domain == domain for danish_domain in danish_domains) or language == 'da'


def run_batch():
    """Orchestrate article fetching, processing, and database storage."""
    db = init_database()
    config = load_config()

    storage_dir = config.storage_dir if hasattr(config, "storage_dir") else Path("data")
    summary_cache_path = Path(storage_dir) / "danish_summaries.json"
    summary_cache = load_danish_summary_cache(summary_cache_path)
    summary_cache_updated = False

                             
    run_id = db.start_pipeline_run()
    
    stats = {
        'fetched_articles': 0,
        'validated_articles': 0,
        'stored_articles': 0,
        'rejected_articles': 0,
        'failed_fetching': 0,
        'failed_processing': 0,
        'failed_validation': 0,
        'failed_storage': 0,
        'ai_topic_count': 0,
        'processing_time': 0,
        'failed_domains': [],
        'domain_failure_count': 0
    }

    start_time = datetime.now()

    try:
                                                              
                                                                               
        try:
                                          
            max_articles = config.max_articles
            
                                                                 
            logger.info("📡 Using GDELT only for fetching articles (fallbacks disabled)")
            
                                                                       
            articles = fetcher.fetch_gdelt_news_articles()
            
                                       
            tracker = fetcher.get_domain_failure_tracker()
            failure_report = tracker.get_failed_domains_report()
            
                                                                                
            if not articles:
                logger.info("No new articles fetched in this batch.")
                                                                         
                db.complete_pipeline_run(run_id, stats)
                return stats
                
            stats['fetched_articles'] = len(articles)
            logger.info(f"Successfully obtained {len(articles)} real articles from GDELT")
            
                                                             
            if failure_report['total_failures'] > 0:
                logger.warning(f"Domain failure report: {failure_report['total_failures']} failed domains")
                for domain, count in failure_report['failure_counts'].items():
                    logger.warning(f"  - {domain}: {count} failures")
                stats['failed_domains'] = failure_report['failed_domains']
                stats['domain_failure_count'] = failure_report['total_failures']
            else:
                logger.info("No domain failures detected")
            
        except (fetcher.DownloadError, fetcher.ExtractionError, fetcher.FetcherError) as e:
                                                             
            logger.warning(f"GDELT data fetch failed: {e} - skipping this batch")
            stats['failed_fetching'] += 1
            return stats

                                               
        logger.info("Processing and validating articles")
        processed_articles = []
        rejected_articles = []
        
        for article in articles:
            try:
                if processor.validate_article(article):
                    processed_article = processor.process_article(article)
                    processed_articles.append(processed_article)
                else:
                    logger.debug(f"Article failed validation: {article.get('url', 'unknown')}")
                                                                    
                    article['rejection_reason'] = 'validation_failed'
                    rejected_articles.append(article)
            except Exception as e:
                logger.warning(f"Error processing article: {e}")
                stats['failed_processing'] += 1
                                                                
                article['rejection_reason'] = f'processing_error: {str(e)}'
                rejected_articles.append(article)

        initial_validated = len(processed_articles)
        stats['validated_articles'] = initial_validated
        logger.info(f"Successfully processed {initial_validated} articles from initial fetch")

                                                                     
        target_articles = config.max_articles
        
                                                                
        if target_articles == 0:
            logger.info("🔄 Unlimited mode: skipping quota logic (all articles already fetched)")
                                           
            pass
        else:
                                                              
            target_danish = target_articles // 2
            target_english = target_articles - target_danish
            
            if len(processed_articles) < target_articles:
                                                                                               
                current_danish = 0
                current_english = 0
                
                for article in processed_articles:
                    if _is_danish_article(article):
                        current_danish += 1
                    else:
                        current_english += 1
                
                missing_danish = max(0, target_danish - current_danish)
                missing_english = max(0, target_english - current_english)
                total_missing = missing_danish + missing_english
                
                logger.info(f"Need {total_missing} more valid articles ({missing_danish} Danish, {missing_english} English)")
            
                                                                           

                                                               
        logger.info("Removing database duplicates from processed articles")
        try:
            processed_urls = db.get_processed_urls()
            logger.debug(f"Found {len(processed_urls)} already processed URLs in database")
            
            from fetcher import normalize_domain_for_dedup
            
            seen_domain_title: Set[tuple] = set()
            final_articles = []
            duplicates_removed = 0
            removed_danish_count = 0
            removed_english_count = 0
            
                                                        
            for article in processed_articles:
                url = article.get('url', '')
                title = article.get('title', '').strip().lower()
                domain = article.get('domain', '')
                
                is_duplicate = False
                
                if url and url in processed_urls:
                    is_duplicate = True
                elif domain and title:
                    normalized_domain = normalize_domain_for_dedup(domain)
                    domain_title_key = (normalized_domain, title)
                    if domain_title_key in seen_domain_title:
                        is_duplicate = True
                        logger.debug(f"Duplicate detected by domain+title: {normalized_domain} - '{title[:50]}...'")
                    else:
                        seen_domain_title.add(domain_title_key)
                
                if not is_duplicate:
                    final_articles.append(article)
                else:
                    duplicates_removed += 1
                                                        
                    if _is_danish_article(article):
                        removed_danish_count += 1
                        logger.debug(f"Removing Danish duplicate: {url}")
                    else:
                        removed_english_count += 1
                        logger.debug(f"Removing English duplicate: {url}")
            
            logger.info(f"Removed {duplicates_removed} database duplicates ({removed_danish_count} Danish, {removed_english_count} English), keeping {len(final_articles)} articles")
            processed_articles = final_articles
            
                                                                            
                                                                                                                
            total_removed = removed_danish_count + removed_english_count
            if total_removed > 0:
                logger.info(f"Removed {total_removed} duplicates but continuing with unlimited mode - no replacement needed")
                                                                                   
                                                                                    
            
        except Exception as e:
            logger.warning(f"Failed to remove database duplicates: {e}")
                                                                         

                                         
        logger.info("Starting AI topic classification")
        if processed_articles:
            try:
                ai_results = classify_articles_ai_topics(processed_articles)
                stats['ai_topic_count'] = len(
                    [
                        a
                        for a in ai_results
                        if a.get("ai_topic_analysis", {}).get("is_ai_topic", False)
                    ]
                )
                logger.info(
                    f"AI topic classification completed: {stats['ai_topic_count']} AI-related articles detected"
                )
            except Exception as e:
                logger.warning(f"AI topic classification failed: {e}")
                stats["ai_topic_count"] = 0
        else:
            stats["ai_topic_count"] = 0

        for article in processed_articles:
            analysis = article.get("ai_topic_analysis", {}) or {}

            if analysis:
                article["ai_topic"] = analysis.get("topic")
                article["ai_confidence"] = analysis.get("confidence")
                article["ai_keywords"] = analysis.get("keywords", [])

            summary_en = analysis.get("explanation") if analysis else None
            if summary_en:
                if summary_en.startswith("OpenAI: "):
                    summary_en = summary_en[8:]
                article["summary_en"] = summary_en

            if analysis.get("is_ai_topic"):
                url = article.get("url", "")
                danish_summary, cache_changed = translate_summary_to_danish(
                    summary_en or "",
                    url,
                    summary_cache,
                )
                article["summary_da"] = danish_summary or summary_en or ""
                if cache_changed:
                    summary_cache_updated = True
            elif summary_en:
                article["summary_da"] = summary_en

                                                      
        if processed_articles or rejected_articles:
            logger.info("Storing processed articles")
            try:
                storage_files = processor.store_articles(processed_articles, rejected_articles)
                articles_file, articles_metadata_file, rejected_file, rejected_metadata_file = storage_files
                
                stats['stored_articles'] = len(processed_articles)
                stats['rejected_articles'] = len(rejected_articles)
                
                                                   
                if articles_file:
                    db.add_processed_articles(processed_articles, str(articles_file))
                
                                                                     
                if rejected_file:
                    db.add_rejected_articles(rejected_articles, str(rejected_file))
                
                logger.info(f"Successfully stored {len(processed_articles)} valid articles and {len(rejected_articles)} rejected articles")
                logger.info(f"Files created: {articles_file}, {articles_metadata_file}, {rejected_file}, {rejected_metadata_file}")

                if summary_cache_updated:
                    save_danish_summary_cache(summary_cache_path, summary_cache)
            except Exception as e:
                logger.error(f"Failed to store articles: {e}")
                stats['failed_storage'] = len(processed_articles) + len(rejected_articles)
        else:
            logger.warning("No articles to store (valid or rejected)")

    except fetcher.FetcherError as e:
        logger.error(f"Fetcher error: {e}")
        stats['failed_fetching'] += 1

    except processor.ProcessorError as e:
        logger.error(f"Processor error: {e}")
        stats['failed_processing'] += 1

    except processor.ValidationError as e:
        logger.error(f"Validation error: {e}")
        stats['failed_validation'] += 1

    except processor.StorageError as e:
        logger.error(f"Storage error: {e}")
        stats['failed_storage'] += 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        stats['failed_fetching'] += 1

                               
    processing_time = (datetime.now() - start_time).total_seconds()
    stats['processing_time'] = processing_time
    
                                    
    db.complete_pipeline_run(run_id, stats)
    
    logger.info(f"Batch run completed in {processing_time:.2f} seconds")
    logger.info(f"Batch run summary: {stats}")
    
    return stats


                                                                                                        

