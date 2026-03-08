/**
 * Base API client for Saarthi.AI
 * Uses Next.js API routes which proxy to AWS API Gateway
 */

import type { ApiResponse } from "@/lib/types";

if (typeof window !== 'undefined' && !process.env.NEXT_PUBLIC_API_GATEWAY_URL) {
  console.warn(
    '[Saarthi.AI] NEXT_PUBLIC_API_GATEWAY_URL is not set. ' +
    'Requests will fall back to /api (mock backend). ' +
    'Set this variable in your environment settings (e.g. Amplify).'
  );
}

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

    // Support optional timeout via AbortController (in ms). Default to 30000ms.
    const timeoutMs = (options as any).timeout !== undefined ? (options as any).timeout : 30000;
    const controller = typeof AbortController !== "undefined" ? new AbortController() : undefined;
    if (controller) {
      config.signal = controller.signal;
    }

    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    if (controller && typeof timeoutMs === "number" && timeoutMs > 0) {
      timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    }

    try {
      const response = await fetch(url, config);

      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || `API error: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request timed out after ${timeoutMs}ms`);
        }
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
