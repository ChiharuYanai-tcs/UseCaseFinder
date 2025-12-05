"""
MAP-Elites用の評価関数
Claude APIを使用してユースケースを評価
"""

import json
import anthropic
from typing import Dict


# 評価基準となる参照用ユースケース例
REFERENCE_USECASE = """# 画像AIによる溶接部外観検査の自動化

## 背景・課題
製造ラインにおける溶接部の目視検査は、熟練検査員の経験と勘に依存しており、以下の課題がある：
- 検査員の習熟に3-5年かかり、人材育成コストが高い
- 疲労による見落としで不良品流出リスクがある（不良流出率：0.3%）
- 24時間稼働ラインで3交代の人員確保が困難

## 解決策
ディープラーニングによる画像検査システムを導入し、溶接部の良否判定を自動化する：
- 高解像度カメラで溶接部を撮影（1200万画素、0.1mm精度）
- CNNモデルで欠陥パターンを学習（過去3年分・10万枚のデータセット使用）
- 判定結果をMESに自動連携し、不良品を後工程に流さない

## 期待効果
- 検査精度の向上：不良流出率を0.3%から0.05%に削減
- 検査時間の短縮：1個あたり30秒から3秒に削減（90%削減）
- 人件費削減：年間検査員3名分の人件費約2,400万円を削減
- 投資回収期間：約1.5年

## 適用範囲・ステークホルダー
- 対象：自動車部品製造ラインの溶接工程（月産5万個）
- 関係部門：製造部、品質保証部、生産技術部、IT部門"""

REFERENCE_EVALUATION = {
    "score": 50,
    "it_domain": 1,
    "business_function": 6,
    "evaluation_notes": {
        "specificity_score": 43,
        "feasibility_score": 42,
        "specificity_reasoning": "課題が定量的に記述され、解決策の技術要素（CNN、画像精度）が具体的。効果も数値で明示されている。",
        "feasibility_reasoning": "既存技術で実装可能。投資対効果が明確で、データセットも現実的。組織横断的な実行体制も示されている。",
        "it_domain_reasoning": "溶接部の外観検査を画像AIで自動化するため、画像検査・外観検品に分類。",
        "business_function_reasoning": "製造ラインの検査工程を対象とし、不良品流出防止が目的のため、品質管理・品質保証に分類。"
    }
}


EVALUATION_PROMPT = """あなたは製造業のDXとビジネスプロセスに精通した評価者です。以下のユースケースを評価し、スコアと特徴量を決定してください。

# 参照用ユースケース例（評価基準として利用）
以下の例を基準として、評価対象のユースケースを相対的に評価してください。

{reference_usecase}

**参照例の評価結果：**
- 完成度スコア：{reference_score}点
- 具体性：{reference_specificity}点 - {reference_specificity_reasoning}
- 実現可能性：{reference_feasibility}点 - {reference_feasibility_reasoning}

---

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
        # プロンプトを構築（参照例を含める）
        prompt = EVALUATION_PROMPT.format(
            reference_usecase=REFERENCE_USECASE,
            reference_score=REFERENCE_EVALUATION["score"],
            reference_specificity=REFERENCE_EVALUATION["evaluation_notes"]["specificity_score"],
            reference_feasibility=REFERENCE_EVALUATION["evaluation_notes"]["feasibility_score"],
            reference_specificity_reasoning=REFERENCE_EVALUATION["evaluation_notes"]["specificity_reasoning"],
            reference_feasibility_reasoning=REFERENCE_EVALUATION["evaluation_notes"]["feasibility_reasoning"],
            usecase=usecase
        )
        
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
