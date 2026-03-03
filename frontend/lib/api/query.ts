/**
 * RAG Query API endpoints
 */

import { apiClient } from "./client";
import type { QueryRequest, QueryResponse } from "@/lib/types";

export async function queryAI(
  request: QueryRequest
): Promise<QueryResponse> {
  const response = await apiClient.post<QueryResponse>("/query", request);
  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to get response");
  }
  return response.data;
}
