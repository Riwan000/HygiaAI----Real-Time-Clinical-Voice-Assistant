#!/usr/bin/env python3
"""
Visualization Script for HygiaAI

Displays temporal trends, case maps, and outbreak signals graphically.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle
import numpy as np

from src.storage.qdrant_storage import QdrantStorage
from src.retrieval.case_retrieval import CaseRetriever
from src.visualization.temporal_trends import TemporalTrendAnalyzer, TrendOptions, TrendGranularity
from src.visualization.case_map import CaseMapGenerator, MapOptions, MapProjection

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def visualize_temporal_trends(analyzer: TemporalTrendAnalyzer):
    """Visualize temporal trends for symptoms, diagnoses, and outcomes"""
    print_section("Temporal Trends Visualization")
    
    # Create trend options
    trend_options = TrendOptions(
        start_date=datetime.now(timezone.utc) - timedelta(days=30),
        end_date=datetime.now(timezone.utc),
        granularity=TrendGranularity.DAILY
    )
    
    # Analyze trends
    print("Analyzing symptom trends...")
    symptom_trends = analyzer.analyze_symptom_trends(trend_options)
    
    print("Analyzing diagnosis trends...")
    diagnosis_trends = analyzer.analyze_diagnosis_trends(trend_options)
    
    print("Analyzing outcome trends...")
    outcome_trends = analyzer.analyze_outcome_trends(trend_options)
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle('HygiaAI - Temporal Trends Analysis', fontsize=16, fontweight='bold')
    
    # Plot symptom trends
    if symptom_trends.data_points:
        dates = [dp.timestamp for dp in symptom_trends.data_points]
        values = [dp.value for dp in symptom_trends.data_points]
        counts = [dp.count for dp in symptom_trends.data_points]
        
        ax1 = axes[0]
        ax1.plot(dates, values, marker='o', linewidth=2, markersize=6, color='#2E86AB', label='Avg Symptoms per Case')
        ax1.fill_between(dates, values, alpha=0.3, color='#2E86AB')
        ax1.set_ylabel('Average Symptoms per Case', fontsize=11, fontweight='bold')
        ax1.set_title('Symptom Trends Over Time', fontsize=12, fontweight='bold', pad=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add count annotations
        ax1_twin = ax1.twinx()
        ax1_twin.bar(dates, counts, alpha=0.2, color='#A23B72', label='Total Symptom Count')
        ax1_twin.set_ylabel('Total Symptom Count', fontsize=11, fontweight='bold', color='#A23B72')
        ax1_twin.tick_params(axis='y', labelcolor='#A23B72')
        ax1_twin.legend(loc='upper right')
    else:
        axes[0].text(0.5, 0.5, 'No symptom trend data available', 
                    ha='center', va='center', transform=axes[0].transAxes, fontsize=12)
        axes[0].set_title('Symptom Trends Over Time', fontsize=12, fontweight='bold')
    
    # Plot diagnosis trends
    if diagnosis_trends.data_points:
        dates = [dp.timestamp for dp in diagnosis_trends.data_points]
        values = [dp.value for dp in diagnosis_trends.data_points]
        counts = [dp.count for dp in diagnosis_trends.data_points]
        
        ax2 = axes[1]
        ax2.plot(dates, values, marker='s', linewidth=2, markersize=6, color='#F18F01', label='Unique Diagnoses')
        ax2.fill_between(dates, values, alpha=0.3, color='#F18F01')
        ax2.set_ylabel('Number of Unique Diagnoses', fontsize=11, fontweight='bold')
        ax2.set_title('Diagnosis Trends Over Time', fontsize=12, fontweight='bold', pad=10)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add count annotations
        ax2_twin = ax2.twinx()
        ax2_twin.bar(dates, counts, alpha=0.2, color='#C73E1D', label='Total Diagnosis Count')
        ax2_twin.set_ylabel('Total Diagnosis Count', fontsize=11, fontweight='bold', color='#C73E1D')
        ax2_twin.tick_params(axis='y', labelcolor='#C73E1D')
        ax2_twin.legend(loc='upper right')
    else:
        axes[1].text(0.5, 0.5, 'No diagnosis trend data available', 
                    ha='center', va='center', transform=axes[1].transAxes, fontsize=12)
        axes[1].set_title('Diagnosis Trends Over Time', fontsize=12, fontweight='bold')
    
    # Plot outcome trends
    if outcome_trends.data_points:
        dates = [dp.timestamp for dp in outcome_trends.data_points]
        values = [dp.value for dp in outcome_trends.data_points]
        counts = [dp.count for dp in outcome_trends.data_points]
        
        ax3 = axes[2]
        ax3.plot(dates, values, marker='^', linewidth=2, markersize=6, color='#6A994E', label='Total Outcomes')
        ax3.fill_between(dates, values, alpha=0.3, color='#6A994E')
        ax3.set_ylabel('Total Outcomes', fontsize=11, fontweight='bold')
        ax3.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax3.set_title('Outcome Trends Over Time', fontsize=12, fontweight='bold', pad=10)
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='upper left')
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax3.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        axes[2].text(0.5, 0.5, 'No outcome trend data available', 
                    ha='center', va='center', transform=axes[2].transAxes, fontsize=12)
        axes[2].set_title('Outcome Trends Over Time', fontsize=12, fontweight='bold')
        axes[2].set_xlabel('Date', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('temporal_trends.png', dpi=300, bbox_inches='tight')
    print("✓ Saved temporal trends to: temporal_trends.png")
    plt.show()

def visualize_outbreak_signals(analyzer: TemporalTrendAnalyzer):
    """Visualize outbreak detection signals"""
    print_section("Outbreak Detection Visualization")
    
    # Detect outbreak signals
    outbreak_signals = analyzer.detect_outbreak_signals(
        symptom_keywords=["fever", "cough", "pneumonia", "shortness of breath"],
        time_window_days=7,
        threshold=2.0
    )
    
    if not outbreak_signals['signals']:
        print("No outbreak signals detected.")
        return
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    symptoms = [s['symptom'] for s in outbreak_signals['signals']]
    surge_ratios = [s['surge_ratio'] for s in outbreak_signals['signals']]
    recent_counts = [s['recent_count'] for s in outbreak_signals['signals']]
    baseline_counts = [s['baseline_count'] for s in outbreak_signals['signals']]
    alert_levels = [s['alert_level'] for s in outbreak_signals['signals']]
    
    # Color mapping for alert levels
    colors = ['#FF6B6B' if level == 'high' else '#FFA500' for level in alert_levels]
    
    # Create bar chart
    x_pos = np.arange(len(symptoms))
    bars = ax.bar(x_pos, surge_ratios, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add threshold line
    ax.axhline(y=outbreak_signals['threshold'], color='red', linestyle='--', 
               linewidth=2, label=f'Threshold ({outbreak_signals["threshold"]}x)')
    
    # Add value labels on bars
    for i, (bar, ratio, recent, baseline) in enumerate(zip(bars, surge_ratios, recent_counts, baseline_counts)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{ratio:.2f}x\n({recent}/{baseline})',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Symptom', fontsize=12, fontweight='bold')
    ax.set_ylabel('Surge Ratio', fontsize=12, fontweight='bold')
    ax.set_title('Outbreak Detection Signals', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(symptoms, rotation=45, ha='right')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('outbreak_signals.png', dpi=300, bbox_inches='tight')
    print("✓ Saved outbreak signals to: outbreak_signals.png")
    plt.show()

def visualize_case_map(map_generator: CaseMapGenerator):
    """Visualize case map with clustering"""
    print_section("Case Map Visualization")
    
    # Generate case map
    map_options = MapOptions(
        projection_method=MapProjection.SIMPLE_2D,
        dimensions=2,
        cluster_cases=True,
        num_clusters=3
    )
    
    print("Generating case map...")
    case_map = map_generator.generate_case_map(
        limit=50,  # Get more cases for better visualization
        options=map_options
    )
    
    if not case_map.points:
        print("No cases available for mapping.")
        return
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Extract coordinates
    x_coords = [point.x for point in case_map.points]
    y_coords = [point.y for point in case_map.points]
    cluster_ids = [point.cluster_id if point.cluster_id is not None else -1 
                   for point in case_map.points]
    case_ids = [point.case_id for point in case_map.points]
    
    # Color map for clusters
    unique_clusters = sorted(set(cluster_ids))
    colors_map = plt.cm.Set3(np.linspace(0, 1, len(unique_clusters)))
    cluster_colors = {cid: colors_map[i] for i, cid in enumerate(unique_clusters)}
    
    # Plot points
    for i, (x, y, cid) in enumerate(zip(x_coords, y_coords, cluster_ids)):
        color = cluster_colors.get(cid, 'gray')
        ax.scatter(x, y, c=color, s=100, alpha=0.6, edgecolors='black', linewidth=1)
        
        # Add case ID label (only for first few to avoid clutter)
        if i < 10:
            ax.annotate(case_ids[i][:8], (x, y), xytext=(5, 5), 
                       textcoords='offset points', fontsize=8, alpha=0.7)
    
    # Add cluster legend
    if case_map.clusters:
        legend_elements = []
        for cluster_id, cluster_info in case_map.clusters.items():
            color = cluster_colors.get(cluster_id, 'gray')
            legend_elements.append(
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                          markersize=10, label=f'Cluster {cluster_id} ({cluster_info["size"]} cases)',
                          markeredgecolor='black', markeredgewidth=1)
            )
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    ax.set_xlabel('Dimension 1', fontsize=12, fontweight='bold')
    ax.set_ylabel('Dimension 2', fontsize=12, fontweight='bold')
    ax.set_title('Case Map - Similarity Visualization', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('case_map.png', dpi=300, bbox_inches='tight')
    print("✓ Saved case map to: case_map.png")
    plt.show()

def main():
    """Main visualization function"""
    print("=" * 80)
    print("  HygiaAI Visualization Dashboard")
    print("=" * 80)
    print("\nThis script generates visualizations for:")
    print("  - Temporal trends (symptoms, diagnoses, outcomes)")
    print("  - Outbreak detection signals")
    print("  - Case map with clustering\n")
    
    try:
        # Initialize storage and retriever
        storage = QdrantStorage(
            host="localhost",
            port=6333,
            collection_name="clinical_cases",
            vector_size=768,
            enable_encryption=False,
            enable_deidentification=False
        )
        
        retriever = CaseRetriever(qdrant_storage=storage)
        
        # Initialize analyzers
        trend_analyzer = TemporalTrendAnalyzer(
            qdrant_storage=storage,
            case_retriever=retriever
        )
        
        map_generator = CaseMapGenerator(
            qdrant_storage=storage,
            case_retriever=retriever
        )
        
        # Generate visualizations
        visualize_temporal_trends(trend_analyzer)
        visualize_outbreak_signals(trend_analyzer)
        visualize_case_map(map_generator)
        
        print("\n" + "=" * 80)
        print("  Visualization Complete!")
        print("=" * 80)
        print("\nGenerated files:")
        print("  - temporal_trends.png")
        print("  - outbreak_signals.png")
        print("  - case_map.png")
        
    except Exception as e:
        print(f"\n✗ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure:")
        print("  1. Qdrant is running on localhost:6333")
        print("  2. The collection 'clinical_cases' exists and has data")
        print("  3. matplotlib is installed: pip install matplotlib")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVisualization interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

