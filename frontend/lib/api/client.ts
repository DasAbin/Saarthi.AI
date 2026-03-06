/**
 * Base API client for Saarthi.AI
 * Uses Next.js API routes which proxy to AWS API Gateway
 */

import type { ApiResponse } from "@/lib/types";

// Prefer calling API Gateway directly when NEXT_PUBLIC_API_GATEWAY_URL is set,
// otherwise fall back to Next.js API routes under /api (useful for local mocks).
const DEFAULT_BASE_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL || "/api";

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
