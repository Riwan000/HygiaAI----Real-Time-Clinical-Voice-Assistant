/**
 * ClusterMap Component
 * 
 * Interactive visualization for disease clusters using Plotly.js
 */

import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export interface ClusterData {
  cluster_id: string;
  time_window: string;
  case_count: number;
  characteristics: {
    symptoms: string[];
    diagnoses: string[];
    locations: string[];
  };
  pattern_insights?: string[];
}

interface ClusterMapProps {
  clusters: ClusterData[];
  title?: string;
  height?: number;
  exportable?: boolean;
  className?: string;
  onClusterClick?: (clusterId: string) => void;
}

export function ClusterMap({
  clusters,
  title = 'Disease Clusters',
  height = 500,
  exportable = true,
  className = '',
  onClusterClick,
}: ClusterMapProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const plotInstance = useRef<any>(null);

  useEffect(() => {
    if (!chartRef.current || clusters.length === 0) return;

    // Prepare data for bubble chart
    const xData: number[] = [];
    const yData: number[] = [];
    const sizes: number[] = [];
    const colors: string[] = [];
    const texts: string[] = [];
    const hoverTexts: string[] = [];

    clusters.forEach((cluster, index) => {
      // Use time window as x-axis (convert to numeric)
      const timeValue = new Date(cluster.time_window).getTime();
      xData.push(timeValue);
      
      // Use case count as y-axis
      yData.push(cluster.case_count);
      
      // Size based on case count
      sizes.push(Math.max(20, cluster.case_count * 5));
      
      // Color based on cluster size (larger = more intense)
      const intensity = Math.min(1, cluster.case_count / 50);
      colors.push(`rgba(37, 99, 235, ${0.3 + intensity * 0.7})`);
      
      // Text labels
      const mainDiagnosis = cluster.characteristics.diagnoses[0] || 'Unknown';
      texts.push(mainDiagnosis);
      
      // Hover text
      const symptoms = cluster.characteristics.symptoms.slice(0, 3).join(', ');
      const diagnoses = cluster.characteristics.diagnoses.join(', ');
      hoverTexts.push(
        `<b>Cluster ${cluster.cluster_id}</b><br>` +
        `Cases: ${cluster.case_count}<br>` +
        `Time: ${cluster.time_window}<br>` +
        `Diagnoses: ${diagnoses}<br>` +
        `Symptoms: ${symptoms}`
      );
    });

    const trace = {
      x: xData,
      y: yData,
      mode: 'markers+text' as const,
      type: 'scatter' as const,
      name: 'Clusters',
      text: texts,
      textposition: 'top center' as const,
      marker: {
        size: sizes,
        color: colors,
        line: {
          color: '#2563EB',
          width: 2,
        },
        opacity: 0.7,
      },
      hovertemplate: '%{hovertext}<extra></extra>',
      hovertext: hoverTexts,
    };

    const layout = {
      title: {
        text: title,
        font: {
          size: 18,
          color: '#1E3A8A',
        },
      },
      xaxis: {
        title: 'Time Window',
        type: 'date',
        gridcolor: '#E2E8F0',
        showgrid: true,
      },
      yaxis: {
        title: 'Case Count',
        gridcolor: '#E2E8F0',
        showgrid: true,
      },
      hovermode: 'closest' as const,
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      font: {
        color: '#0F172A',
        family: 'Inter, system-ui, sans-serif',
      },
      margin: {
        l: 60,
        r: 30,
        t: 60,
        b: 60,
      },
      height,
    };

    const config = {
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
      responsive: true,
      toImageButtonOptions: {
        format: 'png',
        filename: title.toLowerCase().replace(/\s+/g, '_'),
        height,
        width: 1200,
        scale: 2,
      },
    };

    Plotly.newPlot(chartRef.current, [trace], layout, config).then((plot) => {
      plotInstance.current = plot;
      
      // Add click handler
      if (onClusterClick) {
        chartRef.current?.on('plotly_click', (data: any) => {
          if (data.points && data.points[0]) {
            const pointIndex = data.points[0].pointNumber;
            const cluster = clusters[pointIndex];
            if (cluster) {
              onClusterClick(cluster.cluster_id);
            }
          }
        });
      }
    });

    return () => {
      if (plotInstance.current) {
        Plotly.purge(chartRef.current!);
      }
    };
  }, [clusters, title, height, onClusterClick]);

  const handleExport = async (format: 'png' | 'svg') => {
    if (!plotInstance.current || !chartRef.current) return;

    try {
      const filename = title.toLowerCase().replace(/\s+/g, '_');
      await Plotly.downloadImage(plotInstance.current, {
        format,
        filename,
        width: 1200,
        height,
        scale: 2,
      });
    } catch (error) {
      console.error(`Error exporting chart as ${format}:`, error);
      alert(`Failed to export chart as ${format}`);
    }
  };

  if (clusters.length === 0) {
    return (
      <div className={clsx('flex items-center justify-center h-64 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30', className)}>
        <p className="text-[#64748B] dark:text-[#94A3B8]">No cluster data available</p>
      </div>
    );
  }

  return (
    <div 
      className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-4', className)}
      role="region"
      aria-label={`${title} cluster map`}
    >
      {exportable && (
        <div className="flex justify-end mb-2">
          <div className="flex space-x-2" role="group" aria-label="Cluster map export options">
            <button
              type="button"
              onClick={() => handleExport('png')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export cluster map as PNG image"
            >
              <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
              <span>PNG</span>
            </button>
            <button
              type="button"
              onClick={() => handleExport('svg')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export cluster map as SVG image"
            >
              <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
              <span>SVG</span>
            </button>
          </div>
        </div>
      )}
      <div 
        ref={chartRef} 
        className="w-full"
        role="img"
        aria-label={`${title} showing ${clusters.length} disease clusters. Bubble size indicates case count.`}
      />
    </div>
  );
}

