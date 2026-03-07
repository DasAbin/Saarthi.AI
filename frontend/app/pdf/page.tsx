"use client";

import { useState, useRef } from "react";
import { Upload, FileText, Loader2, Download, CheckCircle2, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { processPDF } from "@/lib/api/pdf";
import { useToast } from "@/components/ui/use-toast";
import type { PDFProcessResponse } from "@/lib/types";
import { MAX_FILE_SIZE, ALLOWED_PDF_TYPES } from "@/lib/utils/constants";

export default function PDFPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PDFProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!ALLOWED_PDF_TYPES.includes(selectedFile.type)) {
      setError("Please select a supported document format");
      toast({
        title: "Invalid file",
        description: "Supported formats: PDF, Word, Excel, PowerPoint, CSV, RTF, ODT, Markdown, HTML, Text, Images",
        variant: "destructive",
      });
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size must be less than 50MB");
      toast({
        title: "File too large",
        description: "File size must be less than 50MB",
        variant: "destructive",
      });
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await processPDF(file);
      setResult(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to process PDF";
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

  const downloadText = () => {
    if (!result) return;
    const blob = new Blob([result.extracted_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${file?.name.replace(".pdf", "") || "document"}_extracted.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container py-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Document Analyzer</h1>
          <p className="text-muted-foreground">
            Upload documents (PDF, Word, Excel, PowerPoint, CSV, RTF, ODT, Markdown, HTML, Text, Images) and get instant analysis
          </p>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.xlsx,.xls,.pptx,.ppt,.csv,.rtf,.odt,.md,.html,.htm,image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Select document
                </Button>
                {file && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>{file.name}</span>
                    <span className="text-muted-foreground">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                )}
              </div>

              {file && (
                <Button onClick={handleUpload} disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing document... This may take up to 2 minutes.
                    </>
                  ) : (
                    <>
                      <FileText className="mr-2 h-4 w-4" />
                      Analyze Document
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {error && <ErrorMessage message={error} className="mb-6" />}

        {loading && (
          <div className="flex flex-col items-center py-8 space-y-2">
            <LoadingSpinner size="lg" />
            <p className="text-sm text-muted-foreground text-center max-w-md">
              Processing document with Amazon Textract. This can take up to 2 minutes
              for large or complex PDFs. Please do not close this tab.
            </p>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* High-level document info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  Document Overview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  <span className="font-semibold">Document Type:</span>{" "}
                  {result.document_type || "Unknown"}
                </p>
                {result.purpose && (
                  <p className="text-sm text-muted-foreground">
                    <span className="font-semibold">Purpose:</span>{" "}
                    {result.purpose}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Key Information */}
            {result.key_points && result.key_points.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Key Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.key_points.map((point, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span className="text-foreground">{point}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Important Instructions */}
            {result.instructions && result.instructions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Important Instructions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.instructions.map((inst, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span className="text-foreground">{inst}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground whitespace-pre-wrap">
                  {result.summary}
                </p>
              </CardContent>
            </Card>

            {/* Extracted Text */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Extracted Text</CardTitle>
                  <Button variant="outline" size="sm" onClick={downloadText}>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="max-h-96 overflow-y-auto bg-muted/50 p-4 rounded-md">
                  <p className="text-sm text-foreground whitespace-pre-wrap">
                    {result.extracted_text}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
