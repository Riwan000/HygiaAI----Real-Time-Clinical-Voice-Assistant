/**
 * Multimodal Input Page
 * 
 * Page for uploading audio, text, images, and lab reports with metadata.
 */

import { useState } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { FileUpload } from '../components/FileUpload';
import { Loading } from '../components/Loading';
import { SOAPNoteViewer } from '../components/SOAPNoteViewer';
import { ClinicalMemoryService, type IngestRequest } from '../services/clinicalMemoryService';
import type { UploadedFile, SOAPNote } from '../types';
import { CheckCircleIcon, ExclamationCircleIcon, XMarkIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export function MultimodalInput() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<Map<string, any>>(new Map());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());

  // Form metadata
  const [patientId, setPatientId] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [region, setRegion] = useState('');
  const [comorbidities, setComorbidities] = useState<string[]>([]);
  const [comorbidityInput, setComorbidityInput] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [outcome, setOutcome] = useState('');

  /**
   * Handle files selected
   */
  const handleFilesSelected = (files: UploadedFile[]) => {
    setUploadedFiles(files);
    // Clear previous errors for new files
    setErrors(new Map());
  };

  /**
   * Add comorbidity
   */
  const handleAddComorbidity = () => {
    if (comorbidityInput.trim() && !comorbidities.includes(comorbidityInput.trim())) {
      setComorbidities([...comorbidities, comorbidityInput.trim()]);
      setComorbidityInput('');
    }
  };

  /**
   * Remove comorbidity
   */
  const handleRemoveComorbidity = (index: number) => {
    setComorbidities(comorbidities.filter((_, i) => i !== index));
  };

  /**
   * Upload files
   */
  const handleUpload = async () => {
    if (uploadedFiles.length === 0) {
      setErrors(new Map([['general', 'Please select at least one file to upload']]));
      return;
    }

    if (!patientId.trim()) {
      setErrors(new Map([['general', 'Patient ID is required']]));
      return;
    }

    setIsUploading(true);
    setErrors(new Map());
    setUploadResults(new Map());

    // Group files by type
    const audioFiles = uploadedFiles.filter((f) => f.type === 'audio');
    const imageFiles = uploadedFiles.filter((f) => f.type === 'image');
    const textFiles = uploadedFiles.filter((f) => f.type === 'text');
    const labReportFiles = uploadedFiles.filter((f) => f.type === 'lab_report');

    // Update file statuses to uploading
    setUploadedFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading' as const, progress: 0 }))
    );

    try {
      // Upload each file type (or batch if multiple of same type)
      const uploadPromises: Promise<void>[] = [];

      // Upload audio files
      audioFiles.forEach((uploadedFile) => {
        const promise = uploadSingleFile(uploadedFile, 'audio_file');
        uploadPromises.push(promise);
      });

      // Upload image files
      imageFiles.forEach((uploadedFile) => {
        const promise = uploadSingleFile(uploadedFile, 'image_file');
        uploadPromises.push(promise);
      });

      // Upload text files
      textFiles.forEach((uploadedFile) => {
        const promise = uploadSingleFile(uploadedFile, 'text_file');
        uploadPromises.push(promise);
      });

      // Upload lab report files (as image_file for now, backend will handle)
      labReportFiles.forEach((uploadedFile) => {
        const promise = uploadSingleFile(uploadedFile, 'image_file');
        uploadPromises.push(promise);
      });

      await Promise.all(uploadPromises);
    } catch (error) {
      console.error('Upload error:', error);
      setErrors(new Map([['general', 'Failed to upload files. Please try again.']]));
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Upload a single file
   */
  const uploadSingleFile = async (uploadedFile: UploadedFile, fileField: string): Promise<void> => {
    try {
      // Simulate progress (in real implementation, use axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? { ...f, progress: Math.min(f.progress + 10, 90) }
              : f
          )
        );
      }, 200);

      // Prepare request
      const request: IngestRequest = {
        patient_id: patientId,
        age_group: ageGroup || undefined,
        region: region || undefined,
        comorbidities: comorbidities.length > 0 ? comorbidities : undefined,
        diagnosis: diagnosis || undefined,
        outcome: outcome || undefined,
        [fileField]: uploadedFile.file,
      };

      // Call API
      const response = await ClinicalMemoryService.ingestCase(request);

      clearInterval(progressInterval);

      if (response.success && response.data) {
        // Mark as completed
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? { ...f, status: 'completed' as const, progress: 100 }
              : f
          )
        );

        // Store result
        setUploadResults((prev) => new Map(prev.set(uploadedFile.id, response.data)));
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to upload file';
      
      // Mark as error
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? { ...f, status: 'error' as const, error: errorMessage }
            : f
        )
      );

      // Store error
      setErrors((prev) => new Map(prev.set(uploadedFile.id, errorMessage)));
    }
  };

  /**
   * Clear all files
   */
  const handleClearAll = () => {
    setUploadedFiles([]);
    setUploadResults(new Map());
    setErrors(new Map());
  };

  const hasUploadedFiles = uploadedFiles.length > 0;
  const allFilesCompleted = uploadedFiles.every((f) => f.status === 'completed');
  const hasErrors = errors.size > 0 || uploadedFiles.some((f) => f.status === 'error');

  return (
    <div className="max-w-4xl mx-auto">
      <Breadcrumbs items={[{ name: 'Multimodal Input' }]} />

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white mb-3 font-heading" style={{ fontWeight: 600 }}>
          Multimodal Input
        </h1>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          Upload audio recordings, text transcripts, images, and lab reports for case ingestion
        </p>
      </div>

      {/* Error Alert */}
      {errors.has('general') && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <ExclamationCircleIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
            <p className="text-sm text-red-800 dark:text-red-300">{errors.get('general')}</p>
          </div>
        </div>
      )}

      {/* Success Alert */}
      {allFilesCompleted && !hasErrors && (
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
            <p className="text-sm text-green-800 dark:text-green-300">
              All files uploaded successfully!
            </p>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Patient Metadata Form */}
        <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6">
          <h2 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Patient Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Patient ID */}
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Patient ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                placeholder="Enter patient ID"
                required
              />
            </div>

            {/* Age Group */}
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Age Group
              </label>
              <select
                value={ageGroup}
                onChange={(e) => setAgeGroup(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
              >
                <option value="">Select age group</option>
                <option value="pediatric">Pediatric (0-17)</option>
                <option value="adult">Adult (18-64)</option>
                <option value="elderly">Elderly (65+)</option>
              </select>
            </div>

            {/* Region */}
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Region
              </label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                placeholder="Enter region"
              />
            </div>

            {/* Diagnosis */}
            <div>
              <label 
                htmlFor="diagnosis-input"
                className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2"
              >
                Diagnosis
              </label>
              <input
                id="diagnosis-input"
                type="text"
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                placeholder="Enter diagnosis"
                aria-required="false"
              />
            </div>

            {/* Comorbidities */}
            <div className="md:col-span-2">
              <label 
                htmlFor="comorbidity-input"
                className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2"
              >
                Comorbidities
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  id="comorbidity-input"
                  type="text"
                  value={comorbidityInput}
                  onChange={(e) => setComorbidityInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddComorbidity())}
                  className="flex-1 px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                  placeholder="Add comorbidity and press Enter"
                  aria-label="Add comorbidity"
                  aria-describedby="comorbidity-help"
                />
                <button
                  type="button"
                  onClick={handleAddComorbidity}
                  className="px-4 py-2.5 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
                  aria-label="Add comorbidity to list"
                >
                  Add
                </button>
              </div>
              <p id="comorbidity-help" className="sr-only">
                Type a comorbidity and press Enter or click Add to include it in the list
              </p>
              {comorbidities.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {comorbidities.map((comorbidity, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-[#C4B5FD]/20 dark:bg-[#8B5CF6]/20 text-[#8B5CF6] dark:text-[#C4B5FD]"
                    >
                      {comorbidity}
                      <button
                        type="button"
                        onClick={() => handleRemoveComorbidity(index)}
                        className="ml-2 text-[#8B5CF6] dark:text-[#C4B5FD] hover:text-[#1E3A8A] dark:hover:text-white"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Outcome */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Outcome
              </label>
              <input
                type="text"
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                placeholder="Enter treatment outcome"
              />
            </div>
          </div>
        </div>

        {/* File Upload Section */}
        <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6">
          <h2 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Upload Files
          </h2>

          <FileUpload
            onFilesSelected={handleFilesSelected}
            multiple={true}
            disabled={isUploading}
          />
        </div>

        {/* Action Buttons */}
        {hasUploadedFiles && (
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handleClearAll}
              disabled={isUploading}
              className="px-4 py-2.5 text-sm font-medium text-[#0F172A] dark:text-white bg-slate/10 dark:bg-[#475569]/30 rounded-lg hover:bg-slate/20 dark:hover:bg-[#475569]/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Clear All
            </button>

            <button
              type="button"
              onClick={handleUpload}
              disabled={isUploading || !patientId.trim()}
              className={clsx(
                'px-6 py-2.5 text-sm font-semibold text-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200',
                isUploading || !patientId.trim()
                  ? 'bg-[#64748B] dark:bg-[#475569] cursor-not-allowed'
                  : 'bg-[#2563EB] dark:bg-[#3B82F6] hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB]'
              )}
            >
              {isUploading ? (
                <span className="flex items-center space-x-2">
                  <Loading size="sm" />
                  <span>Uploading...</span>
                </span>
              ) : (
                'Upload Files'
              )}
            </button>
          </div>
        )}

        {/* SOAP Note Display */}
        {Array.from(uploadResults.values()).map((result, idx) => {
          const soapNote = result?.soap_note;
          if (!soapNote) return null;

          return (
            <div key={`soap-${idx}`} className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6 mt-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>
                  <DocumentTextIcon className="h-5 w-5 inline-block mr-2" />
                  SOAP Report
                </h2>
                <span className="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded">
                  Generated & Saved
                </span>
              </div>
              <SOAPNoteViewer
                soapNote={soapNote as SOAPNote}
                patientInfo={{
                  id: patientId,
                  age: ageGroup,
                }}
                caseMetadata={{
                  age_group: ageGroup,
                  region: region,
                  comorbidities: comorbidities,
                  diagnosis: diagnosis,
                  outcome: outcome,
                }}
                editable={false}
                showVersionHistory={false}
                showAnnotations={false}
              />
            </div>
          );
        })}

        {/* RAG Suggestions Display */}
        {Array.from(uploadResults.values()).map((result, idx) => {
          const suggestions = result?.rag_suggestions;
          if (!suggestions || suggestions.error) return null;

          return (
            <div key={`suggestions-${idx}`} className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6 mt-6">
              <h2 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
                🤖 AI Clinical Suggestions
              </h2>

              {/* Differential Diagnoses */}
              {suggestions.differential_diagnoses && suggestions.differential_diagnoses.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-md font-semibold text-[#0F172A] dark:text-white mb-3">Differential Diagnoses</h3>
                  <div className="space-y-2">
                    {suggestions.differential_diagnoses.map((diag: any, i: number) => (
                      <div key={i} className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <div className="flex justify-between items-start">
                          <span className="font-medium text-[#0F172A] dark:text-white">{diag.diagnosis}</span>
                          <span className="text-sm text-[#64748B] dark:text-[#94A3B8] ml-2">
                            {typeof diag.confidence === 'number' 
                              ? `${(diag.confidence * 100).toFixed(1)}%`
                              : diag.confidence}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {suggestions.recommendations && suggestions.recommendations.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-md font-semibold text-[#0F172A] dark:text-white mb-3">Recommendations</h3>
                  <div className="space-y-3">
                    {suggestions.recommendations.map((rec: any, i: number) => (
                      <div key={i} className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="inline-block px-2 py-1 text-xs font-medium bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded mr-2">
                              {rec.type}
                            </span>
                            <span className="font-semibold text-[#0F172A] dark:text-white">{rec.title}</span>
                          </div>
                          <span className={clsx(
                            "text-xs font-medium px-2 py-1 rounded",
                            rec.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
                            rec.priority === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                            'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
                          )}>
                            {rec.priority}
                          </span>
                        </div>
                        <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mb-2">{rec.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-[#64748B] dark:text-[#94A3B8]">
                            Confidence: {(rec.confidence * 100).toFixed(1)}%
                          </span>
                          {rec.citations && rec.citations.length > 0 && (
                            <span className="text-xs text-[#2563EB] dark:text-[#3B82F6]">
                              {rec.citations.length} citation{rec.citations.length !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              {suggestions.summary && (
                <div className="mb-4">
                  <h3 className="text-md font-semibold text-[#0F172A] dark:text-white mb-2">Summary</h3>
                  <p className="text-sm text-[#64748B] dark:text-[#94A3B8] bg-slate/5 dark:bg-[#334155] p-3 rounded-lg">
                    {suggestions.summary}
                  </p>
                </div>
              )}

              {/* Confidence Score */}
              {suggestions.confidence_score !== undefined && (
                <div className="text-xs text-[#64748B] dark:text-[#94A3B8] mt-4">
                  Overall Confidence: {(suggestions.confidence_score * 100).toFixed(1)}%
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

