"""
outputsディレクトリからユースケースを抽出する実行例
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from map_elites_algorithm.usecase_extractor import (
    extract_and_save_usecases,
    process_all_reports_in_directory
)


def main():
    """メイン実行関数"""
    # 環境変数の読み込み
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        return
    
    print("=" * 80)
    print("Usecase Extraction from Reports")
    print("=" * 80)
    
    # ディレクトリの設定
    reports_dir = Path("./outputs")
    output_dir = Path("./initial_usecases")
    
    # 方法1: 特定のレポートファイルから抽出
    # report_file = reports_dir / "Digital_Twins_20251114_193535.md"
    # if report_file.exists():
    #     saved_files = extract_and_save_usecases(
    #         report_filepath=report_file,
    #         output_dir=output_dir,
    #         api_key=api_key,
    #         prefix="digital_twins"
    #     )
    #     print(f"\nSaved {len(saved_files)} usecase file(s)")
    
    # 方法2: outputsディレクトリ内のすべてのレポートを処理
    try:
        results = process_all_reports_in_directory(
            reports_dir=reports_dir,
            output_dir=output_dir,
            api_key=api_key
        )
        
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        total_files = 0
        for report_name, saved_files in results.items():
            print(f"\n{report_name}:")
            print(f"  Extracted {len(saved_files)} usecase(s)")
            total_files += len(saved_files)
        
        print(f"\nTotal: {total_files} usecase file(s) created")
        print(f"Output directory: {output_dir}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
