/**
 * Base API client for Saarthi.AI
 * Always calls Next.js API routes (/api/*) which act as the proxy layer.
 *
 * The Next.js routes either:
 *   - Forward to the real AWS API Gateway (when NEXT_PUBLIC_API_GATEWAY_URL is set server-side)
 *   - Process documents locally (e.g. /api/pdf uses PyMuPDF directly)
 *   - Hit the local mock backend (when pointed at localhost:3001)
 *
 * ✅ NEVER call AWS directly from the browser — that bypasses all our
 *    server-side logic and causes 502 / CORS / auth errors.
 */

import type { ApiResponse } from "@/lib/types";

// Always route through the Next.js API layer — never call AWS directly.
const DEFAULT_BASE_URL = "/api";


class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    // If we're sending FormData, let the browser set the Content-Type (with boundary)
    const isFormData = options.body instanceof FormData;

    const defaultHeaders: HeadersInit = isFormData
      ? {}
      : {
        "Content-Type": "application/json",
      };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || `API error: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("An unexpected error occurred");
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  async post<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
  }

  async postFormData<T>(
    endpoint: string,
    formData: FormData,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
      ...options,
    });
  }
}

export const apiClient = new ApiClient();
