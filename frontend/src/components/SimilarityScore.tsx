/**
 * Similarity Score Component
 * 
 * Visualizes similarity score with progress bar and color coding.
 */

import { clsx } from '../utils/clsx';

interface SimilarityScoreProps {
  score: number; // 0-1
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function SimilarityScore({ score, showLabel = true, size = 'md' }: SimilarityScoreProps) {
  const percentage = Math.round(score * 100);
  
  // Color coding based on score - Clinical NeoTech theme
  const getColorClass = (score: number) => {
    if (score >= 0.8) return 'bg-[#2563EB]'; // Primary Blue
    if (score >= 0.6) return 'bg-[#8B5CF6]'; // Accent Purple
    if (score >= 0.4) return 'bg-[#C4B5FD]'; // Soft Violet
    return 'bg-[#64748B]'; // Slate Gray
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        {showLabel && (
          <span className="text-xs font-medium text-[#64748B]">
            Similarity: {percentage}%
          </span>
        )}
        <span className="text-xs text-[#64748B]">
          {score.toFixed(3)}
        </span>
      </div>
      <div className="w-full bg-[#64748B]/20 rounded-full overflow-hidden">
        <div
          className={clsx(
            sizeClasses[size],
            getColorClass(score),
            'rounded-full transition-all duration-300'
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}

