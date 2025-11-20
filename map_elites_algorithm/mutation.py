"""
MAP-Elites用の変異関数
Claude APIを使用して2種類の変異戦略を実装
"""

import random
from typing import Optional
import anthropic


# 変異プロンプト1: Criticize Question
CRITICIZE_QUESTION_PROMPT = """あなたは批判的思考に優れたビジネスアナリストです。以下のユースケースを分析し、新しいユースケースを生成してください。

# 制約条件
- 元のユースケースが解決しようとしている本質的な問いを特定してください
- その問いに対して批判的な視点を提示してください（前提の妥当性、スコープの適切性、見落とされている側面など）
- 批判から導かれる新しい問いを立ててください
- 新しい問いに基づいた代替的なユースケースを生成してください
- 出力は元のユースケースと同じマークダウン形式で記述してください

# 入力ユースケース
{original_usecase}

# 分析と出力の手順
## ステップ1: 本質的な問いの特定
元のユースケースが暗黙的に答えようとしている問いは何か？

## ステップ2: 批判的検討
- この問いの前提条件は妥当か？
- 問いのスコープは適切か（狭すぎる/広すぎる）？
- 見落とされているステークホルダーや側面はないか？
- 別の視点から見た場合、どのような問題が浮かび上がるか？

## ステップ3: 新しい問いの定式化
批判的検討から導かれる、より本質的または異なる角度からの問いを立ててください。

## ステップ4: 新しいユースケースの生成
新しい問いに基づいて、代替的なユースケースを生成してください。元のITドメインまたはビジネス機能から少しずれた領域を探索することを推奨します。

# 出力形式
新しいユースケースのみをマークダウン形式で出力してください。分析過程は出力に含めないでください。"""


# 変異プロンプト2: Domain/Function Transfer
DOMAIN_FUNCTION_TRANSFER_PROMPT = """あなたは業界横断的な知識を持つビジネスコンサルタントです。以下のユースケースを分析し、異なる領域に転用した新しいユースケースを生成してください。

# 制約条件
- 元のユースケースが属するITドメインとビジネス機能を特定してください
- そのユースケースの核となる価値やメカニズムを抽出してください
- 抽出した価値やメカニズムを、異なるITドメインまたは異なるビジネス機能に転用してください
- 転用先では、元の領域とは異なる具体的な課題や文脈に適応させてください
- 出力は元のユースケースと同じマークダウン形式で記述してください

# 入力ユースケース
{original_usecase}

# ITドメインの候補
1:画像検査・外観検品, 2:予知保全・設備診断, 3:生産計画最適化, 4:工程分析・作業改善, 5:品質予測・不良原因分析, 6:エネルギー管理・省エネ最適化, 7:技術文書管理・ナレッジ継承, 8:サプライヤー管理・調達最適化, 9:作業者安全監視, 10:製品トレーサビリティ・履歴管理

# ビジネス機能の候補
1:製品企画・市場調査, 2:設計・開発, 3:生産技術・工程設計, 4:生産計画・スケジューリング, 5:製造実行・現場管理, 6:品質管理・品質保証, 7:設備保全・メンテナンス, 8:資材・在庫管理, 9:物流・出荷管理, 10:アフターサービス・保守

# 分析と出力の手順
## ステップ1: 現在の特徴量の特定
- このユースケースが属するITドメインは何か？
- このユースケースが対象とするビジネス機能は何か？

## ステップ2: 核となる価値の抽出
- このユースケースが提供する本質的な価値は何か？（例: リアルタイム監視、予測精度向上、作業効率化、リスク低減など）
- その価値を実現している具体的なメカニズムや技術要素は何か？

## ステップ3: 転用先の選択
以下のいずれかのパターンで転用先を選んでください：
- パターンA: ITドメインを変更し、ビジネス機能は同じまたは隣接する領域にする
- パターンB: ビジネス機能を変更し、ITドメインは同じまたは隣接する領域にする
- パターンC: ITドメインとビジネス機能の両方を変更する（この場合、変化は控えめにして実現可能性を保つ）

## ステップ4: 転用先での具体化
- 選択した転用先での具体的な課題や文脈を設定してください
- 抽出した価値やメカニズムが、その新しい文脈でどのように機能するかを考えてください
- 転用先特有の制約条件や要件を反映してください

## ステップ5: 新しいユースケースの生成
転用先の文脈に適応させた新しいユースケースを生成してください。元のユースケースの本質的な価値は保ちつつ、新しい領域での具体的な適用方法を示してください。

# 出力形式
新しいユースケースのみをマークダウン形式で出力してください。分析過程は出力に含めないでください。"""


class UsecaseMutator:
    """ユースケースの変異を行うクラス"""
    
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 4000):
        """
        Args:
            api_key: Anthropic APIキー
            model: 使用するClaudeモデル
            max_tokens: 最大トークン数
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        
        # 変異戦略のリスト
        self.mutation_strategies = [
            ("Criticize Question", CRITICIZE_QUESTION_PROMPT),
            ("Domain/Function Transfer", DOMAIN_FUNCTION_TRANSFER_PROMPT)
        ]
    
    def mutate(self, original_usecase: str) -> tuple[str, str]:
        """
        ユースケースを変異させる
        
        Args:
            original_usecase: 元のユースケース（マークダウン形式）
            
        Returns:
            (変異後のユースケース, 使用した戦略名)
        """
        # ランダムに変異戦略を選択（50%ずつ）
        strategy_name, prompt_template = random.choice(self.mutation_strategies)
        
        # プロンプトを構築
        prompt = prompt_template.format(original_usecase=original_usecase)
        
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
            mutated_usecase = message.content[0].text
            
            return mutated_usecase, strategy_name
            
        except Exception as e:
            raise RuntimeError(f"Failed to mutate usecase using {strategy_name}: {str(e)}")
    
    def set_model(self, model: str) -> None:
        """使用するモデルを変更"""
        self.model = model
    
    def set_max_tokens(self, max_tokens: int) -> None:
        """最大トークン数を変更"""
        self.max_tokens = max_tokens


def create_mutation_function(api_key: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 4000):
    """
    MAP-Elitesで使用する変異関数を作成
    
    Args:
        api_key: Anthropic APIキー
        model: 使用するClaudeモデル
        max_tokens: 最大トークン数
        
    Returns:
        変異関数 (ユースケース文字列 -> 変異後ユースケース文字列)
    """
    mutator = UsecaseMutator(api_key=api_key, model=model, max_tokens=max_tokens)
    
    def mutation_func(usecase: str) -> str:
        mutated_usecase, strategy = mutator.mutate(usecase)
        print(f"    Applied mutation strategy: {strategy}")
        return mutated_usecase
    
    return mutation_func
