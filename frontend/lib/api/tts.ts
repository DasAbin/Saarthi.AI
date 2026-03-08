export async function generateSpeech(text: string, language: string) {
  const res = await fetch("/api/voice/tts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text,
      language,
    }),
  });

  if (!res.ok) {
    throw new Error("Failed to generate speech");
  }

  const data = await res.json();

  const base64Audio: string | undefined =
    data?.data?.audio ?? data?.audio ?? data?.Audio;

  if (!base64Audio) {
    throw new Error("No audio data returned from TTS service");
  }

  // Decode base64 to binary and wrap in a Blob for playback
  const byteString = atob(base64Audio);
  const len = byteString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = byteString.charCodeAt(i);
  }

  return new Blob([bytes], { type: "audio/mpeg" });
}

