"""
MAP-Elites用の評価関数
Claude APIを使用してユースケースを評価
"""

import json
import anthropic
from typing import Dict


EVALUATION_PROMPT = """あなたは製造業のDXとビジネスプロセスに精通した評価者です。以下のユースケースを評価し、スコアと特徴量を決定してください。

# 評価対象ユースケース
{usecase}

# 評価タスク
以下の3つの項目を評価してください：
1. ユースケース完成度スコア（0-100点）
2. ITドメインの分類（1-10の整数）
3. ビジネス機能の分類（1-10の整数）

# 評価基準

## 1. ユースケース完成度スコア [0-100点]
以下の2つの観点から総合的に評価してください：

### 記述の具体性 [0-50点]
- 課題や背景が明確に記述されているか（0-10点）
- 解決策や実装方法が具体的に示されているか（0-15点）
- 期待される効果や成果が定量的に記述されているか（0-10点）
- ステークホルダーや適用範囲が明確か（0-10点）
- 技術要素や手法が具体的に言及されているか（0-5点）

### 実現可能性 [0-50点]
- 現実的な技術で実装可能か（0-15点）
- コストや期間が現実的な範囲か（0-10点）
- 組織的な実行可能性があるか（0-10点）
- データの入手可能性や品質が現実的か（0-10点）
- リスクや制約条件が考慮されているか（0-5点）

## 2. ITドメインの分類 [1-10]
このユースケースが主に属するITドメインを1つ選択してください：
1. 画像検査・外観検品
2. 予知保全・設備診断
3. 生産計画最適化
4. 工程分析・作業改善
5. 品質予測・不良原因分析
6. エネルギー管理・省エネ最適化
7. 技術文書管理・ナレッジ継承
8. サプライヤー管理・調達最適化
9. 作業者安全監視
10. 製品トレーサビリティ・履歴管理

## 3. ビジネス機能の分類 [1-10]
このユースケースが主に対象とするビジネス機能を1つ選択してください：
1. 製品企画・市場調査
2. 設計・開発
3. 生産技術・工程設計
4. 生産計画・スケジューリング
5. 製造実行・現場管理
6. 品質管理・品質保証
7. 設備保全・メンテナンス
8. 資材・在庫管理
9. 物流・出荷管理
10. アフターサービス・保守

# 出力形式
以下のJSON形式で出力してください。JSON以外の説明文は含めないでください。

{{
  "score": <0-100の整数>,
  "it_domain": <1-10の整数>,
  "business_function": <1-10の整数>,
  "evaluation_notes": {{
    "specificity_score": <0-50の整数>,
    "feasibility_score": <0-50の整数>,
    "specificity_reasoning": "<具体性スコアの簡潔な理由>",
    "feasibility_reasoning": "<実現可能性スコアの簡潔な理由>",
    "it_domain_reasoning": "<ITドメイン分類の簡潔な理由>",
    "business_function_reasoning": "<ビジネス機能分類の簡潔な理由>"
  }}
}}"""


class UsecaseEvaluator:
    """ユースケースの評価を行うクラス"""
    
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 2000):
        """
        Args:
            api_key: Anthropic APIキー
            model: 使用するClaudeモデル
            max_tokens: 最大トークン数
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
    
    def evaluate(self, usecase: str) -> Dict:
        """
        ユースケースを評価
        
        Args:
            usecase: 評価対象のユースケース（マークダウン形式）
            
        Returns:
            評価結果の辞書 {score, it_domain, business_function, evaluation_notes}
        """
        # プロンプトを構築
        prompt = EVALUATION_PROMPT.format(usecase=usecase)
        
        try:
            # Claude APIを呼び出し
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # レスポンスからテキストを抽出
            response_text = message.content[0].text
            
            # JSONをパース
            # コードブロックで囲まれている場合は削除
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # 必須フィールドの検証
            required_fields = ['score', 'it_domain', 'business_function']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse evaluation result as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise RuntimeError(f"Failed to evaluate usecase: {str(e)}")


def create_evaluation_function(api_key: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 2000):
    """
    MAP-Elitesで使用する評価関数を作成
    
    Args:
        api_key: Anthropic APIキー
        model: 使用するClaudeモデル
        max_tokens: 最大トークン数
        
    Returns:
        評価関数 (ユースケース文字列 -> 評価結果辞書)
    """
    evaluator = UsecaseEvaluator(api_key=api_key, model=model, max_tokens=max_tokens)
    
    def evaluation_func(usecase: str) -> Dict:
        result = evaluator.evaluate(usecase)
        print(f"    Score: {result['score']}, IT Domain: {result['it_domain']}, Business Function: {result['business_function']}")
        return result
    
    return evaluation_func
