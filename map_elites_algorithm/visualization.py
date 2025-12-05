"""
MAP-Elitesアーカイブの可視化機能
ヒートマップを使用してアーカイブの状態を視覚化
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime

# 日本語フォントの設定
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
plt.rcParams['axes.unicode_minus'] = False


class ArchiveVisualizer:
    """アーカイブを可視化するクラス"""
    
    # ITドメインのラベル
    IT_DOMAIN_LABELS = [
        "画像検査",
        "予知保全",
        "生産計画",
        "工程分析",
        "品質予測",
        "エネルギー",
        "文書管理",
        "調達最適化",
        "安全監視",
        "トレーサビリティ"
    ]
    
    # ビジネス機能のラベル
    BUSINESS_FUNCTION_LABELS = [
        "製品企画",
        "設計開発",
        "生産技術",
        "生産計画",
        "製造実行",
        "品質管理",
        "設備保全",
        "資材管理",
        "物流管理",
        "アフターサービス"
    ]
    
    def __init__(self, grid_size: Tuple[int, int] = (10, 10)):
        """
        Args:
            grid_size: グリッドサイズ (ITドメイン数, ビジネス機能数)
        """
        self.grid_size = grid_size
    
    def create_score_heatmap(
        self,
        archive: Dict[Tuple[int, int], any],
        save_path: Optional[Path] = None,
        title: str = "MAP-Elites Archive - Score Heatmap"
    ) -> plt.Figure:
        """
        スコアのヒートマップを作成
        
        Args:
            archive: アーカイブ辞書 {(it_domain, business_function): Individual}
            save_path: 保存先パス（Noneの場合は保存しない）
            title: グラフのタイトル
            
        Returns:
            matplotlibのFigureオブジェクト
        """
        # グリッドを初期化（-1は空セルを表す）
        score_grid = np.full(self.grid_size, -1.0)
        
        # アーカイブからスコアを抽出
        for (it_domain, business_function), individual in archive.items():
            # インデックスは1-basedなので0-basedに変換
            score_grid[it_domain - 1, business_function - 1] = individual.score
        
        # ヒートマップを作成
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # マスク配列を作成（空セルを白で表示）
        masked_grid = np.ma.masked_where(score_grid < 0, score_grid)
        
        # ヒートマップを描画
        im = ax.imshow(
            masked_grid,
            cmap='YlOrRd',
            aspect='auto',
            vmin=0,
            vmax=100,
            interpolation='nearest'
        )
        
        # カラーバーを追加
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('完成度スコア', rotation=270, labelpad=20, fontsize=12)
        
        # 軸ラベルを設定
        ax.set_xticks(range(self.grid_size[1]))
        ax.set_yticks(range(self.grid_size[0]))
        ax.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right')
        ax.set_yticklabels(self.IT_DOMAIN_LABELS)
        
        ax.set_xlabel('ビジネス機能', fontsize=12)
        ax.set_ylabel('ITドメイン', fontsize=12)
        ax.set_title(title, fontsize=14, pad=20)
        
        # グリッド線を追加
        ax.set_xticks(np.arange(self.grid_size[1]) - 0.5, minor=True)
        ax.set_yticks(np.arange(self.grid_size[0]) - 0.5, minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=2)
        
        # スコアを各セルに表示
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                score = score_grid[i, j]
                if score >= 0:
                    text_color = 'white' if score > 50 else 'black'
                    ax.text(j, i, f'{int(score)}',
                           ha='center', va='center',
                           color=text_color, fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Heatmap saved to: {save_path}")
        
        return fig
    
    def create_generation_heatmap(
        self,
        archive: Dict[Tuple[int, int], any],
        save_path: Optional[Path] = None,
        title: str = "MAP-Elites Archive - Generation Heatmap"
    ) -> plt.Figure:
        """
        世代のヒートマップを作成
        
        Args:
            archive: アーカイブ辞書
            save_path: 保存先パス
            title: グラフのタイトル
            
        Returns:
            matplotlibのFigureオブジェクト
        """
        # グリッドを初期化
        generation_grid = np.full(self.grid_size, -1)
        
        # アーカイブから世代情報を抽出
        max_generation = 0
        for (it_domain, business_function), individual in archive.items():
            generation_grid[it_domain - 1, business_function - 1] = individual.generation
            max_generation = max(max_generation, individual.generation)
        
        # ヒートマップを作成
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # マスク配列を作成
        masked_grid = np.ma.masked_where(generation_grid < 0, generation_grid)
        
        # ヒートマップを描画
        im = ax.imshow(
            masked_grid,
            cmap='viridis',
            aspect='auto',
            vmin=0,
            vmax=max_generation,
            interpolation='nearest'
        )
        
        # カラーバーを追加
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('世代', rotation=270, labelpad=20, fontsize=12)
        
        # 軸ラベルを設定
        ax.set_xticks(range(self.grid_size[1]))
        ax.set_yticks(range(self.grid_size[0]))
        ax.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right')
        ax.set_yticklabels(self.IT_DOMAIN_LABELS)
        
        ax.set_xlabel('ビジネス機能', fontsize=12)
        ax.set_ylabel('ITドメイン', fontsize=12)
        ax.set_title(title, fontsize=14, pad=20)
        
        # グリッド線を追加
        ax.set_xticks(np.arange(self.grid_size[1]) - 0.5, minor=True)
        ax.set_yticks(np.arange(self.grid_size[0]) - 0.5, minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=2)
        
        # 世代を各セルに表示
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                gen = generation_grid[i, j]
                if gen >= 0:
                    ax.text(j, i, f'{gen}',
                           ha='center', va='center',
                           color='white', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Generation heatmap saved to: {save_path}")
        
        return fig
    
    def create_coverage_map(
        self,
        archive: Dict[Tuple[int, int], any],
        save_path: Optional[Path] = None,
        title: str = "MAP-Elites Archive - Coverage Map"
    ) -> plt.Figure:
        """
        充填率マップを作成
        
        Args:
            archive: アーカイブ辞書
            save_path: 保存先パス
            title: グラフのタイトル
            
        Returns:
            matplotlibのFigureオブジェクト
        """
        # グリッドを初期化（0=空, 1=充填）
        coverage_grid = np.zeros(self.grid_size)
        
        # アーカイブから充填情報を抽出
        for (it_domain, business_function) in archive.keys():
            coverage_grid[it_domain - 1, business_function - 1] = 1
        
        # 充填率を計算
        coverage_rate = (np.sum(coverage_grid) / coverage_grid.size) * 100
        
        # ヒートマップを作成
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # ヒートマップを描画
        im = ax.imshow(
            coverage_grid,
            cmap='RdYlGn',
            aspect='auto',
            vmin=0,
            vmax=1,
            interpolation='nearest'
        )
        
        # 軸ラベルを設定
        ax.set_xticks(range(self.grid_size[1]))
        ax.set_yticks(range(self.grid_size[0]))
        ax.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right')
        ax.set_yticklabels(self.IT_DOMAIN_LABELS)
        
        ax.set_xlabel('ビジネス機能', fontsize=12)
        ax.set_ylabel('ITドメイン', fontsize=12)
        ax.set_title(f'{title}\n充填率: {coverage_rate:.1f}% ({len(archive)}/{coverage_grid.size} cells)',
                    fontsize=14, pad=20)
        
        # グリッド線を追加
        ax.set_xticks(np.arange(self.grid_size[1]) - 0.5, minor=True)
        ax.set_yticks(np.arange(self.grid_size[0]) - 0.5, minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=2)
        
        # 記号を各セルに表示
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                if coverage_grid[i, j] > 0:
                    ax.text(j, i, '●',
                           ha='center', va='center',
                           color='darkgreen', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Coverage map saved to: {save_path}")
        
        return fig
    
    def create_combined_visualization(
        self,
        archive: Dict[Tuple[int, int], any],
        save_path: Optional[Path] = None,
        suptitle: str = "MAP-Elites Archive Visualization"
    ) -> plt.Figure:
        """
        3つのヒートマップを1つの図にまとめて作成
        
        Args:
            archive: アーカイブ辞書
            save_path: 保存先パス
            suptitle: 全体のタイトル
            
        Returns:
            matplotlibのFigureオブジェクト
        """
        fig = plt.figure(figsize=(20, 6))
        fig.suptitle(suptitle, fontsize=16, fontweight='bold')
        
        # スコアヒートマップ
        ax1 = plt.subplot(1, 3, 1)
        score_grid = np.full(self.grid_size, -1.0)
        for (it_domain, business_function), individual in archive.items():
            score_grid[it_domain - 1, business_function - 1] = individual.score
        
        masked_score = np.ma.masked_where(score_grid < 0, score_grid)
        im1 = ax1.imshow(masked_score, cmap='YlOrRd', aspect='auto', vmin=0, vmax=100)
        ax1.set_title('スコア分布', fontsize=12, pad=10)
        ax1.set_xticks(range(self.grid_size[1]))
        ax1.set_yticks(range(self.grid_size[0]))
        ax1.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right', fontsize=8)
        ax1.set_yticklabels(self.IT_DOMAIN_LABELS, fontsize=8)
        plt.colorbar(im1, ax=ax1, label='スコア')
        
        # 世代ヒートマップ
        ax2 = plt.subplot(1, 3, 2)
        generation_grid = np.full(self.grid_size, -1)
        max_gen = 0
        for (it_domain, business_function), individual in archive.items():
            generation_grid[it_domain - 1, business_function - 1] = individual.generation
            max_gen = max(max_gen, individual.generation)
        
        masked_gen = np.ma.masked_where(generation_grid < 0, generation_grid)
        im2 = ax2.imshow(masked_gen, cmap='viridis', aspect='auto', vmin=0, vmax=max_gen)
        ax2.set_title('世代分布', fontsize=12, pad=10)
        ax2.set_xticks(range(self.grid_size[1]))
        ax2.set_yticks(range(self.grid_size[0]))
        ax2.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right', fontsize=8)
        ax2.set_yticklabels(self.IT_DOMAIN_LABELS, fontsize=8)
        plt.colorbar(im2, ax=ax2, label='世代')
        
        # 充填率マップ
        ax3 = plt.subplot(1, 3, 3)
        coverage_grid = np.zeros(self.grid_size)
        for (it_domain, business_function) in archive.keys():
            coverage_grid[it_domain - 1, business_function - 1] = 1
        
        coverage_rate = (np.sum(coverage_grid) / coverage_grid.size) * 100
        im3 = ax3.imshow(coverage_grid, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        ax3.set_title(f'充填状況 ({coverage_rate:.1f}%)', fontsize=12, pad=10)
        ax3.set_xticks(range(self.grid_size[1]))
        ax3.set_yticks(range(self.grid_size[0]))
        ax3.set_xticklabels(self.BUSINESS_FUNCTION_LABELS, rotation=45, ha='right', fontsize=8)
        ax3.set_yticklabels(self.IT_DOMAIN_LABELS, fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Combined visualization saved to: {save_path}")
        
        return fig


def create_visualizer(grid_size: Tuple[int, int] = (10, 10)) -> ArchiveVisualizer:
    """
    ビジュアライザーを作成するヘルパー関数
    
    Args:
        grid_size: グリッドサイズ
        
    Returns:
        ArchiveVisualizerインスタンス
    """
    return ArchiveVisualizer(grid_size=grid_size)
