/**
 * Document Processing API endpoints
 * Uses presigned S3 upload URL, then triggers processing with s3Key.
 */

import { apiClient } from "./client";
import type { PDFProcessResponse } from "@/lib/types";
import { MAX_FILE_SIZE } from "@/lib/utils/constants";

type UploadUrlResponse = {
  uploadUrl: string;
  key: string;
};

async function getUploadUrl(file: File): Promise<UploadUrlResponse> {
  const response = await apiClient.post<UploadUrlResponse>("/upload-url", {
    filename: file.name,
    contentType: file.type || "application/octet-stream",
  });

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to generate upload URL");
  }

  return response.data;
}

/**
 * Check the status of a document processing job
 */
export async function checkJobStatus(jobId: string): Promise<PDFProcessResponse> {
  const response = await apiClient.get<PDFProcessResponse>(`/pdf/${jobId}`);

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to check job status");
  }

  return response.data;
}

/**
 * Process a document (PDF, Word, image, etc.) using:
 * 1) POST /upload-url
 * 2) PUT file to presigned S3 URL
 * 3) POST /pdf with { s3Key, filename }
 * 
 * For PDFs, this starts an async job and returns a jobId.
 * For images, this processes synchronously and returns the result.
 */
export async function processPDF(
  file: File,
  language: string = "en"
): Promise<PDFProcessResponse | { jobId: string; status: string }> {
  // Validate file size before processing
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`);
  }

  try {
    // 1) Get presigned upload URL
    const { uploadUrl, key } = await getUploadUrl(file);

    // 2) Upload directly to S3
    const putResponse = await fetch(uploadUrl, {
      method: "PUT",
      headers: {
        "Content-Type": file.type || "application/octet-stream",
      },
      body: file,
    });

    if (!putResponse.ok) {
      // For presigned PUTs, body is often empty; keep message simple.
      throw new Error(
        `Upload to storage failed (${putResponse.status}). Please retry.`
      );
    }

    // 3) Trigger processing
    const response = await apiClient.post<
      PDFProcessResponse | { jobId: string; status: string }
    >("/pdf", {
      s3Key: key,
      filename: file.name,
      language,
    });

    if (!response.success || !response.data) {
      throw new Error(response.message || "Failed to process document");
    }

    // If response contains jobId, it's an async PDF job - return it for polling
    if ("jobId" in response.data && "status" in response.data) {
      return response.data;
    }

    // Otherwise, it's a synchronous result (images) - return directly
    return response.data as PDFProcessResponse;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("An unexpected error occurred while processing the document");
  }
}
