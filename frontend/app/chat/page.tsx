"use client";

import { useState } from "react";
import { Send, Loader2, FileText, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LanguageSelector } from "@/components/common/LanguageSelector";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { queryAI } from "@/lib/api/query";
import { useToast } from "@/components/ui/use-toast";
import type { Language, QueryResponse } from "@/lib/types";

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState<Language>("en");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    setError(null);

    try {
      const result = await queryAI({ query, language });
      setResponse(result);
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
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-h-[120px]"
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !query.trim()}>
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

        {response && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Answer</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-700 whitespace-pre-wrap">
                  {response.answer}
                </p>
                {response.confidence && (
                  <div className="flex items-center gap-2 mt-4 text-sm text-muted-foreground">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>
                      Confidence: {(response.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {response.sources && response.sources.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {response.sources.map((source, idx) => (
                      <Card key={idx} className="bg-muted/50">
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-2">
                            <FileText className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm text-foreground">
                                {source.text}
                              </p>
                              <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
                                <span>{source.source}</span>
                                {source.page && <span>Page {source.page}</span>}
                                <span>Score: {(source.score * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
