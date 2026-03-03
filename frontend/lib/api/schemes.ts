/**
 * Scheme Recommendation API endpoints
 */

import { apiClient } from "./client";
import type {
  SchemeRecommendationRequest,
  SchemeRecommendationResponse,
} from "@/lib/types";

export async function recommendSchemes(
  request: SchemeRecommendationRequest
): Promise<SchemeRecommendationResponse> {
  const response = await apiClient.post<SchemeRecommendationResponse>(
    "/recommend",
    request
  );

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to get recommendations");
  }

  return response.data;
}
