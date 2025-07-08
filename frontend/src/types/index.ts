// User types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  tpa_id: string;
  permissions: string[];
  is_active: boolean;
  is_verified: boolean;
  phone?: string;
  department?: string;
  title?: string;
  last_login_at?: string;
  login_count: number;
  mfa_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  TPA_ADMIN = 'tpa_admin',
  CS_MANAGER = 'cs_manager',
  CS_AGENT = 'cs_agent',
  MEMBER = 'member',
  READONLY = 'readonly',
}

// TPA types
export interface TPA {
  id: string;
  name: string;
  slug: string;
  email: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country: string;
  is_active: boolean;
  subscription_tier: string;
  max_users: number;
  max_health_plans: number;
  max_documents: number;
  settings: Record<string, any>;
  branding: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Health Plan types
export interface HealthPlan {
  id: string;
  tpa_id: string;
  name: string;
  plan_number: string;
  plan_year: number;
  effective_date: string;
  termination_date?: string;
  plan_type?: string;
  description?: string;
  deductible_individual?: number;
  deductible_family?: number;
  out_of_pocket_max_individual?: number;
  out_of_pocket_max_family?: number;
  primary_care_copay?: number;
  specialist_copay?: number;
  urgent_care_copay?: number;
  emergency_room_copay?: number;
  in_network_coinsurance?: number;
  out_of_network_coinsurance?: number;
  rx_generic_copay?: number;
  rx_brand_copay?: number;
  rx_specialty_copay?: number;
  benefits_summary?: Record<string, any>;
  exclusions?: Record<string, any>;
  network_info?: Record<string, any>;
  is_active: boolean;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

// Document types
export interface Document {
  id: string;
  tpa_id: string;
  health_plan_id?: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_hash?: string;
  document_type: DocumentType;
  title?: string;
  description?: string;
  version: string;
  processing_status: ProcessingStatus;
  processing_error?: string;
  processing_log?: Record<string, any>;
  extracted_metadata?: Record<string, any>;
  page_count?: number;
  is_public: boolean;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export enum DocumentType {
  SPD = 'spd',
  BPS = 'bps',
  AMENDMENT = 'amendment',
  CERTIFICATE = 'certificate',
  OTHER = 'other',
}

export enum ProcessingStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ARCHIVED = 'archived',
}

// Chat types
export interface Conversation {
  id: string;
  tpa_id: string;
  user_id: string;
  health_plan_id?: string;
  title?: string;
  status: ConversationStatus;
  session_id?: string;
  context?: Record<string, any>;
  total_messages: number;
  avg_response_time?: number;
  satisfaction_rating?: number;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export enum ConversationStatus {
  ACTIVE = 'active',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated',
  ARCHIVED = 'archived',
}

export interface Message {
  id: string;
  tpa_id: string;
  conversation_id: string;
  content: string;
  message_type: MessageType;
  query_intent?: string;
  query_complexity?: string;
  confidence_score?: number;
  source_documents?: Record<string, any>[];
  reasoning?: string;
  response_time?: number;
  token_count?: number;
  user_rating?: number;
  user_feedback?: string;
  was_helpful?: boolean;
  model_used?: string;
  processing_log?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export enum MessageType {
  USER_QUERY = 'user_query',
  AI_RESPONSE = 'ai_response',
  SYSTEM = 'system',
  FEEDBACK = 'feedback',
}

// API types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface ChatQueryForm {
  health_plan_id?: string;
  message: string;
}

export interface DocumentUploadForm {
  health_plan_id?: string;
  document_type: DocumentType;
  title?: string;
  description?: string;
  file: File;
}

// Analytics types
export interface UsageAnalytics {
  total_queries: number;
  total_conversations: number;
  avg_response_time: number;
  avg_confidence_score: number;
  success_rate: number;
  user_satisfaction: number;
  popular_query_types: Array<{
    type: string;
    count: number;
  }>;
  daily_usage: Array<{
    date: string;
    queries: number;
    conversations: number;
  }>;
}

export interface SystemStats {
  total_tpas: number;
  total_users: number;
  total_health_plans: number;
  total_documents: number;
  processed_documents: number;
  total_conversations: number;
  monthly_queries: number;
  system_uptime: number;
  api_response_time: number;
}