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
export interface QueryRequest {
  query: string;
  language: "en" | "hi" | "mr";
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
export interface PDFProcessResponse {
  document_type: string;
  purpose: string;
  key_points: string[];
  instructions: string[];
  summary: string;
  extracted_text: string;
  s3_key?: string;
  document_id?: string;
  chunk_count?: number;
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
