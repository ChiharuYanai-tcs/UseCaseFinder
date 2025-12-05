"""
MAP-Elites アルゴリズムの実装
製造業DXユースケースの進化的生成を行う

使用例:
    from map_elites_algorithm.mutation import create_mutation_function
    from map_elites_algorithm.evaluation import create_evaluation_function
    
    # 変異関数と評価関数を作成
    mutate_func = create_mutation_function(api_key="your-api-key")
    evaluate_func = create_evaluation_function(api_key="your-api-key")
    
    # MAP-Elitesを初期化
    map_elites = MAPElites(
        archive_dir=Path("./archive"),
        keyword="manufacturing_dx",
        evaluate_func=evaluate_func,
        mutate_func=mutate_func
    )
    
    # 初期個体群を設定して進化を実行
    map_elites.initialize_population(initial_usecases)
    map_elites.evolve()
    map_elites.save_final_report()
    
    # 可視化
    map_elites.visualize_heatmap()
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime


@dataclass
class Individual:
    """個体を表すデータクラス"""
    content: str  # ユースケースの本文（マークダウン形式）
    score: float  # 完成度スコア (0-100)
    it_domain: int  # ITドメイン (1-10)
    business_function: int  # ビジネス機能 (1-10)
    filepath: Optional[Path] = None  # 保存先ファイルパス
    generation: int = 0  # 生成された世代
    evaluation_notes: Optional[Dict] = None  # 評価詳細


class MAPElites:
    """MAP-Elitesアルゴリズムの実装クラス"""
    
    def __init__(
        self,
        archive_dir: Path,
        keyword: str,
        grid_size: Tuple[int, int] = (10, 10),
        population_size: int = 10,
        max_generations: int = 100,
        evaluate_func: Optional[Callable[[str], Dict]] = None,
        mutate_func: Optional[Callable[[str], str]] = None
    ):
        """
        Args:
            archive_dir: アーカイブの基底ディレクトリ
            keyword: 実行キーワード
            grid_size: グリッドサイズ (ITドメイン数, ビジネス機能数)
            population_size: 1世代あたりの個体数
            max_generations: 最大世代数
            evaluate_func: 評価関数 (ユースケース文字列 -> 評価結果辞書)
            mutate_func: 変異関数 (ユースケース文字列 -> 変異後ユースケース文字列)
        """
        self.grid_size = grid_size
        self.population_size = population_size
        self.max_generations = max_generations
        self.evaluate_func = evaluate_func
        self.mutate_func = mutate_func
        
        # アーカイブディレクトリの設定
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = archive_dir / f"{timestamp}_{keyword}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # グリッドの初期化 (ITドメイン x ビジネス機能)
        self.archive: Dict[Tuple[int, int], Individual] = {}
        
        # 統計情報
        self.stats = {
            "generations": [],
            "archive_size": [],
            "max_score": [],
            "mean_score": []
        }
    
    def _get_niche(self, individual: Individual) -> Tuple[int, int]:
        """個体が属するニッチ（グリッドセル）を取得"""
        return (individual.it_domain, individual.business_function)
    
    def _add_to_archive(self, individual: Individual) -> bool:
        """
        個体をアーカイブに追加
        
        Args:
            individual: 追加する個体
            
        Returns:
            追加された場合True、既存個体の方が優れていた場合False
        """
        niche = self._get_niche(individual)
        
        # ニッチが空の場合、または既存個体よりスコアが高い場合
        if niche not in self.archive or individual.score > self.archive[niche].score:
            self.archive[niche] = individual
            return True
        
        return False
    
    def _save_individual(self, individual: Individual, generation: int) -> Path:
        """個体をファイルに保存"""
        gen_dir = self.run_dir / f"generation_{generation:03d}"
        gen_dir.mkdir(exist_ok=True)
        
        # ファイル名の生成
        niche = self._get_niche(individual)
        filename = f"itd{niche[0]:02d}_bf{niche[1]:02d}_score{int(individual.score):03d}.md"
        filepath = gen_dir / filename
        
        # メタデータを含めて保存
        metadata = f"""---
generation: {generation}
score: {individual.score}
it_domain: {individual.it_domain}
business_function: {individual.business_function}
created_at: {datetime.now().isoformat()}
---

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(metadata)
            f.write(individual.content)
        
        individual.filepath = filepath
        return filepath
    
    def _load_individual(self, filepath: Path) -> Individual:
        """ファイルから個体を読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # メタデータとコンテンツを分離
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata_str = parts[1]
                usecase_content = parts[2].strip()
                
                # メタデータをパース
                metadata = {}
                for line in metadata_str.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                
                return Individual(
                    content=usecase_content,
                    score=float(metadata.get('score', 0)),
                    it_domain=int(metadata.get('it_domain', 1)),
                    business_function=int(metadata.get('business_function', 1)),
                    filepath=filepath,
                    generation=int(metadata.get('generation', 0))
                )
        
        # メタデータがない場合は評価が必要
        raise ValueError(f"Invalid file format: {filepath}")
    
    def initialize_population(self, initial_usecases: List[str]) -> None:
        """
        初期個体群を評価してアーカイブに配置
        
        Args:
            initial_usecases: 初期ユースケースのリスト
        """
        if self.evaluate_func is None:
            raise ValueError("evaluate_func must be provided")
        
        print(f"Initializing population with {len(initial_usecases)} individuals...")
        
        for i, usecase_content in enumerate(initial_usecases):
            print(f"  Evaluating initial individual {i+1}/{len(initial_usecases)}...")
            
            # 評価
            eval_result = self.evaluate_func(usecase_content)
            
            # 個体を作成
            individual = Individual(
                content=usecase_content,
                score=eval_result['score'],
                it_domain=eval_result['it_domain'],
                business_function=eval_result['business_function'],
                generation=0,
                evaluation_notes=eval_result.get('evaluation_notes')
            )
            
            # アーカイブに追加
            if self._add_to_archive(individual):
                self._save_individual(individual, 0)
        
        print(f"Initial archive size: {len(self.archive)}")
        self._update_stats(0)
    
    def _select_random_individuals(self, n: int) -> List[Individual]:
        """アーカイブからランダムにn個の個体を選択"""
        if len(self.archive) == 0:
            return []
        
        return random.sample(list(self.archive.values()), min(n, len(self.archive)))
    
    def _mutate_individual(self, individual: Individual) -> str:
        """個体を変異させる"""
        if self.mutate_func is None:
            raise ValueError("mutate_func must be provided")
        
        return self.mutate_func(individual.content)
    
    def _update_stats(self, generation: int) -> None:
        """統計情報を更新"""
        if len(self.archive) == 0:
            return
        
        scores = [ind.score for ind in self.archive.values()]
        
        self.stats["generations"].append(generation)
        self.stats["archive_size"].append(len(self.archive))
        self.stats["max_score"].append(max(scores))
        self.stats["mean_score"].append(sum(scores) / len(scores))
    
    def evolve(self) -> None:
        """進化プロセスを実行"""
        if self.evaluate_func is None or self.mutate_func is None:
            raise ValueError("evaluate_func and mutate_func must be provided")
        
        print(f"\nStarting evolution for {self.max_generations} generations...")
        
        for generation in range(1, self.max_generations + 1):
            print(f"\n=== Generation {generation}/{self.max_generations} ===")
            
            # ランダムに個体を選択
            selected = self._select_random_individuals(self.population_size)
            print(f"Selected {len(selected)} individuals for mutation")
            
            # 各個体を変異
            new_individuals = []
            for i, parent in enumerate(selected):
                print(f"  Mutating individual {i+1}/{len(selected)}...")
                
                try:
                    # 変異
                    mutated_content = self._mutate_individual(parent)
                    
                    # 評価
                    eval_result = self.evaluate_func(mutated_content)
                    
                    # 新個体を作成
                    new_individual = Individual(
                        content=mutated_content,
                        score=eval_result['score'],
                        it_domain=eval_result['it_domain'],
                        business_function=eval_result['business_function'],
                        generation=generation,
                        evaluation_notes=eval_result.get('evaluation_notes')
                    )
                    
                    new_individuals.append(new_individual)
                    
                except Exception as e:
                    print(f"    Error during mutation/evaluation: {e}")
                    continue
            
            # アーカイブに追加
            added_count = 0
            for individual in new_individuals:
                if self._add_to_archive(individual):
                    self._save_individual(individual, generation)
                    added_count += 1
            
            print(f"  Added {added_count} new individuals to archive")
            print(f"  Archive size: {len(self.archive)}")
            
            # 統計を更新
            self._update_stats(generation)
            
            # 進捗を表示
            if len(self.archive) > 0:
                print(f"  Max score: {self.stats['max_score'][-1]:.2f}")
                print(f"  Mean score: {self.stats['mean_score'][-1]:.2f}")
    
    def save_final_report(self) -> Path:
        """最終レポートを保存"""
        report_path = self.run_dir / "final_report.json"
        
        report = {
            "run_info": {
                "directory": str(self.run_dir),
                "grid_size": self.grid_size,
                "population_size": self.population_size,
                "max_generations": self.max_generations,
                "final_archive_size": len(self.archive)
            },
            "statistics": self.stats,
            "archive_summary": []
        }
        
        # アーカイブの各個体の情報を追加
        for niche, individual in sorted(self.archive.items()):
            report["archive_summary"].append({
                "niche": {
                    "it_domain": niche[0],
                    "business_function": niche[1]
                },
                "score": individual.score,
                "generation": individual.generation,
                "filepath": str(individual.filepath.relative_to(self.run_dir)) if individual.filepath else None
            })
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nFinal report saved to: {report_path}")
        return report_path
    
    def get_best_individuals(self, top_k: int = 10) -> List[Individual]:
        """スコアが高い上位k個の個体を取得"""
        sorted_individuals = sorted(
            self.archive.values(),
            key=lambda x: x.score,
            reverse=True
        )
        return sorted_individuals[:top_k]
    
    def visualize_archive(self) -> str:
        """アーカイブの状態を可視化（テキストベース）"""
        lines = ["\nArchive Visualization (IT Domain x Business Function):"]
        lines.append("    " + "".join(f"{i:4d}" for i in range(1, self.grid_size[1] + 1)))
        
        for it_domain in range(1, self.grid_size[0] + 1):
            row = f"{it_domain:2d}: "
            for bf in range(1, self.grid_size[1] + 1):
                if (it_domain, bf) in self.archive:
                    score = int(self.archive[(it_domain, bf)].score)
                    row += f"{score:4d}"
                else:
                    row += "   -"
            lines.append(row)
        
        visualization = "\n".join(lines)
        print(visualization)
        return visualization
    
    def visualize_heatmap(
        self,
        heatmap_type: str = "score",
        save: bool = True
    ) -> Optional[object]:
        """
        アーカイブをヒートマップで可視化
        
        Args:
            heatmap_type: ヒートマップの種類
                - "score": スコアのヒートマップ
                - "generation": 世代のヒートマップ
                - "coverage": 充填率マップ
                - "combined": 3つを組み合わせた図
            save: Trueの場合、run_dirに保存
            
        Returns:
            matplotlibのFigureオブジェクト（saveがFalseの場合）
        """
        try:
            from map_elites_algorithm.visualization import create_visualizer
        except ImportError:
            print("Error: visualization module not found. Please ensure visualization.py exists.")
            return None
        
        if len(self.archive) == 0:
            print("Warning: Archive is empty. Cannot create visualization.")
            return None
        
        visualizer = create_visualizer(grid_size=self.grid_size)
        
        # 保存先パス
        save_path = None
        if save:
            viz_dir = self.run_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = viz_dir / f"{heatmap_type}_heatmap_{timestamp}.png"
        
        # ヒートマップの種類に応じて作成
        if heatmap_type == "score":
            fig = visualizer.create_score_heatmap(
                archive=self.archive,
                save_path=save_path
            )
        elif heatmap_type == "generation":
            fig = visualizer.create_generation_heatmap(
                archive=self.archive,
                save_path=save_path
            )
        elif heatmap_type == "coverage":
            fig = visualizer.create_coverage_map(
                archive=self.archive,
                save_path=save_path
            )
        elif heatmap_type == "combined":
            fig = visualizer.create_combined_visualization(
                archive=self.archive,
                save_path=save_path
            )
        else:
            print(f"Error: Unknown heatmap_type '{heatmap_type}'. "
                  f"Use 'score', 'generation', 'coverage', or 'combined'.")
            return None
        
        if not save:
            return fig
        
        return None
    
    def visualize_all_heatmaps(self) -> None:
        """全種類のヒートマップを作成して保存"""
        print("\nCreating visualizations...")
        
        heatmap_types = ["score", "generation", "coverage", "combined"]
        for hmap_type in heatmap_types:
            print(f"  Creating {hmap_type} heatmap...")
            self.visualize_heatmap(heatmap_type=hmap_type, save=True)
        
        print("All visualizations created successfully!")
