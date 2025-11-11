#!/usr/bin/env python3
"""
Language Configuration for AI Trend Tracker
Supports English and Danish languages
"""

LANGUAGES = {
    'en': {
                   
        'app_title': 'AI Trend Tracker',
        'welcome_text': 'Stay up to date on the latest AI news and trends from trusted sources: automatically tracked, analyzed, and presented to you in real time.',
        'read_more': '+ Read more here',
        'detailed_description': 'The AI Trend Tracker is an intelligent news monitoring system that automatically scans news articles from famous English and Danish domains covered by the GDELT corpus to identify and analyze AI-related content. Using advanced artificial intelligence, the system categorizes articles by AI topics, tracks trends over time, and provides real-time insights into how artificial intelligence is being discussed in these curated media sources. Whether you\'re a researcher, journalist, business professional, or simply curious about AI developments, this tool helps you stay informed about the latest AI news and trends from trusted sources without having to manually search through countless websites. The system runs continuously, processing new articles every few hours and presenting the most relevant AI-related content in an easy-to-understand dashboard with interactive charts and detailed article summaries.',
        
                 
        'start_button': 'START',
        'stop_button': 'STOP',
        'refresh_stats': 'Refresh Stats',
        'clear_database': 'Clear Database',
        'check_status': 'Check Status',
        'login': 'Admin Login',
        'logout': 'Logout',
        'back_to_main': 'Back to Main',
        'confirm_clear': 'Confirm Clear',
        'cancel': 'Cancel',
        
                     
        'username': 'Username',
        'password': 'Password',
        'enter_username': 'Enter your username',
        'enter_password': 'Enter your password',
        
                              
        'admin_controls': 'Admin Controls',
        'pipeline_status': 'Pipeline Status',
        'statistics': 'Statistics',
        'recent_articles': 'Recent Articles',
        'trend_charts': 'Trend Charts',
        'admin_login': 'Admin Login',
        'language_selection': 'Language / Sprog',
        
                         
        'pipeline_running': 'Pipeline is running',
        'pipeline_running_with_interval': 'Pipeline is running - Processing articles every 2 hours',
        'pipeline_stopped': 'Pipeline is stopped',
        'pipeline_stopped_click_start': 'Pipeline is stopped - Click Start to begin',
        'pipeline_starting': 'Starting pipeline...',
        'pipeline_stopping': 'Stopping pipeline...',
        'pipeline_error': 'Pipeline ERROR',
        'tracker_online': 'AI Trend Tracker is online - Data updates automatically.',
        'tracker_offline': 'AI Trend Tracker is offline.',
        'no_articles_found': 'No articles found',
        'no_ai_articles_found': 'No AI-related articles found yet.',
        'no_ai_topics_data': 'No AI topics data available yet.',
        'no_category_data': 'No category data available yet.',
        'loading_articles': 'Loading articles...',
        'processing_articles': 'Processing articles...',
        
                           
        'total_articles': 'Total Articles',
        'ai_articles': 'AI Articles',
        'processing_rate': 'Processing Rate',
        'last_run': 'Last Run',
        'articles_per_hour': 'Articles/Hour',
        'success_rate': 'Success Rate',
        'ai_detection_rate': 'AI Detection Rate',
        
                     
        'never': 'Never',
        'minutes_ago': 'minutes ago',
        'hours_ago': 'hours ago',
        'days_ago': 'days ago',
        'just_now': 'Just now',
        
                         
        'article_title': 'Title',
        'article_url': 'URL',
        'article_domain': 'Domain',
        'article_language': 'Language',
        'article_published': 'Published',
        'article_processed': 'Processed',
        'article_topic': 'Topic',
        'article_confidence': 'Confidence',
        'article_keywords': 'Keywords',
        'article_summary': 'Summary',
        'view_original': 'View Original',
        'copy_url': 'Copy URL',
        
                        
        'login_failed': 'Login failed. Please check your credentials.',
        'login_successful': 'Login successful! Redirecting to main page...',
        'pipeline_error': 'Pipeline error occurred',
        'database_error': 'Database error occurred',
        'network_error': 'Network error occurred',
        'unknown_error': 'Unknown error occurred',
        
                               
        'confirm_clear_database': 'Are you sure you want to clear all database data? This action cannot be undone.',
        'database_cleared': 'Database cleared successfully',
        'pipeline_started': 'Pipeline started successfully',
        'pipeline_stopped': 'Pipeline stopped successfully',
        
                
        'footer_built_with': 'Built with Streamlit',
        'footer_description': 'Crawl and analyse English and Danish AI-related articles from journalism, media and commercial sources in near real-time.',
        
                      
        'topics_distribution': 'Topics Distribution',
        'articles_by_domain': 'Articles by Domain Category',
        'ai_trends': 'AI Trends',
        'hourly_trends': 'Hourly Trends (Today)',
        'daily_trends': 'Daily Trends (This Week)',
        'weekly_trends': 'Weekly Trends (This Month)',
        'monthly_trends': 'Monthly Trends (This Year)',
        'yearly_trends': 'Yearly Trends',
        
                                     
        'live_statistics': 'Live Statistics',
        'live_updates': 'Live Updates',
        'manual_refresh_available': 'Manual refresh available',
        'use_refresh_buttons': 'Use refresh buttons below to see live updates',
        
                            
        'prev': 'Prev',
        'next': 'Next',
        
                                
        'title': 'Title',
        'summary': 'Summary',
        'domain': 'Domain',
        'category': 'Category',
        'ai_topic': 'AI Topic',
        'ai_confidence': 'AI Confidence',
        'language': 'Language',
        'published': 'Published',
        'processed': 'Processed',
        
                                  
        'ai_articles_by_topic': 'AI Articles by AI Topic',
        'ai_articles_by_category': 'AI Articles by Category',
        'ai_articles_trend': 'AI Articles Trend',
        'ai_topics': 'AI Topics',
        'number_of_articles': 'Number of Articles',
        'categories': 'Categories',
        'hours': 'Hours',
        'days_of_week': 'Days of Week',
        'weeks': 'Weeks',
        'months': 'Months',
        'years': 'Years',
        
                      
        'hourly': 'Hourly',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'yearly': 'Yearly',
        'select_time_period': 'Select time period:',
        'time_period': 'Time Period',
        
                   
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday',
        
                     
        'january': 'January',
        'february': 'February',
        'march': 'March',
        'april': 'April',
        'may': 'May',
        'june': 'June',
        'july': 'July',
        'august': 'August',
        'september': 'September',
        'october': 'October',
        'november': 'November',
        'december': 'December',
        
                     
        'week_1': 'Week 1',
        'week_2': 'Week 2',
        'week_3': 'Week 3',
        'week_4': 'Week 4',
        
                        
        'admin_credentials_message': 'Please enter your admin credentials to access pipeline controls.',
        'contact_admin_message': 'Contact the system administrator if you need access credentials.',
        
                   
        'ai_research_development': 'AI Research and Development',
        'ai_ethics_regulations': 'AI Ethics and Regulations',
        'ai_safety_governance': 'AI Safety and Governance',
        'ai_business_industry': 'AI Business and Industry',
        'ai_language_models_nlp': 'AI Language Models and NLP',
        'ai_robotics_automation': 'AI Robotics and Automation',
        'ai_healthcare_medical': 'AI Healthcare and Medical',
        'ai_education_training': 'AI Education and Training',
        'ai_cybersecurity_privacy': 'AI Cybersecurity and Privacy',
        'ai_computer_vision': 'AI Computer Vision',
        'ai_data_science_analytics': 'AI Data Science and Analytics',
        'ai_neural_networks_deep_learning': 'AI Neural Networks and Deep Learning',
        'ai_applications_deployment': 'AI Applications and Deployment',
        'ai_technology_infrastructure': 'AI Technology and Infrastructure',
        
                           
        'advertising_commercial': 'Advertising and Commercial',
        'journalism_news_media': 'Journalism, News and Media',
        'digital_media_content_creation': 'Digital Media and Content Creation',
        'strategic_communication_pr': 'Strategic Communication and PR',
        'photography': 'Photography',
        'web_ux_design': 'Web and UX Design',
        'film_tv_production': 'Film and TV Production',
        'unknown': 'Unknown',
        
                    
        'page': 'Page',
        'of': 'of',
        'previous': 'Previous',
        'next': 'Next',
        'showing': 'Showing',
        'to': 'to',
        'of_total': 'of total',
        
                    
        'journalism_news_media': 'Journalism, News and Media',
        'advertising_commercial': 'Advertising and Commercial',
        'digital_media_content': 'Digital Media and Content Creation',
        'strategic_communication_pr': 'Strategic Communication and PR',
        'photography': 'Photography',
        'web_ux_design': 'Web and UX Design',
        'film_tv_production': 'Film and TV Production',
        'other': 'Other',
        
                 
        'filter_articles': 'Filter Articles',
        'all': 'All',
    },
    
    'da': {
                   
        'app_title': 'AI Trend Tracker',
        'welcome_text': 'Hold dig opdateret på de seneste AI-nyheder og trends fra pålidelige kilder: automatisk sporet, analyseret og præsenteret for dig i realtid.',
        'read_more': '+ Læs mere her',
        'detailed_description': 'AI Trend Tracker er et intelligent nyhedsmonitoringssystem, der automatisk scanner nyhedsartikler fra berømte engelske og danske domæner dækket af GDELT-korpuset for at identificere og analysere AI-relateret indhold. Ved hjælp af avanceret kunstig intelligens kategoriserer systemet artikler efter AI-emner, sporer trends over tid og giver realtidsindsigt i, hvordan kunstig intelligens diskuteres i disse kurerede mediekilder. Uanset om du er forsker, journalist, forretningsprofessionel eller bare nysgerrig på AI-udvikling, hjælper dette værktøj dig med at holde dig informeret om de seneste AI-nyheder og trends fra pålidelige kilder uden at skulle manuelt søge gennem utallige websteder. Systemet kører kontinuerligt, behandler nye artikler hver få timer og præsenterer det mest relevante AI-relaterede indhold i et letforståeligt dashboard med interaktive diagrammer og detaljerede artikelsammenfatninger.',
        
                 
        'start_button': 'START',
        'stop_button': 'STOP',
        'refresh_stats': 'Opdater statistikker',
        'clear_database': 'Ryd database',
        'check_status': 'Tjek status',
        'login': 'Admin login',
        'logout': 'Log ud',
        'back_to_main': 'Tilbage til hovedside',
        'confirm_clear': 'Bekræft rydning',
        'cancel': 'Annuller',
        
                     
        'username': 'Brugernavn',
        'password': 'Adgangskode',
        'enter_username': 'Indtast dit brugernavn',
        'enter_password': 'Indtast din adgangskode',
        
                              
        'admin_controls': 'Admin kontroller',
        'pipeline_status': 'Pipeline status',
        'statistics': 'Statistikker',
        'recent_articles': 'Seneste artikler',
        'trend_charts': 'Trend diagrammer',
        'admin_login': 'Admin login',
        'language_selection': 'Language / Sprog',
        
                         
        'pipeline_running': 'Pipeline kører',
        'pipeline_running_with_interval': 'Pipeline kører - Behandler artikler hver 2. time',
        'pipeline_stopped': 'Pipeline er stoppet',
        'pipeline_stopped_click_start': 'Pipeline er stoppet - Klik på Start for at begynde',
        'pipeline_starting': 'Starter pipeline...',
        'pipeline_stopping': 'Stopper pipeline...',
        'pipeline_error': 'Pipeline FEJL',
        'tracker_online': 'AI Trend Tracker er online - Data opdateres automatisk.',
        'tracker_offline': 'AI Trend Tracker er offline.',
        'no_articles_found': 'Ingen artikler fundet',
        'no_ai_articles_found': 'Ingen AI-relaterede artikler fundet endnu.',
        'no_ai_topics_data': 'Ingen AI-emnedata tilgængelig endnu.',
        'no_category_data': 'Ingen kategoridata tilgængelig endnu.',
        'loading_articles': 'Indlæser artikler...',
        'processing_articles': 'Behandler artikler...',
        
                           
        'total_articles': 'Samlede artikler',
        'ai_articles': 'AI-artikler',
        'processing_rate': 'Behandlingshastighed',
        'last_run': 'Sidste kørsel',
        'articles_per_hour': 'Artikler/time',
        'success_rate': 'Succesrate',
        'ai_detection_rate': 'AI-detektionsrate',
        
                     
        'never': 'Aldrig',
        'minutes_ago': 'minutter siden',
        'hours_ago': 'timer siden',
        'days_ago': 'dage siden',
        'just_now': 'Lige nu',
        
                         
        'article_title': 'Titel',
        'article_url': 'URL',
        'article_domain': 'Domæne',
        'article_language': 'Sprog',
        'article_published': 'Udgivet',
        'article_processed': 'Behandlet',
        'article_topic': 'Emne',
        'article_confidence': 'Tillid',
        'article_keywords': 'Nøgleord',
        'article_summary': 'Sammenfatning',
        'view_original': 'Se original',
        'copy_url': 'Kopier URL',
        
                        
        'login_failed': 'Login mislykkedes. Tjek dine legitimationsoplysninger.',
        'login_successful': 'Login succesfuldt! Omdirigerer til hovedside...',
        'pipeline_error': 'Pipeline-fejl opstod',
        'database_error': 'Database-fejl opstod',
        'network_error': 'Netværksfejl opstod',
        'unknown_error': 'Ukendt fejl opstod',
        
                               
        'confirm_clear_database': 'Er du sikker på, at du vil rydde alle database-data? Denne handling kan ikke fortrydes.',
        'database_cleared': 'Database ryddet succesfuldt',
        'pipeline_started': 'Pipeline startet succesfuldt',
        'pipeline_stopped': 'Pipeline stoppet succesfuldt',
        
                
        'footer_built_with': 'Bygget med Streamlit',
        'footer_description': 'Crawl og analyser engelske og danske AI-relaterede artikler fra journalistik, medier og kommercielle kilder i næsten realtid.',
        
                      
        'topics_distribution': 'Emnefordeling',
        'articles_by_domain': 'Artikler efter domænekategori',
        'ai_trends': 'AI tendenser',
        'hourly_trends': 'Timebaserede trends (i dag)',
        'daily_trends': 'Daglige trends (denne uge)',
        'weekly_trends': 'Ugentlige trends (denne måned)',
        'monthly_trends': 'Månedlige trends (dette år)',
        'yearly_trends': 'Årlige trends',
        
                                     
        'live_statistics': 'Live statistikker',
        'live_updates': 'Live opdateringer',
        'manual_refresh_available': 'Manuel opdatering tilgængelig',
        'use_refresh_buttons': 'Brug opdateringsknapperne nedenfor for at se live opdateringer',
        
                            
        'prev': 'Forrige',
        'next': 'Næste',
        
                                
        'title': 'Titel',
        'summary': 'Sammenfatning',
        'domain': 'Domæne',
        'category': 'Kategori',
        'ai_topic': 'AI emne',
        'ai_confidence': 'AI tillid',
        'language': 'Sprog',
        'published': 'Udgivet',
        'processed': 'Behandlet',
        
                                  
        'ai_articles_by_topic': 'AI-artikler efter AI emne',
        'ai_articles_by_category': 'AI-artikler efter kategori',
        'ai_articles_trend': 'AI-artikler trend',
        'ai_topics': 'AI emner',
        'number_of_articles': 'Antal artikler',
        'categories': 'Kategorier',
        'hours': 'Timer',
        'days_of_week': 'Ugedage',
        'weeks': 'Uger',
        'months': 'Måneder',
        'years': 'År',
        
                      
        'hourly': 'Timebaseret',
        'daily': 'Daglig',
        'weekly': 'Ugentlig',
        'monthly': 'Månedlig',
        'yearly': 'Årlig',
        'select_time_period': 'Vælg tidsperiode:',
        'time_period': 'Tidsperiode',
        
                   
        'monday': 'Mandag',
        'tuesday': 'Tirsdag',
        'wednesday': 'Onsdag',
        'thursday': 'Torsdag',
        'friday': 'Fredag',
        'saturday': 'Lørdag',
        'sunday': 'Søndag',
        
                     
        'january': 'Januar',
        'february': 'Februar',
        'march': 'Marts',
        'april': 'April',
        'may': 'Maj',
        'june': 'Juni',
        'july': 'Juli',
        'august': 'August',
        'september': 'September',
        'october': 'Oktober',
        'november': 'November',
        'december': 'December',
        
                     
        'week_1': 'Uge 1',
        'week_2': 'Uge 2',
        'week_3': 'Uge 3',
        'week_4': 'Uge 4',
        
                        
        'admin_credentials_message': 'Indtast venligst dine admin-legitimationsoplysninger for at få adgang til pipeline-kontroller.',
        'contact_admin_message': 'Kontakt systemadministratoren, hvis du har brug for adgangslegitimationsoplysninger.',
        
                   
        'ai_research_development': 'AI forskning og udvikling',
        'ai_ethics_regulations': 'AI etik og regulering',
        'ai_safety_governance': 'AI sikkerhed og styring',
        'ai_business_industry': 'AI forretning og industri',
        'ai_language_models_nlp': 'AI sprogmodeller og NLP',
        'ai_robotics_automation': 'AI robotik og automatisering',
        'ai_healthcare_medical': 'AI sundhed og medicin',
        'ai_education_training': 'AI uddannelse og træning',
        'ai_cybersecurity_privacy': 'AI cybersikkerhed og privatliv',
        'ai_computer_vision': 'AI computervision',
        'ai_data_science_analytics': 'AI datavidenskab og analyse',
        'ai_neural_networks_deep_learning': 'AI neurale netværk og deep learning',
        'ai_applications_deployment': 'AI applikationer og implementering',
        'ai_technology_infrastructure': 'AI teknologi og infrastruktur',
        
                           
        'advertising_commercial': 'Reklame og kommerciel',
        'journalism_news_media': 'Journalistik, nyheder og medier',
        'digital_media_content_creation': 'Digitale medier og indholdsproduktion',
        'strategic_communication_pr': 'Strategisk kommunikation og PR',
        'photography': 'Fotografi',
        'web_ux_design': 'Web- og UX-design',
        'film_tv_production': 'Film- og TV-produktion',
        'unknown': 'Ukendt',
        
                    
        'page': 'Side',
        'of': 'af',
        'previous': 'Forrige',
        'next': 'Næste',
        'showing': 'Viser',
        'to': 'til',
        'of_total': 'af i alt',
        
                    
        'journalism_news_media': 'Journalistik, nyheder og medier',
        'advertising_commercial': 'Reklame og kommerciel',
        'digital_media_content': 'Digitale medier og indholdsproduktion',
        'strategic_communication_pr': 'Strategisk kommunikation og PR',
        'photography': 'Fotografi',
        'web_ux_design': 'Web- og UX-design',
        'film_tv_production': 'Film- og TV-produktion',
        'other': 'Andet',
        
                 
        'filter_articles': 'Filtrer artikler',
        'all': 'Alle',
    }
}

def get_language():
    """Get current language from session state or default to Danish"""
    import streamlit as st
    if 'language' not in st.session_state:
        st.session_state.language = 'da'
    return st.session_state.language

def set_language(lang):
    """Set language in session state"""
    import streamlit as st
    st.session_state.language = lang

def t(key):
    """Translation function - get text for current language"""
    lang = get_language()
    return LANGUAGES[lang].get(key, key)

def translate_ai_topic(topic: str) -> str:
    """Translate AI topic from English to current language"""
    if not topic or topic.lower() in ['unknown', 'unknown topic', 'other', 'none', 'null']:
        return t('other')
    
                                                        
    topic_mapping = {
        'AI Research and Development': 'ai_research_development',
        'AI Ethics and Regulations': 'ai_ethics_regulations',
        'AI Safety and Governance': 'ai_safety_governance',
        'AI Business and Industry': 'ai_business_industry',
        'AI Language Models and NLP': 'ai_language_models_nlp',
        'AI Robotics and Automation': 'ai_robotics_automation',
        'AI Healthcare and Medical': 'ai_healthcare_medical',
        'AI Education and Training': 'ai_education_training',
        'AI Cybersecurity and Privacy': 'ai_cybersecurity_privacy',
        'AI Computer Vision': 'ai_computer_vision',
        'AI Data Science and Analytics': 'ai_data_science_analytics',
        'AI Neural Networks and Deep Learning': 'ai_neural_networks_deep_learning',
        'AI Applications and Deployment': 'ai_applications_deployment',
        'AI Technology and Infrastructure': 'ai_technology_infrastructure'
    }
    
    translation_key = topic_mapping.get(topic, 'other')
    return t(translation_key)

def translate_domain_category(category: str) -> str:
    """Translate domain category from English to current language"""
    if not category:
        return t('other')
    
                                                                
    category_mapping = {
        'advertising and commercial': 'advertising_commercial',
        'journalism, news and media': 'journalism_news_media',
        'digital media and content creation': 'digital_media_content_creation',
        'strategic communication and pr': 'strategic_communication_pr',
        'photography': 'photography',
        'web and ux design': 'web_ux_design',
        'film and tv production': 'film_tv_production',
        'other': 'other',
        'unknown': 'unknown'
    }
    
                                        
    normalized_category = category.lower()
    if normalized_category == 'unknown':
        normalized_category = 'other'
    translation_key = category_mapping.get(normalized_category, 'other')
    return t(translation_key)

def translate_day_name(day_name: str) -> str:
    """Translate day name from English to current language"""
    day_mapping = {
        'Monday': 'monday',
        'Tuesday': 'tuesday',
        'Wednesday': 'wednesday',
        'Thursday': 'thursday',
        'Friday': 'friday',
        'Saturday': 'saturday',
        'Sunday': 'sunday'
    }
    
    translation_key = day_mapping.get(day_name, day_name.lower())
    return t(translation_key)

def translate_month_name(month_name: str) -> str:
    """Translate month name from English to current language"""
    month_mapping = {
        'January': 'january',
        'February': 'february',
        'March': 'march',
        'April': 'april',
        'May': 'may',
        'June': 'june',
        'July': 'july',
        'August': 'august',
        'September': 'september',
        'October': 'october',
        'November': 'november',
        'December': 'december'
    }
    
    translation_key = month_mapping.get(month_name, month_name.lower())
    return t(translation_key)

def translate_week_label(week_label: str) -> str:
    """Translate week label from English to current language"""
    week_mapping = {
        'Week 1': 'week_1',
        'Week 2': 'week_2',
        'Week 3': 'week_3',
        'Week 4': 'week_4'
    }
    
    translation_key = week_mapping.get(week_label, week_label.lower().replace(' ', '_'))
    return t(translation_key)
