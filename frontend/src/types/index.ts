/**
 * TypeScript type definitions for HygiaAI Frontend
 */

// Note: ApiResponse is defined in services/api.ts to avoid circular dependencies

// Clinical Memory Types
export type Case = {
  id: string;
  patient_id: string;
  transcript?: string;
  soap_note?: SOAPNote;
  metadata: CaseMetadata;
  similarity_score?: number;
};

export type CaseMetadata = {
  age_group?: string;
  region?: string;
  comorbidities?: string[];
  diagnosis?: string;
  outcome?: string;
  timestamp: string;
};

export type SOAPNote = {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  metadata?: {
    generated_at: string;
    entity_count: number;
    transcript_length: number;
    patient_metadata?: CaseMetadata;
  };
};

export type SimilarCase = {
  case: Case;
  similarity_score: number;
  matching_entities?: string[];
};

// Transcription Types
export type TranscriptionResult = {
  transcript: string;
  confidence: number;
  words?: WordTimestamp[];
  speakers?: SpeakerSegment[];
  is_final: boolean;
};

export type WordTimestamp = {
  word: string;
  start: number;
  end: number;
  confidence: number;
};

export type SpeakerSegment = {
  speaker: number;
  start: number;
  end: number;
  text: string;
};

// Visualization Types
export type TrendData = {
  date: string;
  value: number;
  label?: string;
};

export type ClusterData = {
  id: string;
  cases: Case[];
  characteristics: {
    symptoms: string[];
    diagnoses: string[];
    locations: string[];
  };
};

// Knowledge Base Types
export type KnowledgeEntry = {
  id: string;
  title: string;
  content: string;
  source: string;
  domain: string;
  year?: number;
  provenance_url: string;
};

// File Upload Types
export type UploadedFile = {
  id: string;
  file: File;
  type: 'audio' | 'text' | 'image' | 'lab_report';
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
  error?: string;
};

