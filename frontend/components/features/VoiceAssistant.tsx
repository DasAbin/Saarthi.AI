"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Loader2, Volume2, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { speechToText, textToSpeech, queryAI } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

export default function VoiceAssistant() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [language, setLanguage] = useState("en");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
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
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await processAudio(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setTranscript("");
      setResponse("");
    } catch (error) {
      toast({
        title: "Error",
        description: "Could not access microphone. Please check permissions.",
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

    try {
      // Step 1: Speech to Text
      const sttResponse = await speechToText(audioBlob);
      if (!sttResponse.success || !sttResponse.data) {
        throw new Error(sttResponse.message || "STT failed");
      }

      const transcribedText = sttResponse.data.text;
      setTranscript(transcribedText);

      // Step 2: Query AI
      const aiResponse = await queryAI({ query: transcribedText, language });
      if (!aiResponse.success || !aiResponse.data) {
        throw new Error(aiResponse.message || "AI query failed");
      }

      const answer = aiResponse.data.answer;
      setResponse(answer);

      // Step 3: Text to Speech
      const ttsResponse = await textToSpeech({ text: answer, language });
      if (!ttsResponse.success || !ttsResponse.data) {
        throw new Error(ttsResponse.message || "TTS failed");
      }

      // Play audio
      const audioData = ttsResponse.data.audio;
      const audioBlob = new Blob(
        [Uint8Array.from(atob(audioData), (c) => c.charCodeAt(0))],
        { type: "audio/mpeg" }
      );
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.play();
      setIsPlaying(true);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred",
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
    <div className="space-y-6">
      {/* Language Selector */}
      <div className="flex gap-2">
        <Button
          variant={language === "en" ? "default" : "outline"}
          size="sm"
          onClick={() => setLanguage("en")}
        >
          English
        </Button>
        <Button
          variant={language === "hi" ? "default" : "outline"}
          size="sm"
          onClick={() => setLanguage("hi")}
        >
          हिंदी
        </Button>
        <Button
          variant={language === "mr" ? "default" : "outline"}
          size="sm"
          onClick={() => setLanguage("mr")}
        >
          मराठी
        </Button>
      </div>

      {/* Recording Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-6">
            <div className="relative">
              <Button
                size="lg"
                className={`h-24 w-24 rounded-full ${
                  isRecording
                    ? "bg-red-500 hover:bg-red-600 animate-pulse"
                    : "bg-indigo-600 hover:bg-indigo-700"
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
                  <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
                </div>
              )}
            </div>

            <div className="text-center">
              {isRecording && (
                <p className="text-red-600 font-medium animate-pulse">Recording...</p>
              )}
              {isProcessing && (
                <p className="text-indigo-600 font-medium">Processing...</p>
              )}
              {!isRecording && !isProcessing && (
                <p className="text-slate-600">Click to start recording</p>
              )}
            </div>

            {/* Waveform Animation */}
            {isRecording && (
              <div className="flex items-center gap-1 h-12">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-2 bg-indigo-600 rounded-full animate-wave"
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

      {/* Transcript */}
      {transcript && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-semibold text-lg mb-2">You said:</h3>
            <p className="text-slate-700">{transcript}</p>
          </CardContent>
        </Card>
      )}

      {/* Response */}
      {response && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg">Response:</h3>
              {isPlaying && (
                <Button variant="outline" size="sm" onClick={stopAudio}>
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              )}
            </div>
            <p className="text-slate-700 mb-4">{response}</p>
            {isPlaying && (
              <div className="flex items-center gap-2 text-sm text-indigo-600">
                <Volume2 className="h-4 w-4 animate-pulse" />
                <span>Playing audio...</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
