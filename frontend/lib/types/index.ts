/**
 * TypeScript type definitions for Saarthi.AI
 */

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

// RAG Query Types
export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface QueryRequest {
  query: string;
  language: "en" | "hi" | "mr";
  docId?: string;
  history?: ChatHistoryItem[];
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  confidence: number;
}

export interface Source {
  text: string;
  source: string;
  page?: number;
  score: number;
}

// PDF Processing Types
export interface SchemeFacts {
  scheme_name: string;
  coverage_amount: string;
  launch_year: string;
  beneficiaries: string;
  target_population: string;
  institution: string;
}

export interface StakeholderRole {
  role: string;
  responsibilities: string[];
}

export interface KeyContact {
  service: string;
  contact: string;
}

export interface FAQ {
  question: string;
  answer: string;
}

export interface PDFProcessResponse {
  // New structured intelligence fields
  document_overview: string;
  scheme_facts: SchemeFacts;
  eligibility_and_coverage: string[];
  healthcare_benefits: string[];
  operational_workflow: string[];
  stakeholders_and_roles: StakeholderRole[];
  community_impact: string[];
  policy_insights: string[];
  key_contacts: KeyContact[];
  frequently_asked_questions: FAQ[];
  summary: string;
  // Legacy fields for backward compatibility
  document_type: string;
  purpose: string;
  key_points: string[];
  instructions: string[];
  // Metadata
  extracted_text: string;
  s3_key?: string;
  document_id?: string;
  chunk_count?: number;
  status?: "done" | "processing" | "error";
  error?: string;
}

// Scheme Recommendation Types
export interface SchemeRecommendationRequest {
  age: number;
  state: string;
  income: number;
  occupation: string;
}

export interface Scheme {
  name: string;
  description: string;
  eligibility: string[];
  apply_steps: string[];
  link?: string;
}

export interface SchemeRecommendationResponse {
  schemes: Scheme[];
}

// Voice Types
export interface STTResponse {
  text: string;
}

export interface TTSRequest {
  text: string;
  language?: "en" | "hi" | "mr";
}

export interface TTSResponse {
  audio: string; // base64 encoded
}

// Grievance Types
export interface GrievanceRequest {
  issue_type: string;
  description: string;
  location: string;
}

export interface GrievanceResponse {
  complaint_letter: string;
}

// Language Types
export type Language = "en" | "hi" | "mr";

export const LANGUAGES: { code: Language; name: string; native: string }[] = [
  { code: "en", name: "English", native: "English" },
  { code: "hi", name: "Hindi", native: "हिंदी" },
  { code: "mr", name: "Marathi", native: "मराठी" },
];

// Issue Types
export const ISSUE_TYPES = [
  "Water Supply",
  "Road Maintenance",
  "Garbage Collection",
  "Electricity",
  "Sewage",
  "Street Lighting",
  "Public Toilets",
  "Park Maintenance",
  "Other",
] as const;

export type IssueType = (typeof ISSUE_TYPES)[number];

// Indian States
export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Puducherry",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli",
  "Daman and Diu",
  "Lakshadweep",
] as const;

// Occupations
export const OCCUPATIONS = [
  "Farmer",
  "Student",
  "Unemployed",
  "Self-employed",
  "Government Employee",
  "Private Employee",
  "Business Owner",
  "Homemaker",
  "Retired",
  "Other",
] as const;

export type Occupation = (typeof OCCUPATIONS)[number];
