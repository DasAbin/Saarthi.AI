const API_BASE_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'https://your-api-gateway-url.execute-api.region.amazonaws.com/prod';

export interface QueryRequest {
  query: string;
  language: string;
}

export interface QueryResponse {
  success: boolean;
  message?: string;
  data?: {
    answer: string;
    sources: Array<{
      text: string;
      source: string;
      page?: number;
      score: number;
    }>;
    confidence: number;
  };
}

export interface PDFProcessResponse {
  success: boolean;
  message?: string;
  data?: {
    extracted_text: string;
    summary: string;
    points: string[];
  };
}

export interface RecommendRequest {
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

export interface RecommendResponse {
  success: boolean;
  message?: string;
  data?: {
    schemes: Scheme[];
  };
}

export interface STTResponse {
  success: boolean;
  message?: string;
  data?: {
    text: string;
  };
}

export interface TTSRequest {
  text: string;
  language?: string;
}

export interface TTSResponse {
  success: boolean;
  message?: string;
  data?: {
    audio: string; // base64 encoded audio
  };
}

export interface GrievanceRequest {
  issue_type: string;
  description: string;
  location: string;
}

export interface GrievanceResponse {
  success: boolean;
  message?: string;
  data?: {
    complaint_letter: string;
  };
}

export async function queryAI(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function processPDF(file: File): Promise<PDFProcessResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function recommendSchemes(request: RecommendRequest): Promise<RecommendResponse> {
  const response = await fetch(`${API_BASE_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function speechToText(audioFile: File): Promise<STTResponse> {
  const formData = new FormData();
  formData.append('audio', audioFile);

  const response = await fetch(`${API_BASE_URL}/voice/stt`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function textToSpeech(request: TTSRequest): Promise<TTSResponse> {
  const response = await fetch(`${API_BASE_URL}/voice/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function generateGrievance(request: GrievanceRequest): Promise<GrievanceResponse> {
  const response = await fetch(`${API_BASE_URL}/grievance`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}
