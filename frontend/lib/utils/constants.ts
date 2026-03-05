/**
 * Application constants
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ||
  "https://your-api-gateway-url.execute-api.region.amazonaws.com/prod";

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const ALLOWED_PDF_TYPES = ["application/pdf"];
export const ALLOWED_DOCUMENT_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
  "application/msword", // .doc
  "text/plain",          // .txt
  "text/html",           // .html
  "image/png",
  "image/jpeg",
  "image/jpg",
  "image/bmp",
  "image/tiff",
  "image/webp",
];
export const ALLOWED_AUDIO_TYPES = ["audio/webm", "audio/mp3", "audio/wav"];

export const CONFIDENCE_THRESHOLD = 0.7;
export const MAX_SOURCES_DISPLAY = 5;

export const ANIMATION_DURATION = 300;
