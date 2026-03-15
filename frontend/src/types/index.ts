export interface User {
  id: number;
  email: string;
  full_name?: string;
  subscription_tier: 'free' | 'starter' | 'pro';
  documents_analyzed: number;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DocumentUpload {
  file: File;
}

export interface Document {
  document_id: string;
  filename: string;
  uploaded_at: string;
  analyzed_at?: string;
  expires_at?: string;
  analysis?: Analysis;
}

export interface Analysis {
  document_id: string;
  document_type: string;
  summary: string;
  key_clauses: Clause[];
  financial_obligations: string[];
  risk_alerts: string[];
  negotiation_points: string[];
  contract_risk_score: number;
  risk_heatmap: RiskHeatmapItem[];
  clause_comparisons: ClauseBenchmark[];
  legal_terms_dictionary: LegalTermDefinition[];
  language: string;
}

export interface Clause {
  title: string;
  details: string;
  risk_level: 'low' | 'medium' | 'high';
}

export interface RiskHeatmapItem {
  clause_title: string;
  risk_level: 'low' | 'medium' | 'high';
}

export interface ClauseBenchmark {
  clause_title: string;
  market_standard: string;
  document_value: string;
  assessment: 'favorable' | 'neutral' | 'needs_attention';
}

export interface LegalTermDefinition {
  term: string;
  plain_explanation: string;
}
