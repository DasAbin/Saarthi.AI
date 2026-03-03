/**
 * PDF Processing API endpoints
 */

import { apiClient } from "./client";
import type { PDFProcessResponse } from "@/lib/types";

export async function processPDF(file: File): Promise<PDFProcessResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.postFormData<PDFProcessResponse>(
    "/pdf",
    formData
  );

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to process PDF");
  }

  return response.data;
}
