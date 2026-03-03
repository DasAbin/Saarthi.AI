/**
 * Voice STT/TTS API endpoints
 */

import { apiClient } from "./client";
import type { STTResponse, TTSRequest, TTSResponse } from "@/lib/types";

export async function speechToText(audioFile: File): Promise<STTResponse> {
  const formData = new FormData();
  formData.append("audio", audioFile);

  const response = await apiClient.postFormData<STTResponse>(
    "/voice/stt",
    formData
  );

  if (!response.success || !response.data) {
    throw new Error(response.message || "Failed to transcribe audio");
  }

  return response.data;
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
