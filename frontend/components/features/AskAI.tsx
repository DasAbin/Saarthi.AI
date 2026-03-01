"use client";

import { useState } from "react";
import { Send, Loader2, FileText, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { queryAI, type QueryResponse } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

export default function AskAI() {
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse["data"] | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);

    try {
      const result = await queryAI({ query, language });
      if (result.success && result.data) {
        setResponse(result.data);
      } else {
        toast({
          title: "Error",
          description: result.message || "Failed to get response",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
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

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="space-y-4">
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

      {/* Response */}
      {response && (
        <div className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-lg mb-2">Answer</h3>
                  <p className="text-slate-700 whitespace-pre-wrap">{response.answer}</p>
                </div>

                {response.confidence && (
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Confidence: {(response.confidence * 100).toFixed(1)}%</span>
                  </div>
                )}

                {response.sources && response.sources.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Sources</h4>
                    <div className="space-y-2">
                      {response.sources.map((source, idx) => (
                        <Card key={idx} className="bg-slate-50">
                          <CardContent className="pt-4">
                            <div className="flex items-start gap-2">
                              <FileText className="h-4 w-4 mt-0.5 text-slate-500" />
                              <div className="flex-1">
                                <p className="text-sm text-slate-700">{source.text}</p>
                                <div className="mt-2 flex gap-4 text-xs text-slate-500">
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
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
