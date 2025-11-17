/**
 * File Upload Component
 * 
 * Multimodal file upload with drag-and-drop, validation, progress tracking, and previews.
 */

import { useState, useRef, useCallback } from 'react';
import {
  CloudArrowUpIcon,
  DocumentIcon,
  PhotoIcon,
  MusicalNoteIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';
import type { UploadedFile } from '../types';

interface FileUploadProps {
  onFilesSelected?: (files: UploadedFile[]) => void;
  onFileUploaded?: (file: UploadedFile, response: any) => void;
  onFileError?: (file: UploadedFile, error: string) => void;
  maxFileSize?: number; // in bytes, default 50MB
  acceptedFileTypes?: {
    audio?: string[];
    text?: string[];
    image?: string[];
    lab_report?: string[];
  };
  multiple?: boolean;
  disabled?: boolean;
}

const DEFAULT_MAX_SIZE = 50 * 1024 * 1024; // 50MB

const DEFAULT_ACCEPTED_TYPES = {
  audio: ['.wav', '.mp3', '.m4a', '.ogg'],
  text: ['.txt', '.doc', '.docx'],
  image: ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
  lab_report: ['.pdf', '.png', '.jpg', '.jpeg'],
};

export function FileUpload({
  onFilesSelected,
  onFileUploaded,
  onFileError,
  maxFileSize = DEFAULT_MAX_SIZE,
  acceptedFileTypes = DEFAULT_ACCEPTED_TYPES,
  multiple = true,
  disabled = false,
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  /**
   * Determine file type based on extension
   */
  const getFileType = (file: File): UploadedFile['type'] => {
    const name = file.name.toLowerCase();
    const extension = name.substring(name.lastIndexOf('.'));

    if (acceptedFileTypes.audio?.some((ext) => name.endsWith(ext))) {
      return 'audio';
    }
    if (acceptedFileTypes.text?.some((ext) => name.endsWith(ext))) {
      return 'text';
    }
    if (acceptedFileTypes.lab_report?.some((ext) => name.endsWith(ext))) {
      return 'lab_report';
    }
    if (acceptedFileTypes.image?.some((ext) => name.endsWith(ext))) {
      return 'image';
    }
    return 'text'; // default
  };

  /**
   * Validate file
   */
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > maxFileSize) {
      return {
        valid: false,
        error: `File size exceeds ${(maxFileSize / 1024 / 1024).toFixed(0)}MB limit`,
      };
    }

    // Check file type
    const fileType = getFileType(file);
    const name = file.name.toLowerCase();
    const allAcceptedTypes = [
      ...(acceptedFileTypes.audio || []),
      ...(acceptedFileTypes.text || []),
      ...(acceptedFileTypes.image || []),
      ...(acceptedFileTypes.lab_report || []),
    ];

    const isAccepted = allAcceptedTypes.some((ext) => name.endsWith(ext));
    if (!isAccepted) {
      return {
        valid: false,
        error: `File type not supported. Accepted: ${allAcceptedTypes.join(', ')}`,
      };
    }

    return { valid: true };
  };

  /**
   * Process selected files
   */
  const processFiles = useCallback(
    (fileList: FileList | File[]) => {
      const fileArray = Array.from(fileList);
      const newFiles: UploadedFile[] = [];

      fileArray.forEach((file) => {
        const validation = validateFile(file);
        const fileType = getFileType(file);

        const uploadedFile: UploadedFile = {
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          file,
          type: fileType,
          status: validation.valid ? 'pending' : 'error',
          progress: 0,
          error: validation.error,
        };

        newFiles.push(uploadedFile);
      });

      if (multiple) {
        setFiles((prev) => [...prev, ...newFiles]);
      } else {
        setFiles(newFiles);
      }

      if (onFilesSelected) {
        onFilesSelected(newFiles);
      }
    },
    [multiple, onFilesSelected, maxFileSize, acceptedFileTypes]
  );

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
    // Reset input to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  /**
   * Handle drag and drop
   */
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;

    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  /**
   * Remove file
   */
  const handleRemoveFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  /**
   * Get file icon
   */
  const getFileIcon = (type: UploadedFile['type']) => {
    switch (type) {
      case 'audio':
        return <MusicalNoteIcon className="h-6 w-6" />;
      case 'image':
        return <PhotoIcon className="h-6 w-6" />;
      case 'lab_report':
        return <DocumentIcon className="h-6 w-6" />;
      default:
        return <DocumentIcon className="h-6 w-6" />;
    }
  };

  /**
   * Format file size
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  /**
   * Get accept string for input
   */
  const getAcceptString = (): string => {
    const allTypes = [
      ...(acceptedFileTypes.audio || []),
      ...(acceptedFileTypes.text || []),
      ...(acceptedFileTypes.image || []),
      ...(acceptedFileTypes.lab_report || []),
    ];
    return allTypes.join(',');
  };

  return (
    <div className="w-full">
      {/* Drop Zone */}
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="region"
        aria-label="File upload drop zone"
        aria-describedby="file-upload-instructions"
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
          isDragging
            ? 'border-[#2563EB] bg-[#2563EB]/5 dark:border-[#60A5FA] dark:bg-[#2563EB]/10'
            : 'border-[#64748B]/30 dark:border-[#475569]/30 hover:border-[#2563EB]/50 dark:hover:border-[#60A5FA]/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={getAcceptString()}
          onChange={handleFileInputChange}
          disabled={disabled}
          className="hidden"
          aria-label="File upload input"
          aria-describedby="file-upload-instructions"
        />

        <div className="flex flex-col items-center space-y-4">
          <div
            className={clsx(
              'p-4 rounded-full transition-colors',
              isDragging
                ? 'bg-[#2563EB]/10 dark:bg-[#2563EB]/20'
                : 'bg-[#64748B]/10 dark:bg-[#475569]/20'
            )}
          >
            <CloudArrowUpIcon
              className={clsx(
                'h-10 w-10 transition-colors',
                isDragging
                  ? 'text-[#2563EB] dark:text-[#60A5FA]'
                  : 'text-[#64748B] dark:text-[#94A3B8]'
              )}
              aria-hidden="true"
            />
          </div>

          <div id="file-upload-instructions">
            <p className="text-base font-semibold text-[#1E3A8A] dark:text-white mb-1">
              {isDragging ? 'Drop files here' : 'Drag and drop files here'}
            </p>
            <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
              or{' '}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="text-[#2563EB] dark:text-[#60A5FA] hover:underline font-medium focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
                aria-label="Browse files to upload"
                aria-disabled={disabled}
              >
                browse files
              </button>
            </p>
          </div>

          <div className="text-xs text-[#64748B] dark:text-[#94A3B8] space-y-1" role="note">
            <p>
              Supported: Audio (.wav, .mp3), Text (.txt, .doc, .docx), Images (.jpg, .png), Lab Reports (.pdf)
            </p>
            <p>Max file size: {(maxFileSize / 1024 / 1024).toFixed(0)}MB</p>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6 space-y-3" role="region" aria-label="Selected files">
          <h3 className="text-sm font-semibold text-[#1E3A8A] dark:text-white">
            Selected Files ({files.length})
          </h3>
          <div className="space-y-2" role="list" aria-label="List of selected files">
            {files.map((uploadedFile) => (
              <FilePreview
                key={uploadedFile.id}
                file={uploadedFile}
                onRemove={() => handleRemoveFile(uploadedFile.id)}
                formatFileSize={formatFileSize}
                getFileIcon={getFileIcon}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * File Preview Component
 */
interface FilePreviewProps {
  file: UploadedFile;
  onRemove: () => void;
  formatFileSize: (bytes: number) => string;
  getFileIcon: (type: UploadedFile['type']) => React.ReactNode;
}

function FilePreview({ file, onRemove, formatFileSize, getFileIcon }: FilePreviewProps) {
  const getStatusIcon = () => {
    switch (file.status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-600 dark:text-green-400" aria-hidden="true" />;
      case 'error':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-600 dark:text-red-400" aria-hidden="true" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (file.status) {
      case 'completed':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'error':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      case 'uploading':
        return 'border-[#2563EB]/30 dark:border-[#60A5FA]/30 bg-[#2563EB]/5 dark:bg-[#2563EB]/10';
      default:
        return 'border-slate/20 dark:border-[#475569]/30 bg-white dark:bg-[#1E293B]';
    }
  };

  return (
    <div
      className={clsx(
        'flex items-center justify-between p-4 rounded-lg border transition-all',
        getStatusColor()
      )}
      role="listitem"
      aria-label={`File: ${file.file.name}, ${formatFileSize(file.file.size)}, ${file.type.replace('_', ' ')}${file.status === 'uploading' ? `, ${file.progress}% uploaded` : file.status === 'completed' ? ', uploaded successfully' : file.status === 'error' ? `, error: ${file.error || 'unknown error'}` : ''}`}
    >
      <div className="flex items-center space-x-3 flex-1 min-w-0">
        <div className="flex-shrink-0 text-[#64748B] dark:text-[#94A3B8]" aria-hidden="true">
          {getFileIcon(file.type)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium text-[#0F172A] dark:text-white truncate">
              {file.file.name}
            </p>
            {getStatusIcon()}
          </div>
          <div className="flex items-center space-x-3 mt-1">
            <p className="text-xs text-[#64748B] dark:text-[#94A3B8]">
              {formatFileSize(file.file.size)}
            </p>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[#64748B]/10 dark:bg-[#475569]/30 text-[#64748B] dark:text-[#94A3B8] capitalize">
              {file.type.replace('_', ' ')}
            </span>
            {file.status === 'uploading' && (
              <span className="text-xs text-[#2563EB] dark:text-[#60A5FA]" aria-live="polite">
                {file.progress}%
              </span>
            )}
          </div>

          {/* Progress Bar */}
          {file.status === 'uploading' && (
            <div 
              className="mt-2 w-full bg-[#64748B]/20 dark:bg-[#475569]/30 rounded-full h-1.5"
              role="progressbar"
              aria-valuenow={file.progress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Upload progress: ${file.progress}%`}
            >
              <div
                className="bg-[#2563EB] dark:bg-[#60A5FA] h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${file.progress}%` }}
              />
            </div>
          )}

          {/* Error Message */}
          {file.error && (
            <p 
              className="mt-1 text-xs text-red-600 dark:text-red-400"
              role="alert"
              aria-live="assertive"
            >
              {file.error}
            </p>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={onRemove}
        className="flex-shrink-0 p-1 rounded-md text-[#64748B] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
        aria-label={`Remove ${file.file.name}`}
      >
        <XMarkIcon className="h-5 w-5" aria-hidden="true" />
      </button>
    </div>
  );
}

