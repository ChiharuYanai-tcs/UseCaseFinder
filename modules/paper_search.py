import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from config import config

class PaperSearchModule:
    """論文検索モジュール（Semantic Scholar API使用）"""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.cache_file = os.path.join(config.cache_dir, "papers_cache.json")
        self.cache = self._load_cache()
    
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
    
    def search_papers(self, keyword: str) -> List[Dict]:
        """論文を検索"""
        # キャッシュチェック
        if self._is_cache_valid(keyword):
            print(f"論文検索: キャッシュから取得 ({keyword})")
            return self.cache[keyword]['data']
        
        print(f"論文検索中: {keyword}")
        
        # 日付フィルター（過去2年）
        cutoff_date = datetime.now() - timedelta(days=365 * config.date_range_years)
        year_filter = cutoff_date.year
        
        # Semantic Scholar API検索
        url = f"{self.base_url}/paper/search"
        params = {
            'query': keyword,
            'limit': config.max_papers,
            'fields': 'title,abstract,year,authors,citationCount,url,publicationDate',
            'year': f'{year_filter}-'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper in data.get('data', []):
                papers.append({
                    'title': paper.get('title', 'N/A'),
                    'abstract': paper.get('abstract', 'N/A'),
                    'year': paper.get('year', 'N/A'),
                    'authors': [a.get('name', 'Unknown') for a in paper.get('authors', [])[:3]],
                    'citations': paper.get('citationCount', 0),
                    'url': paper.get('url', ''),
                    'date': paper.get('publicationDate', 'N/A')
                })
            
            # キャッシュに保存
            self.cache[keyword] = {
                'timestamp': datetime.now().isoformat(),
                'data': papers
            }
            self._save_cache()
            
            print(f"論文 {len(papers)}件 取得完了")
            return papers
            
        except Exception as e:
            print(f"論文検索エラー: {e}")
            return []
