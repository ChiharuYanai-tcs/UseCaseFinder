from anthropic import Anthropic
from typing import List, Dict
from config import config

class AIAnalysisModule:
    """AI分析・ユースケース提案モジュール"""
    
    def __init__(self):
        self.client = Anthropic(api_key=config.claude_api_key)
    
    def _format_papers(self, papers: List[Dict]) -> str:
        """論文情報を整形"""
        if not papers:
            return "関連論文: なし"
        
        text = "## 関連論文\n\n"
        for i, paper in enumerate(papers[:5], 1):
            authors = ", ".join(paper.get('authors', ['Unknown'])[:3])
            text += f"{i}. **{paper['title']}** ({paper.get('year', 'N/A')})\n"
            text += f"   著者: {authors}\n"
            text += f"   被引用数: {paper.get('citations', 0)}\n"
            if paper.get('abstract') and paper['abstract'] != 'N/A':
                text += f"   概要: {paper['abstract'][:200]}...\n"
            text += "\n"
        return text
    
    def _format_news(self, articles: List[Dict]) -> str:
        """ニュース情報を整形"""
        if not articles:
            return "関連ニュース: なし"
        
        text = "## 最新ニュース・技術記事\n\n"
        for i, article in enumerate(articles[:5], 1):
            text += f"{i}. **{article['title']}**\n"
            text += f"   {article.get('summary', 'N/A')}\n"
            text += f"   公開日: {article.get('published', 'N/A')}\n\n"
        return text
    
    def generate_usecases(self, keyword: str, papers: List[Dict], news: List[Dict]) -> str:
        """ユースケースを生成"""
        print(f"AI分析中: {keyword}")
        
        # 情報を整形
        papers_text = self._format_papers(papers)
        news_text = self._format_news(news)
        
        # IEP (Inferential Exclusion Prompting) を活用したプロンプト
        prompt = f"""あなたはテクノロジービジネスコンサルタントです。
以下のキーワードに関する最新情報と論文を分析し、ビジネス層向けに革新的なユースケースを提案してください。

キーワード: {keyword}

{papers_text}

{news_text}

## タスク
上記の情報を基に、以下の形式で分析とユースケース提案を行ってください：

### 1. 技術トレンド分析
- 現在の技術的な動向と注目点
- 最近の研究や開発で明らかになった新しい可能性と課題

### 2. 実用可能なユースケース（3-5個）
各ユースケースについて：
- **タイトル**: 簡潔な名称
- **概要**: どのような課題を解決するか
- **実装の可能性**: 技術的実現性と必要なリソース
- **期待される効果**: ビジネス価値

### 3. 実装時の注意点
- 技術的な課題
- 考慮すべきリスク
- 必要な専門知識

**重要**: 提案は具体的で実装可能なものに限定してください。単なる理論的な可能性ではなく、
現在の技術レベルで実現可能なユースケースのみを提案してください。"""

        try:
            message = self.client.messages.create(
                model=config.claude_model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = message.content[0].text
            print("AI分析完了")
            return result
            
        except Exception as e:
            print(f"AI分析エラー: {e}")
            return f"エラーが発生しました: {e}"
