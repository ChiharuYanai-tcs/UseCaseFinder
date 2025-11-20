"""
MAP-Elitesアルゴリズムの実行例
3世代だけ実行して結果を可視化
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from map_elites_algorithm.map_elites import MAPElites
from map_elites_algorithm.mutation import create_mutation_function
from map_elites_algorithm.evaluation import create_evaluation_function


# 初期ユースケースのサンプル
INITIAL_USECASES = [
    """# AI画像検査による製品外観検品の自動化

## 背景・課題
製造ラインでの製品外観検品は、現在人の目視に依存しており、検査員の疲労や習熟度によって検査精度にばらつきが生じている。特に微細な傷や色ムラの検出が困難で、不良品の見逃しや過検出が発生している。

## 解決策
ディープラーニングを用いた画像検査システムを導入し、製品の外観検査を自動化する。高解像度カメラで撮影した製品画像を、事前学習済みのCNNモデルで解析し、傷・汚れ・色ムラなどの不良を自動検出する。

## 期待効果
- 検査精度の向上：不良検出率を95%以上に向上
- 検査時間の短縮：1製品あたりの検査時間を30秒から5秒に削減
- 人的コストの削減：検査員を2名から1名に削減可能

## 技術要素
- 画像認識AI（CNN）
- 高解像度産業用カメラ
- エッジコンピューティング""",

    """# 設備故障予知による予防保全の最適化

## 背景・課題
製造設備の突発的な故障により、生産ラインの停止が発生し、大きな損失が生じている。現在は定期メンテナンスを実施しているが、故障の予兆を事前に検知できていない。

## 解決策
センサーデータとAIを活用した予知保全システムを構築する。設備の振動・温度・電流値などをリアルタイムで収集し、機械学習モデルで異常の予兆を検知する。

## 期待効果
- 突発故障の削減：年間故障件数を50%削減
- ダウンタイムの削減：計画外停止時間を70%削減
- メンテナンスコストの最適化：過剰保全を防止し、コストを30%削減

## 技術要素
- IoTセンサー
- 時系列データ解析
- 異常検知AI（Isolation Forest、LSTM）""",

    """# 需要予測AIによる生産計画の最適化

## 背景・課題
市場需要の変動が大きく、過剰在庫や欠品が頻繁に発生している。現在の生産計画は過去実績ベースで作成されており、市場トレンドや季節変動に対応できていない。

## 解決策
機械学習を用いた需要予測システムを導入し、過去の販売データ、季節要因、市場トレンドなどを分析して高精度な需要予測を実現する。予測結果に基づいて最適な生産計画を自動生成する。

## 期待効果
- 予測精度の向上：需要予測誤差を±10%以内に改善
- 在庫削減：適正在庫レベルを維持し、在庫コストを20%削減
- 欠品率の低減：欠品発生率を50%削減

## 技術要素
- 時系列予測モデル（ARIMA、Prophet）
- 機械学習（Random Forest、XGBoost）
- 最適化アルゴリズム"""
]


def main():
    """メイン実行関数"""
    # 環境変数の読み込み
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key:")
        print("ANTHROPIC_API_KEY=your-api-key-here")
        return
    
    print("=" * 80)
    print("MAP-Elites Algorithm - Example Run (3 Generations)")
    print("=" * 80)
    
    # 変異関数と評価関数を作成
    print("\nInitializing mutation and evaluation functions...")
    mutate_func = create_mutation_function(
        api_key=api_key,
        model="claude-haiku-4-5-20251001",
        max_tokens=4000
    )
    
    evaluate_func = create_evaluation_function(
        api_key=api_key,
        model="claude-haiku-4-5-20251001",
        max_tokens=2000
    )
    
    # MAP-Elitesを初期化
    print("\nInitializing MAP-Elites...")
    archive_dir = Path("./archive")
    map_elites = MAPElites(
        archive_dir=archive_dir,
        keyword="example_3gen",
        grid_size=(10, 10),
        population_size=5,  # 3世代で素早く実行するため少なめに設定
        max_generations=3,   # 3世代のみ実行
        evaluate_func=evaluate_func,
        mutate_func=mutate_func
    )
    
    print(f"Archive directory: {map_elites.run_dir}")
    
    # 初期個体群を設定
    print("\n" + "=" * 80)
    print("Phase 1: Initializing Population")
    print("=" * 80)
    map_elites.initialize_population(INITIAL_USECASES)
    
    # テキストベースの可視化
    map_elites.visualize_archive()
    
    # 進化を実行
    print("\n" + "=" * 80)
    print("Phase 2: Evolution")
    print("=" * 80)
    map_elites.evolve()
    
    # 最終的なテキストベースの可視化
    print("\n" + "=" * 80)
    print("Phase 3: Final Results")
    print("=" * 80)
    map_elites.visualize_archive()
    
    # レポートを保存
    report_path = map_elites.save_final_report()
    
    # ヒートマップで可視化
    print("\n" + "=" * 80)
    print("Phase 4: Creating Visualizations")
    print("=" * 80)
    map_elites.visualize_all_heatmaps()
    
    # 上位個体を表示
    print("\n" + "=" * 80)
    print("Top 5 Individuals by Score")
    print("=" * 80)
    top_individuals = map_elites.get_best_individuals(top_k=5)
    for i, ind in enumerate(top_individuals, 1):
        print(f"\n{i}. Score: {ind.score:.1f}, IT Domain: {ind.it_domain}, Business Function: {ind.business_function}")
        print(f"   Generation: {ind.generation}")
        if ind.filepath:
            print(f"   File: {ind.filepath.relative_to(map_elites.run_dir)}")
    
    print("\n" + "=" * 80)
    print("Execution completed successfully!")
    print("=" * 80)
    print(f"\nResults saved to: {map_elites.run_dir}")
    print(f"  - Archive files: {map_elites.run_dir}/generation_*/")
    print(f"  - Visualizations: {map_elites.run_dir}/visualizations/")
    print(f"  - Report: {report_path}")


if __name__ == "__main__":
    main()
