/**
 * HeatmapView Component
 * 
 * Clinic-level disease pattern heatmap using Plotly.js
 */

import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export interface HeatmapData {
  clinic: string;
  disease: string;
  cases: number;
  severity?: 'low' | 'medium' | 'high';
}

interface HeatmapViewProps {
  data: HeatmapData[];
  title?: string;
  height?: number;
  exportable?: boolean;
  className?: string;
}

export function HeatmapView({
  data,
  title = 'Clinic-Level Disease Patterns',
  height = 500,
  exportable = true,
  className = '',
}: HeatmapViewProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const plotInstance = useRef<any>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    // Get unique clinics and diseases
    const clinics = Array.from(new Set(data.map((d) => d.clinic))).sort();
    const diseases = Array.from(new Set(data.map((d) => d.disease))).sort();

    // Create matrix for heatmap
    const z: number[][] = [];
    const text: string[][] = [];

    clinics.forEach((clinic) => {
      const row: number[] = [];
      const textRow: string[] = [];
      
      diseases.forEach((disease) => {
        const item = data.find((d) => d.clinic === clinic && d.disease === disease);
        row.push(item?.cases || 0);
        textRow.push(item ? `${clinic}<br>${disease}<br>Cases: ${item.cases}` : '');
      });
      
      z.push(row);
      text.push(textRow);
    });

    const trace = {
      x: diseases,
      y: clinics,
      z,
      text,
      type: 'heatmap' as const,
      colorscale: [
        [0, 'rgba(255, 255, 255, 0.1)'],
        [0.3, 'rgba(37, 99, 235, 0.3)'],
        [0.6, 'rgba(37, 99, 235, 0.6)'],
        [1, 'rgba(37, 99, 235, 1)'],
      ],
      showscale: true,
      colorbar: {
        title: 'Cases',
        titlefont: {
          color: '#0F172A',
        },
        tickfont: {
          color: '#0F172A',
        },
      },
      hovertemplate: '%{text}<extra></extra>',
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
        title: 'Disease',
        gridcolor: '#E2E8F0',
        showgrid: true,
      },
      yaxis: {
        title: 'Clinic',
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
        l: 100,
        r: 30,
        t: 60,
        b: 100,
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
    });

    return () => {
      if (plotInstance.current) {
        Plotly.purge(chartRef.current!);
      }
    };
  }, [data, title, height]);

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

  if (data.length === 0) {
    return (
      <div className={clsx('flex items-center justify-center h-64 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30', className)}>
        <p className="text-[#64748B] dark:text-[#94A3B8]">No heatmap data available</p>
      </div>
    );
  }

  return (
    <div 
      className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-4', className)}
      role="region"
      aria-label={`${title} heatmap`}
    >
      {exportable && (
        <div className="flex justify-end mb-2">
          <div className="flex space-x-2" role="group" aria-label="Heatmap export options">
            <button
              type="button"
              onClick={() => handleExport('png')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export heatmap as PNG image"
            >
              <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
              <span>PNG</span>
            </button>
            <button
              type="button"
              onClick={() => handleExport('svg')}
              className="px-3 py-1.5 text-xs font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export heatmap as SVG image"
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
        aria-label={`${title} showing disease patterns across clinics. Color intensity indicates case count.`}
      />
    </div>
  );
}

