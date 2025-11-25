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


def load_initial_usecases(usecase_dir: Path) -> list[str]:
    """
    指定ディレクトリからマークダウンファイルを読み込み、初期ユースケースとして返す
    
    Args:
        usecase_dir: ユースケースマークダウンファイルが格納されたディレクトリ
        
    Returns:
        ユースケース文字列のリスト
    """
    if not usecase_dir.exists():
        raise FileNotFoundError(f"Usecase directory not found: {usecase_dir}")
    
    usecases = []
    md_files = sorted(usecase_dir.glob("*.md"))
    
    if not md_files:
        raise ValueError(f"No markdown files found in: {usecase_dir}")
    
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                usecases.append(content)
                print(f"  Loaded: {md_file.name}")
    
    return usecases


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
    
    # 初期ユースケースを読み込み
    print("\nLoading initial usecases...")
    usecase_dir = Path("./initial_usecases")
    try:
        initial_usecases = load_initial_usecases(usecase_dir)
        print(f"Loaded {len(initial_usecases)} usecase(s)")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        print(f"\nPlease create '{usecase_dir}' directory and add markdown files.")
        return
    
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
    map_elites.initialize_population(initial_usecases)
    
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
