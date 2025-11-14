import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# .envファイルを読み込む（このモジュールがインポートされた時点で実行）
load_dotenv()

@dataclass
class Config:
    """アプリケーション設定"""
    # APIキー
    claude_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # 検索パラメータ
    max_papers: int = 10
    max_news_results: int = 10
    date_range_years: int = 2
    
    # キャッシュ設定
    cache_dir: str = "./cache"
    enable_cache: bool = True
    cache_expiry_hours: int = 24
    
    # 出力設定
    output_dir: str = "./outputs"
    output_format: str = "markdown"  # markdown, json, text
    
    # Claude設定
    claude_model: str = "claude-haiku-4-5-20251001"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    def __post_init__(self):
        """ディレクトリ作成"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

config = Config()
