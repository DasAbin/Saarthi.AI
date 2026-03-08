"use client";

import { Suspense, useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Loader2, FileText, CheckCircle2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LanguageSelector } from "@/components/common/LanguageSelector";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { queryAI } from "@/lib/api/query";
import { useToast } from "@/components/ui/use-toast";
import type { Language, QueryResponse, ChatHistoryItem } from "@/lib/types";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: QueryResponse["sources"];
  confidence?: number;
};

function ChatContent() {
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const { toast } = useToast();
  const params = useSearchParams();
  const docId = params.get("docId") || undefined;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const userMessage: ChatMessage = {
        role: "user",
        content: input,
      };

      const nextMessages = [...messages, userMessage];
      setMessages(nextMessages);
      const history: ChatHistoryItem[] = nextMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const currentInput = input;
      setInput("");

      const result: QueryResponse = await queryAI({
        query: currentInput,
        language,
        docId,
        history,
      });

      const aiMessage: ChatMessage = {
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        confidence: result.confidence,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to get response";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Ask AI</h1>
          <p className="text-muted-foreground">
            Get answers about government schemes and policies
          </p>
        </div>

        <LanguageSelector value={language} onChange={setLanguage} className="mb-6" />

        <form onSubmit={handleSubmit} className="space-y-4 mb-6">
          <Textarea
            placeholder={
              language === "hi"
                ? "सरकारी योजनाओं के बारे में पूछें..."
                : language === "mr"
                  ? "सरकारी योजनांबद्दल विचारा..."
                  : "Ask about government schemes..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="min-h-[120px]"
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Ask
              </>
            )}
          </Button>
        </form>

        {error && <ErrorMessage message={error} className="mb-6" />}

        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {messages.length > 0 && (
          <div className="max-h-[500px] overflow-y-auto p-4 mt-6">
            <div className="flex flex-col gap-4 mt-6">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={
                    msg.role === "user"
                      ? "bg-blue-100 rounded-xl p-4 ml-auto max-w-2xl shadow-sm"
                      : "bg-gray-100 rounded-xl p-4 max-w-2xl shadow-sm"
                  }
                >
                  <div className="text-sm font-medium mb-1">
                    {msg.role === "user" ? "You" : "AI Assistant"}
                  </div>
                  <div className="text-sm whitespace-pre-wrap">
                    {msg.role === "assistant" ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({ ...props }) => (
                            <h1 className="text-xl font-bold mb-2" {...props} />
                          ),
                          h2: ({ ...props }) => (
                            <h2 className="text-lg font-semibold mb-2" {...props} />
                          ),
                          h3: ({ ...props }) => (
                            <h3 className="font-semibold mb-1" {...props} />
                          ),
                          strong: ({ ...props }) => (
                            <strong className="font-semibold" {...props} />
                          ),
                          ul: ({ ...props }) => (
                            <ul className="list-disc ml-6" {...props} />
                          ),
                          li: ({ ...props }) => (
                            <li className="mb-1" {...props} />
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="container py-8"><p className="text-muted-foreground">Loading...</p></div>}>
      <ChatContent />
    </Suspense>
  );
}
