"use client";

import { useState, useRef } from "react";
import {
  Upload,
  FileText,
  Loader2,
  Download,
  CheckCircle2,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { processPDF } from "@/lib/api/pdf";
import type { PDFProcessResponse } from "@/lib/types";
import { useToast } from "@/components/ui/use-toast";

export default function PDFAnalyzer() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PDFProcessResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (
      selectedFile &&
      (selectedFile.type === "application/pdf" ||
        selectedFile.type.startsWith("image/"))
    ) {
      setFile(selectedFile);
      setResult(null);
    } else {
      toast({
        title: "Invalid file",
        description: "Please select a PDF or image file",
        variant: "destructive",
      });
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);

    try {
      const data = await processPDF(file);
      setResult(data);
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
    <div className="space-y-6">
      {/* File Upload */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,image/*"
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
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <FileText className="h-4 w-4" />
                  <span>{file.name}</span>
                  <span className="text-slate-400">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
              )}
            </div>

            {file && (
              <Button onClick={handleUpload} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Analyze PDF
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* High-level document info */}
          <Card>
            <CardContent className="pt-6 space-y-2">
              <h3 className="font-semibold text-lg mb-2 flex items-center gap-2">
                <Info className="h-5 w-5 text-indigo-600" />
                Document Overview
              </h3>
              <p className="text-sm text-slate-600">
                <span className="font-semibold">Document Type:</span>{" "}
                {result.document_type || "Unknown"}
              </p>
              {result.purpose && (
                <p className="text-sm text-slate-600">
                  <span className="font-semibold">Purpose:</span>{" "}
                  {result.purpose}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Key Information */}
          {result.key_points && result.key_points.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold text-lg mb-4">Key Information</h3>
                <ul className="space-y-2">
                  {result.key_points.map((point, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-indigo-600 mt-1">•</span>
                      <span className="text-slate-700">{point}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Important Instructions */}
          {result.instructions && result.instructions.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold text-lg mb-4">
                  Important Instructions
                </h3>
                <ul className="space-y-2">
                  {result.instructions.map((inst, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-indigo-600 mt-1">•</span>
                      <span className="text-slate-700">{inst}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Summary */}
          <Card>
            <CardContent className="pt-6">
              <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                Summary
              </h3>
              <p className="text-slate-700 whitespace-pre-wrap">
                {result.summary}
              </p>
            </CardContent>
          </Card>

          {/* Extracted Text */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">Extracted Text</h3>
                <Button variant="outline" size="sm" onClick={downloadText}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
              <div className="max-h-96 overflow-y-auto bg-slate-50 p-4 rounded-md">
                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {result.extracted_text}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
