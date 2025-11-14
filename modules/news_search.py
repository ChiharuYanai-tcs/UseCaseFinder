import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict
from datetime import datetime, timedelta
import json
import os
from config import config

class NewsSearchModule:
    """ニュース・技術記事検索モジュール"""
    
    def __init__(self):
        self.cache_file = os.path.join(config.cache_dir, "news_cache.json")
        self.cache = self._load_cache()
        self.tech_rss_feeds = [
            "https://news.ycombinator.com/rss",
            "https://www.reddit.com/r/technology/.rss",
        ]
    
    def _load_cache(self) -> Dict:
        """キャッシュを読み込む"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """キャッシュを保存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _is_cache_valid(self, keyword: str) -> bool:
        """キャッシュが有効か確認"""
        if not config.enable_cache or keyword not in self.cache:
            return False
        
        cache_time = datetime.fromisoformat(self.cache[keyword]['timestamp'])
        expiry = timedelta(hours=config.cache_expiry_hours)
        return datetime.now() - cache_time < expiry
    
    def search_news(self, keyword: str) -> List[Dict]:
        """ニュース・技術記事を検索"""
        # キャッシュチェック
        if self._is_cache_valid(keyword):
            print(f"ニュース検索: キャッシュから取得 ({keyword})")
            return self.cache[keyword]['data']
        
        print(f"ニュース検索中: {keyword}")
        
        articles = []
        
        # RSSフィードから取得
        for feed_url in self.tech_rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:config.max_news_results]:
                    if keyword.lower() in entry.get('title', '').lower() or \
                       keyword.lower() in entry.get('summary', '').lower():
                        articles.append({
                            'title': entry.get('title', 'N/A'),
                            'summary': entry.get('summary', 'N/A')[:300],
                            'url': entry.get('link', ''),
                            'published': entry.get('published', 'N/A'),
                            'source': feed_url
                        })
            except Exception as e:
                print(f"RSS取得エラー ({feed_url}): {e}")
        
        # 重複除去
        seen_titles = set()
        unique_articles = []
        for article in articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
        
        # キャッシュに保存
        self.cache[keyword] = {
            'timestamp': datetime.now().isoformat(),
            'data': unique_articles[:config.max_news_results]
        }
        self._save_cache()
        
        print(f"ニュース {len(unique_articles[:config.max_news_results])}件 取得完了")
        return unique_articles[:config.max_news_results]
