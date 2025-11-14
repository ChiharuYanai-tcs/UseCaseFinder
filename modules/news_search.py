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
        keyword_lower = keyword.lower()
        
        # RSSフィードから取得
        for feed_url in self.tech_rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                # まず全てのエントリを取得し、関連度でスコアリング
                scored_entries = []
                for entry in feed.entries:
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()
                    
                    # 関連度スコア計算
                    score = 0
                    if keyword_lower in title:
                        score += 10
                    if keyword_lower in summary:
                        score += 5
                    
                    # キーワードの部分一致もチェック
                    words = keyword_lower.split()
                    for word in words:
                        if len(word) > 2:  # 短すぎる単語は除外
                            if word in title:
                                score += 3
                            if word in summary:
                                score += 1
                    
                    if score > 0:
                        scored_entries.append((score, entry))
                
                # スコアでソートして上位を取得
                scored_entries.sort(reverse=True, key=lambda x: x[0])
                
                for score, entry in scored_entries[:config.max_news_results]:
                    articles.append({
                        'title': entry.get('title', 'N/A'),
                        'summary': entry.get('summary', 'N/A')[:300],
                        'url': entry.get('link', ''),
                        'published': entry.get('published', 'N/A'),
                        'source': feed_url,
                        'relevance_score': score
                    })
            except Exception as e:
                print(f"RSS取得エラー ({feed_url}): {e}")
        
        # スコアでソート
        articles.sort(reverse=True, key=lambda x: x.get('relevance_score', 0))
        
        # 重複除去
        seen_titles = set()
        unique_articles = []
        for article in articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                # relevance_scoreは内部用なので削除
                article_copy = {k: v for k, v in article.items() if k != 'relevance_score'}
                unique_articles.append(article_copy)
        
        result = unique_articles[:config.max_news_results]
        
        # キャッシュに保存
        self.cache[keyword] = {
            'timestamp': datetime.now().isoformat(),
            'data': result
        }
        self._save_cache()
        
        print(f"ニュース {len(result)}件 取得完了")
        return result
