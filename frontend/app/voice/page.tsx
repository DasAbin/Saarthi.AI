"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Loader2, Volume2, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LanguageSelector } from "@/components/common/LanguageSelector";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { speechToText, textToSpeech } from "@/lib/api/voice";
import { queryAI } from "@/lib/api/query";
import { useToast } from "@/components/ui/use-toast";
import type { Language } from "@/lib/types";

export default function VoicePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [language, setLanguage] = useState<Language>("en");
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [isRecording]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        await processAudio(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setTranscript("");
      setResponse("");
      setError(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Could not access microphone";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setError(null);

    try {
      // Step 1: Speech to Text
      // Convert recorded Blob into a File so our API helper (FormData) accepts it
      const audioFile = new File([audioBlob], "recording.webm", {
        type: "audio/webm",
      });
      const sttResponse = await speechToText(audioFile);
      const transcribedText = sttResponse.text;
      setTranscript(transcribedText);

      // Step 2: Query AI
      const aiResponse = await queryAI({
        query: transcribedText,
        language,
      });
      const answer = aiResponse.answer;
      setResponse(answer);

      // Step 3: Text to Speech
      const ttsResponse = await textToSpeech({
        text: answer,
        language,
      });

      // Play audio
      const audioData = ttsResponse.audio;
      const ttsAudioBlob = new Blob(
        [Uint8Array.from(atob(audioData), (c) => c.charCodeAt(0))],
        { type: "audio/mpeg" }
      );
      const audioUrl = URL.createObjectURL(ttsAudioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.play();
      setIsPlaying(true);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  return (
    <div className="container py-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Voice Assistant</h1>
          <p className="text-muted-foreground">
            Speak naturally and get voice responses
          </p>
        </div>

        <LanguageSelector
          value={language}
          onChange={setLanguage}
          className="mb-6"
        />

        {error && <ErrorMessage message={error} className="mb-6" />}

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-6">
              <div className="relative">
                <Button
                  size="lg"
                  className={`h-24 w-24 rounded-full ${
                    isRecording
                      ? "bg-destructive hover:bg-destructive/90 animate-pulse"
                      : ""
                  }`}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isProcessing}
                >
                  {isRecording ? (
                    <Square className="h-8 w-8" />
                  ) : (
                    <Mic className="h-8 w-8" />
                  )}
                </Button>
                {isProcessing && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <LoadingSpinner className="h-12 w-12 text-primary" />
                  </div>
                )}
              </div>

              <div className="text-center">
                {isRecording && (
                  <p className="text-destructive font-medium animate-pulse">
                    Recording...
                  </p>
                )}
                {isProcessing && (
                  <p className="text-primary font-medium">Processing...</p>
                )}
                {!isRecording && !isProcessing && (
                  <p className="text-muted-foreground">
                    Click to start recording
                  </p>
                )}
              </div>

              {isRecording && (
                <div className="flex items-center gap-1 h-12">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-2 bg-primary rounded-full animate-wave"
                      style={{
                        animationDelay: `${i * 0.1}s`,
                        height: `${20 + Math.random() * 30}px`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {transcript && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>You said:</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground">{transcript}</p>
            </CardContent>
          </Card>
        )}

        {response && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Response:</CardTitle>
                {isPlaying && (
                  <Button variant="outline" size="sm" onClick={stopAudio}>
                    <Square className="mr-2 h-4 w-4" />
                    Stop
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-foreground mb-4">{response}</p>
              {isPlaying && (
                <div className="flex items-center gap-2 text-sm text-primary">
                  <Volume2 className="h-4 w-4 animate-pulse" />
                  <span>Playing audio...</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
