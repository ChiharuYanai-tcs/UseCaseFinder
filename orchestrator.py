from modules.paper_search import PaperSearchModule
from modules.news_search import NewsSearchModule
from modules.ai_analysis import AIAnalysisModule
from datetime import datetime
import os
from typing import Dict
from config import config

class UseCaseOrchestrator:
    """ユースケース提案エージェントのメインオーケストレーター"""
    
    def __init__(self):
        self.paper_search = PaperSearchModule()
        self.news_search = NewsSearchModule()
        self.ai_analysis = AIAnalysisModule()
    
    def process(self, keyword: str) -> Dict:
        """キーワードに基づいてユースケースを生成"""
        print(f"\n{'='*60}")
        print(f"ユースケース提案エージェント起動")
        print(f"キーワード: {keyword}")
        print(f"{'='*60}\n")
        
        # 1. 論文検索
        papers = self.paper_search.search_papers(keyword)
        
        # 2. ニュース検索
        news = self.news_search.search_news(keyword)
        
        # 3. AI分析・ユースケース生成
        analysis = self.ai_analysis.generate_usecases(keyword, papers, news)
        
        # 結果をまとめる
        result = {
            'keyword': keyword,
            'timestamp': datetime.now().isoformat(),
            'papers_count': len(papers),
            'news_count': len(news),
            'papers': papers,
            'news': news,
            'analysis': analysis
        }
        
        # 結果を保存
        self._save_result(keyword, result)
        
        return result
    
    def _save_result(self, keyword: str, result: Dict):
        """結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{keyword.replace(' ', '_')}_{timestamp}.md"
        filepath = os.path.join(config.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} - ユースケース提案レポート\n\n")
            f.write(f"生成日時: {result['timestamp']}\n\n")
            f.write(f"---\n\n")
            f.write(result['analysis'])
            f.write(f"\n\n---\n\n")
            f.write(f"## 参考情報\n\n")
            
            # 論文リスト
            f.write(f"### 関連論文 ({result['papers_count']}件)\n\n")
            if result['papers']:
                for paper in result['papers']:
                    title = paper.get('title', 'N/A')
                    url = paper.get('url', '')
                    year = paper.get('year', 'N/A')
                    citations = paper.get('citations', 0)
                    
                    if url:
                        f.write(f"- [{title}]({url}) ({year}, 引用数: {citations})\n")
                    else:
                        f.write(f"- {title} ({year}, 引用数: {citations})\n")
            else:
                f.write("- 該当する論文が見つかりませんでした\n")
            
            f.write("\n")
            
            # ニュース記事リスト
            f.write(f"### 関連ニュース記事 ({result['news_count']}件)\n\n")
            if result['news']:
                for article in result['news']:
                    title = article.get('title', 'N/A')
                    url = article.get('url', '')
                    published = article.get('published', 'N/A')
                    
                    if url:
                        f.write(f"- [{title}]({url}) ({published})\n")
                    else:
                        f.write(f"- {title} ({published})\n")
            else:
                f.write("- 該当するニュース記事が見つかりませんでした\n")
        
        print(f"\n結果を保存: {filepath}")
