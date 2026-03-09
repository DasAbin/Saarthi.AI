"use client";

import { Suspense, useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Loader2, FileText, CheckCircle2, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function TypingResponse({ content }: { content: string }) {
  const [displayText, setDisplayText] = useState("");
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setDisplayText(content.slice(0, i));
      i++;
      if (i > content.length + 5) clearInterval(interval);
    }, 15);
    return () => clearInterval(interval);
  }, [content]);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ ...props }) => <h1 className="text-xl font-bold mb-2 mt-4" {...props} />,
        h2: ({ ...props }) => <h2 className="text-lg font-semibold mb-2 mt-4" {...props} />,
        h3: ({ ...props }) => <h3 className="font-semibold mb-1 mt-3" {...props} />,
        strong: ({ ...props }) => <strong className="font-semibold" {...props} />,
        ul: ({ ...props }) => <ul className="list-disc ml-6 mt-2 mb-2" {...props} />,
        li: ({ ...props }) => <li className="mb-1" {...props} />,
        p: ({ ...props }) => <p className="mb-2" {...props} />,
      }}
    >
      {displayText}
    </ReactMarkdown>
  );
}
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
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const { toast } = useToast();
  const params = useSearchParams();
  const docId = params.get("docId") || undefined;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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

      if ((result as any).audioUrl) {
        new Audio((result as any).audioUrl).play().catch(e => console.error("Audio playback error:", e));
      }

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
    <div className="flex flex-col min-h-screen">
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        <div className="mx-auto max-w-3xl w-full px-4">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold mb-2">Saarthi AI Assistant</h1>
            <p className="text-muted-foreground font-medium">
              Powered by Amazon Bedrock
            </p>
          </div>

          <LanguageSelector value={language} onChange={setLanguage} className="mb-6" />

          {error && <ErrorMessage message={error} className="mb-6" />}

          {messages.length > 0 && (
            <div className="flex flex-col gap-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={
                    msg.role === "user"
                      ? "bg-blue-100 p-3 rounded-lg max-w-md ml-auto"
                      : "bg-gray-100 p-4 rounded-lg max-w-2xl"
                  }>
                    <div className="text-sm font-medium mb-1">
                      {msg.role === "user" ? "You" : "Saarthi AI"}
                    </div>
                    <div className="text-sm whitespace-pre-wrap">
                      {msg.role === "assistant" ? (
                        <>
                          <TypingResponse content={msg.content} />
                          {msg.sources && msg.sources.length > 0 && (
                            <div className="mt-4 border-t border-gray-200 pt-4">
                              <div className="text-sm font-medium mb-3 text-gray-700">Sources</div>
                              <div className="flex flex-col gap-2">
                                {msg.sources.map((source: any, idx) => (
                                  <div key={idx} className="border rounded-lg p-3 bg-white shadow-sm flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <FileText className="w-4 h-4 text-blue-500" />
                                      <span className="text-sm text-gray-700 font-medium">{source.title || source.document}</span>
                                    </div>
                                    {source.url && source.url !== "#" && (
                                      <a href={source.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-700">
                                        <ExternalLink className="w-4 h-4" />
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          {msg.confidence !== undefined && (
                            <div className="mt-3 text-xs text-gray-500 font-medium">
                              Confidence: {msg.confidence}%
                            </div>
                          )}
                        </>
                      ) : (
                        msg.content
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="text-gray-500 italic">
                    Saarthi is analyzing your question...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </main>

      <footer className="border-t bg-white p-4 sticky bottom-0 z-10">
        <div className="mx-auto max-w-3xl w-full px-4">
          <form onSubmit={handleSubmit} className="space-y-4">
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
              className="min-h-[80px]"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <div className="flex md:flex-row flex-col justify-between items-start md:items-center gap-4">
              <div className="flex flex-wrap gap-2">
                {[
                  "What is PM SHRI scheme?",
                  "Ayushman Bharat eligibility",
                  "Scholarships for students",
                  "Government schemes for farmers"
                ].map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setInput(s)}
                    className="text-sm bg-blue-50 text-blue-600 rounded-full px-3 py-1.5 hover:bg-blue-100 transition-colors border border-blue-100"
                  >
                    {s}
                  </button>
                ))}
              </div>
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
            </div>
          </form>
        </div>
      </footer>
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
