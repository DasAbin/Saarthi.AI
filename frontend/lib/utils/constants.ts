/**
 * Application constants
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ||
  "https://your-api-gateway-url.execute-api.region.amazonaws.com/prod";

// With presigned S3 uploads, we can support larger files.
// Keep a reasonable UX/processing ceiling for hackathon/prototype deployments.
export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// Allow multiple document types (PDF, Word, Excel, PowerPoint, text, CSV, images, and more)
export const ALLOWED_PDF_TYPES = [
  // PDF
  "application/pdf",
  // Word
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  // Excel
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  // PowerPoint
  "application/vnd.ms-powerpoint",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  // Text formats
  "text/plain",
  "text/csv",
  "text/markdown",
  "text/html",
  "text/rtf",
  // OpenDocument
  "application/vnd.oasis.opendocument.text",
  "application/vnd.oasis.opendocument.spreadsheet",
  "application/vnd.oasis.opendocument.presentation",
  // Images
  "image/png",
  "image/jpeg",
  "image/jpg",
  "image/bmp",
  "image/tiff",
  "image/webp",
  "image/gif",
  "image/svg+xml",
];
export const ALLOWED_AUDIO_TYPES = ["audio/webm", "audio/mp3", "audio/wav"];

export const CONFIDENCE_THRESHOLD = 0.7;
export const MAX_SOURCES_DISPLAY = 5;

export const ANIMATION_DURATION = 300;
