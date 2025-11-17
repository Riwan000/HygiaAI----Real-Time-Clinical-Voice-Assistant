/**
 * TrendChart Component
 * 
 * Interactive time-series chart for disease trends using Plotly.js
 */

import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
  confidence_interval?: {
    lower: number;
    upper: number;
  };
}

interface TrendChartProps {
  data: TrendDataPoint[];
  title?: string;
  yAxisLabel?: string;
  showConfidenceInterval?: boolean;
  height?: number;
  exportable?: boolean;
  className?: string;
  'aria-label'?: string;
}

export function TrendChart({
  data,
  title = 'Disease Trend',
  yAxisLabel = 'Cases',
  showConfidenceInterval = true,
  height = 400,
  exportable = true,
  className = '',
  'aria-label': ariaLabel,
}: TrendChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const plotInstance = useRef<any>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    const dates = data.map((d) => d.date);
    const values = data.map((d) => d.value);
    const labels = data.map((d) => d.label || '');

    const traces: any[] = [
      {
        x: dates,
        y: values,
        type: 'scatter',
        mode: 'lines+markers',
        name: title,
        line: {
          color: '#2563EB',
          width: 2,
        },
        marker: {
          color: '#2563EB',
          size: 6,
        },
        text: labels,
        hovertemplate: '<b>%{text}</b><br>' +
          'Date: %{x}<br>' +
          'Value: %{y}<extra></extra>',
      },
    ];

    // Add confidence interval if available
    if (showConfidenceInterval && data[0]?.confidence_interval) {
      const lower = data.map((d) => d.confidence_interval?.lower || d.value);
      const upper = data.map((d) => d.confidence_interval?.upper || d.value);

      traces.push({
        x: dates,
        y: upper,
        type: 'scatter',
        mode: 'lines',
        name: 'Upper CI',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
      });

      traces.push({
        x: dates,
        y: lower,
        type: 'scatter',
        mode: 'lines',
        name: 'Lower CI',
        line: { width: 0 },
        fill: 'tonexty',
        fillcolor: 'rgba(37, 99, 235, 0.1)',
        showlegend: false,
        hoverinfo: 'skip',
      });
    }

    const layout = {
      title: {
        text: title,
        font: {
          size: 18,
          color: '#1E3A8A',
        },
      },
      xaxis: {
        title: 'Date',
        type: 'date',
        gridcolor: '#E2E8F0',
        showgrid: true,
      },
      yaxis: {
        title: yAxisLabel,
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

    Plotly.newPlot(chartRef.current, traces, layout, config).then((plot) => {
      plotInstance.current = plot;
    });

    return () => {
      if (plotInstance.current) {
        Plotly.purge(chartRef.current!);
      }
    };
  }, [data, title, yAxisLabel, showConfidenceInterval, height]);

  const handleExport = async (format: 'png' | 'svg' | 'pdf') => {
    if (!plotInstance.current || !chartRef.current) return;

    try {
      const filename = title.toLowerCase().replace(/\s+/g, '_');
      
      if (format === 'pdf') {
        // For PDF, we'll use the image export and convert
        const imgData = await Plotly.toImage(plotInstance.current, {
          format: 'png',
          width: 1200,
          height,
          scale: 2,
        });
        
        // Create a link to download
        const link = document.createElement('a');
        link.href = imgData;
        link.download = `${filename}.png`;
        link.click();
      } else {
        await Plotly.downloadImage(plotInstance.current, {
          format,
          filename,
          width: 1200,
          height,
          scale: 2,
        });
      }
    } catch (error) {
      console.error(`Error exporting chart as ${format}:`, error);
      alert(`Failed to export chart as ${format}`);
    }
  };

  if (data.length === 0) {
    return (
      <div className={clsx('flex items-center justify-center h-64 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30', className)}>
        <p className="text-[#64748B] dark:text-[#94A3B8]">No data available</p>
      </div>
    );
  }

  return (
    <div 
      className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-4', className)}
      role="region"
      aria-label={ariaLabel || `${title} chart`}
    >
      {exportable && (
        <div className="flex justify-end mb-2">
          <div className="flex space-x-2" role="group" aria-label="Chart export options">
            <button
              type="button"
              onClick={() => handleExport('png')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export chart as PNG image"
            >
              <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
              <span>PNG</span>
            </button>
            <button
              type="button"
              onClick={() => handleExport('svg')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export chart as SVG image"
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
        aria-label={ariaLabel || `${title} showing ${data.length} data points`}
      />
    </div>
  );
}

