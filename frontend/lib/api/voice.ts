/**
 * Voice STT/TTS API endpoints
 */

import { apiClient } from "./client";
import type { STTResponse, TTSRequest, TTSResponse } from "@/lib/types";

export async function speechToText(audioFile: File, language = "en"): Promise<STTResponse> {
  // Convert audio file to base64 and send as JSON.
  // Sending multipart/form-data through API Gateway is unreliable for binary
  // (API Gateway re-encodes the body), so we use base64+JSON which is guaranteed
  // to arrive intact. The backend STT Lambda already handles { audio: "<base64>" }.
  const arrayBuffer = await audioFile.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64Audio = btoa(binary);

  const response = (await apiClient.post<any>("/voice/stt", {
    audio: base64Audio,
    language,
  })) as any;

  if (!response || !response.success || !response.text) {
    const message =
      (response && (response.error as string)) ||
      response?.message ||
      "Failed to transcribe audio";
    throw new Error(message);
  }

  return { text: response.text };
}

export async function textToSpeech(
  request: TTSRequest
): Promise<TTSResponse> {
  const response = await apiClient.post<TTSResponse>("/voice/tts", request);

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to synthesize speech");
  }

  return response.data;
}
