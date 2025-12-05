"""
outputsディレクトリのマークダウンファイルから個別のユースケースを抽出し、
initial_usecases形式のファイルとして保存するモジュール
"""

import json
import re
from pathlib import Path
from typing import List, Dict
import anthropic


def extract_usecases_from_report(
    report_filepath: Path,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4000
) -> List[Dict[str, str]]:
    """
    レポートファイルからユースケースを抽出する
    
    Args:
        report_filepath: レポートマークダウンファイルのパス
        api_key: Anthropic API key
        model: 使用するClaudeモデル
        max_tokens: 最大トークン数
        
    Returns:
        ユースケース情報のリスト [{"title": "...", "content": "..."}]
    """
    # レポートファイルを読み込み
    with open(report_filepath, "r", encoding="utf-8") as f:
        report_content = f.read()
    
    # Claude APIでユースケースを抽出
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""以下のレポートファイルには複数のユースケースが記載されています。
各ユースケースを抽出し、以下の形式のマークダウンファイルとして出力してください。

# 期待する出力形式（各ユースケースごと）:
```markdown
---
generation: 0
score: 0
---

# [ユースケースのタイトル]

## 背景・課題
[課題の説明]

## 解決策
[解決策の説明]

## 期待効果
[期待効果の箇条書き]

## 技術要素
[必要な技術要素の箇条書き]
```

# 抽出ルール:
1. レポート内の「ユースケース」セクションから個別のユースケースを特定してください
2. 各ユースケースについて、背景・課題、解決策、期待効果、技術要素を抽出してください
3. 表形式のデータは箇条書きに変換してください
4. 各ユースケースは独立したマークダウン文書として出力してください
5. ファイルの先頭には必ず以下のFront Matterヘッダーを含めてください：
   ---
   generation: 0
   score: 50
   ---
6. JSONで返してください: {{"usecases": [{{"title": "タイトル", "content": "マークダウン本文(Front Matter含む)"}}]}}

# レポート内容:
{report_content}"""

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # JSON部分を抽出
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
        return result.get("usecases", [])
    
    # JSONが見つからない場合は空リストを返す
    print("Warning: Could not extract JSON from Claude response")
    return []


def save_usecases_to_files(
    usecases: List[Dict[str, str]],
    output_dir: Path,
    prefix: str = "usecase"
) -> List[Path]:
    """
    抽出したユースケースを個別ファイルとして保存
    
    Args:
        usecases: ユースケース情報のリスト
        output_dir: 出力先ディレクトリ
        prefix: ファイル名のプレフィックス
        
    Returns:
        保存したファイルパスのリスト
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    
    for i, usecase in enumerate(usecases, 1):
        # ファイル名を生成（タイトルから安全なファイル名を作成）
        title = usecase.get("title", f"usecase_{i}")
        # ファイル名に使えない文字を除去
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        safe_title = safe_title.replace(' ', '_')[:50]  # 長すぎる場合は切り詰め
        
        filename = f"{prefix}_{i:02d}_{safe_title}.md"
        filepath = output_dir / filename
        
        # ファイルに書き込み
        content = usecase.get("content", "")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        saved_files.append(filepath)
        print(f"  Saved: {filename}")
    
    return saved_files


def extract_and_save_usecases(
    report_filepath: Path,
    output_dir: Path,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4000,
    prefix: str = "usecase"
) -> List[Path]:
    """
    レポートファイルからユースケースを抽出して保存する（統合関数）
    
    Args:
        report_filepath: レポートマークダウンファイルのパス
        output_dir: 出力先ディレクトリ
        api_key: Anthropic API key
        model: 使用するClaudeモデル
        max_tokens: 最大トークン数
        prefix: ファイル名のプレフィックス
        
    Returns:
        保存したファイルパスのリスト
    """
    print(f"\nExtracting usecases from: {report_filepath.name}")
    
    # ユースケースを抽出
    usecases = extract_usecases_from_report(
        report_filepath=report_filepath,
        api_key=api_key,
        model=model,
        max_tokens=max_tokens
    )
    
    if not usecases:
        print("Warning: No usecases extracted")
        return []
    
    print(f"Extracted {len(usecases)} usecase(s)")
    
    # ファイルに保存
    saved_files = save_usecases_to_files(
        usecases=usecases,
        output_dir=output_dir,
        prefix=prefix
    )
    
    return saved_files


def process_all_reports_in_directory(
    reports_dir: Path,
    output_dir: Path,
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4000
) -> Dict[str, List[Path]]:
    """
    outputsディレクトリ内のすべてのレポートファイルを処理
    
    Args:
        reports_dir: レポートファイルがあるディレクトリ
        output_dir: 出力先ディレクトリ
        api_key: Anthropic API key
        model: 使用するClaudeモデル
        max_tokens: 最大トークン数
        
    Returns:
        {レポートファイル名: [保存したファイルパスのリスト]}の辞書
    """
    if not reports_dir.exists():
        raise FileNotFoundError(f"Reports directory not found: {reports_dir}")
    
    report_files = list(reports_dir.glob("*.md"))
    
    if not report_files:
        print(f"No markdown files found in: {reports_dir}")
        return {}
    
    print(f"Found {len(report_files)} report file(s)")
    
    results = {}
    
    for report_file in report_files:
        # レポートファイル名から適切なプレフィックスを生成
        prefix = report_file.stem  # 拡張子を除いたファイル名
        
        saved_files = extract_and_save_usecases(
            report_filepath=report_file,
            output_dir=output_dir,
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            prefix=prefix
        )
        
        results[report_file.name] = saved_files
    
    return results
