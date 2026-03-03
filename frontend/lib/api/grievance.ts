/**
 * Grievance API endpoints
 */

import { apiClient } from "./client";
import type { GrievanceRequest, GrievanceResponse } from "@/lib/types";

export async function generateGrievance(
  request: GrievanceRequest
): Promise<GrievanceResponse> {
  const response = await apiClient.post<GrievanceResponse>(
    "/grievance",
    request
  );

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to generate complaint letter");
  }

  return response.data;
}
