/**
 * OutbreakAlert Component
 * 
 * Displays outbreak notifications with severity levels
 */

import { ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export interface OutbreakAlertData {
  disease: string;
  severity: 'low' | 'medium' | 'high';
  cases: number;
  recommendation: string;
  region?: string;
  detected_at?: string;
}

interface OutbreakAlertProps {
  alerts: OutbreakAlertData[];
  className?: string;
  onDismiss?: (disease: string) => void;
}

export function OutbreakAlert({ alerts, className = '', onDismiss }: OutbreakAlertProps) {
  if (alerts.length === 0) {
    return (
      <div className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6', className)}>
        <div className="flex items-center justify-center text-[#64748B] dark:text-[#94A3B8]">
          <InformationCircleIcon className="h-5 w-5 mr-2" />
          <span>No outbreak alerts at this time</span>
        </div>
      </div>
    );
  }

  const getSeverityConfig = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'high':
        return {
          icon: XCircleIcon,
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          textColor: 'text-red-800 dark:text-red-300',
          iconColor: 'text-red-600 dark:text-red-400',
          badgeColor: 'bg-red-600 dark:bg-red-500',
        };
      case 'medium':
        return {
          icon: ExclamationTriangleIcon,
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          borderColor: 'border-yellow-200 dark:border-yellow-800',
          textColor: 'text-yellow-800 dark:text-yellow-300',
          iconColor: 'text-yellow-600 dark:text-yellow-400',
          badgeColor: 'bg-yellow-600 dark:bg-yellow-500',
        };
      case 'low':
        return {
          icon: InformationCircleIcon,
          bgColor: 'bg-blue-50 dark:bg-blue-900/20',
          borderColor: 'border-blue-200 dark:border-blue-800',
          textColor: 'text-blue-800 dark:text-blue-300',
          iconColor: 'text-blue-600 dark:text-blue-400',
          badgeColor: 'bg-blue-600 dark:bg-blue-500',
        };
    }
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {alerts.map((alert, index) => {
        const config = getSeverityConfig(alert.severity);
        const Icon = config.icon;

        return (
          <div
            key={`${alert.disease}-${index}`}
            className={clsx(
              'rounded-lg border p-4',
              config.bgColor,
              config.borderColor
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <Icon className={clsx('h-6 w-6 mt-0.5 flex-shrink-0', config.iconColor)} />
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className={clsx('text-lg font-semibold', config.textColor)}>
                      {alert.disease}
                    </h3>
                    <span
                      className={clsx(
                        'px-2 py-0.5 text-xs font-semibold text-white rounded-full uppercase',
                        config.badgeColor
                      )}
                    >
                      {alert.severity}
                    </span>
                  </div>
                  
                  <div className={clsx('space-y-1 text-sm', config.textColor)}>
                    <p>
                      <strong>Cases:</strong> {alert.cases}
                    </p>
                    {alert.region && (
                      <p>
                        <strong>Region:</strong> {alert.region}
                      </p>
                    )}
                    {alert.detected_at && (
                      <p>
                        <strong>Detected:</strong>{' '}
                        {new Date(alert.detected_at).toLocaleDateString()}
                      </p>
                    )}
                    <p className="mt-2">
                      <strong>Recommendation:</strong> {alert.recommendation}
                    </p>
                  </div>
                </div>
              </div>

              {onDismiss && (
                <button
                  type="button"
                  onClick={() => onDismiss(alert.disease)}
                  className={clsx(
                    'ml-4 p-1 rounded hover:bg-opacity-20 transition-colors',
                    config.textColor
                  )}
                  aria-label="Dismiss alert"
                >
                  <XCircleIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

