"use client";

import { useState, useRef } from "react";
import type { ChangeEvent } from "react";
import {
  Upload,
  FileText,
  Loader2,
  Download,
  CheckCircle2,
  Info,
  Heart,
  Users,
  Globe,
  Phone,
  BarChart3,
  Building2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { processPDF, checkJobStatus } from "@/lib/api/pdf";
import { useToast } from "@/components/ui/use-toast";
import type { PDFProcessResponse } from "@/lib/types";
import { MAX_FILE_SIZE, ALLOWED_PDF_TYPES } from "@/lib/utils/constants";

export default function PDFPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PDFProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedFaqs, setExpandedFaqs] = useState<Set<number>>(new Set());
  const [jobId, setJobId] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
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
    setJobId(null);
    setPolling(false);

    try {
      const response = await processPDF(file);
      
      // Check if this is an async job (PDF) or synchronous result (image)
      if ("jobId" in response && "status" in response) {
        // Async PDF job - start polling
        const jobIdValue = response.jobId;
        setJobId(jobIdValue);
        setPolling(true);
        
        // Poll for status every 3 seconds
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await checkJobStatus(jobIdValue);
            
            // Check if job is complete (has extracted_text or status is "done")
            if (statusResponse.extracted_text || statusResponse.status === "done") {
              clearInterval(pollInterval);
              setPolling(false);
              setResult(statusResponse);
              setLoading(false);
              toast({
                title: "Success",
                description: "Document processed successfully",
              });
            } else if (statusResponse.status === "error") {
              clearInterval(pollInterval);
              setPolling(false);
              setLoading(false);
              const errorMsg = (statusResponse as any).error || "Document processing failed";
              setError(errorMsg);
              toast({
                title: "Error",
                description: errorMsg,
                variant: "destructive",
              });
            }
            // If status is still "processing", continue polling
          } catch (pollErr) {
            // Don't stop polling on transient errors
            console.error("Polling error:", pollErr);
          }
        }, 3000); // Poll every 3 seconds
        
        // Stop polling after 5 minutes (max wait time)
        setTimeout(() => {
          clearInterval(pollInterval);
          if (polling) {
            setPolling(false);
            setLoading(false);
            setError("Document processing timed out. Please try again.");
            toast({
              title: "Timeout",
              description: "Document processing took too long. Please try again.",
              variant: "destructive",
            });
          }
        }, 300000); // 5 minutes
      } else {
        // Synchronous result (images) - set result immediately
        setResult(response as PDFProcessResponse);
        setLoading(false);
        toast({
          title: "Success",
          description: "Document processed successfully",
        });
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to process PDF";
      setError(errorMessage);
      setLoading(false);
      setPolling(false);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const downloadText = () => {
    if (!result) return;
    const blob = new Blob([result.extracted_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const fileName = file?.name ? file.name.replace(".pdf", "") : "document";
    a.download = fileName + "_extracted.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleFaq = (index: number) => {
    const newExpanded = new Set(expandedFaqs);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedFaqs(newExpanded);
  };

  return (
    <div className="w-full max-w-[1500px] mx-auto px-8 py-6">
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
              <Button onClick={handleUpload} disabled={loading || polling}>
                {loading || polling ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {polling ? "Processing document... Checking status..." : "Starting document processing..."}
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

      {(loading || polling) && (
        <div className="flex flex-col items-center py-8 space-y-2">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-muted-foreground text-center max-w-md">
            {polling 
              ? (jobId 
                  ? `Processing document with Amazon Textract (Job ID: ${jobId}). This can take up to 2 minutes for large PDFs. Please do not close this tab.`
                  : "Processing document with Amazon Textract. This can take up to 2 minutes for large PDFs. Please do not close this tab.")
              : "Starting document processing..."}
          </p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Two-Column Dashboard Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr]" style={{ gap: '24px' }}>
              {/* LEFT COLUMN */}
              <div className="space-y-5">
                {/* Document Overview */}
                <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                  <CardHeader className="p-0 pb-4">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <span className="text-xl">📄</span>
                      Document Overview
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <p className="text-foreground whitespace-pre-wrap">
                      {result.document_overview || result.purpose || "No overview available."}
                    </p>
                  </CardContent>
                </Card>

                {/* Community Impact */}
                {result.community_impact && result.community_impact.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">🌍</span>
                        Community Impact
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ul className="space-y-2">
                        {result.community_impact.map((impact, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-green-600 mt-1">•</span>
                            <span className="text-foreground">{impact}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* AI Policy Insights */}
                {result.policy_insights && result.policy_insights.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">🧠</span>
                        AI Policy Insights
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ul className="space-y-2">
                        {result.policy_insights.map((insight, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-amber-600 mt-1">•</span>
                            <span className="text-foreground">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Eligibility & Coverage */}
                {result.eligibility_and_coverage && result.eligibility_and_coverage.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">📋</span>
                        Eligibility & Coverage
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ul className="space-y-2">
                        {result.eligibility_and_coverage.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-primary mt-1">•</span>
                            <span className="text-foreground">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Operational Workflow */}
                {result.operational_workflow && result.operational_workflow.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">⚙️</span>
                        Operational Workflow
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <ol className="space-y-3 list-decimal list-inside">
                        {result.operational_workflow.map((step, idx) => (
                          <li key={idx} className="text-foreground">
                            <span className="font-semibold text-primary">{idx + 1}.</span> {step}
                          </li>
                        ))}
                      </ol>
                    </CardContent>
                  </Card>
                )}

                {/* Summary */}
                <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                  <CardHeader className="p-0 pb-4">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                      Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <p className="text-foreground whitespace-pre-wrap">
                      {result.summary}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* RIGHT COLUMN */}
              <div className="space-y-5">
                {/* Scheme Facts */}
                {result.scheme_facts && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">📊</span>
                        Scheme Facts
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                          <tbody className="divide-y divide-border">
                            {result.scheme_facts.scheme_name && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Scheme Name</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.scheme_name}</td>
                              </tr>
                            )}
                            {result.scheme_facts.coverage_amount && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Coverage</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.coverage_amount}</td>
                              </tr>
                            )}
                            {result.scheme_facts.launch_year && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Launch Year</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.launch_year}</td>
                              </tr>
                            )}
                            {result.scheme_facts.beneficiaries && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Beneficiaries</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.beneficiaries}</td>
                              </tr>
                            )}
                            {result.scheme_facts.target_population && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Target</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.target_population}</td>
                              </tr>
                            )}
                            {result.scheme_facts.institution && (
                              <tr>
                                <td className="py-2 px-3 text-sm font-semibold text-foreground bg-muted">Institution</td>
                                <td className="py-2 px-3 text-sm text-foreground">{result.scheme_facts.institution}</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Key Contacts */}
                {result.key_contacts && result.key_contacts.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">📞</span>
                        Key Contacts
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                          <thead>
                            <tr className="bg-muted">
                              <th className="py-2 px-3 text-left text-xs font-semibold text-foreground">Service</th>
                              <th className="py-2 px-3 text-left text-xs font-semibold text-foreground">Contact</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {result.key_contacts.map((contact, idx) => (
                              <tr key={idx}>
                                <td className="py-2 px-3 text-sm text-foreground">{contact.service || "-"}</td>
                                <td className="py-2 px-3 text-sm text-foreground">{contact.contact || "-"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Stakeholders & Roles */}
                {result.stakeholders_and_roles && result.stakeholders_and_roles.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">👥</span>
                        Stakeholders
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="space-y-3">
                        {result.stakeholders_and_roles.map((stakeholder, idx) => (
                          <div key={idx} className="border rounded-lg p-3 bg-muted/50">
                            <h4 className="font-semibold text-foreground mb-2 text-sm">{stakeholder.role}</h4>
                            <ul className="space-y-1">
                              {stakeholder.responsibilities.map((resp, rIdx) => (
                                <li key={rIdx} className="text-xs text-muted-foreground flex items-start gap-2">
                                  <span className="text-purple-600 mt-1">•</span>
                                  <span>{resp}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Frequently Asked Questions */}
                {result.frequently_asked_questions && result.frequently_asked_questions.length > 0 && (
                  <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
                    <CardHeader className="p-0 pb-4">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <span className="text-xl">❓</span>
                        FAQs
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="space-y-2">
                        {result.frequently_asked_questions.map((faq, idx) => (
                          <div key={idx} className="border rounded-lg overflow-hidden">
                            <button
                              onClick={() => toggleFaq(idx)}
                              className="w-full flex items-center justify-between p-3 text-left hover:bg-muted transition-colors"
                            >
                              <span className="font-semibold text-foreground text-sm">{faq.question}</span>
                              {expandedFaqs.has(idx) ? (
                                <ChevronUp className="h-4 w-4 text-muted-foreground flex-shrink-0 ml-2" />
                              ) : (
                                <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0 ml-2" />
                              )}
                            </button>
                            {expandedFaqs.has(idx) && (
                              <div className="p-3 pt-0 text-foreground bg-muted/50 text-sm">
                                {faq.answer}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Extracted Text - Full Width */}
            <Card className="shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
              <CardHeader className="p-0 pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <FileText className="h-5 w-5" />
                    Extracted Text
                  </CardTitle>
                  <Button variant="outline" size="sm" onClick={downloadText}>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-y-auto bg-muted/50 p-4 rounded-md" style={{ maxHeight: '300px' }}>
                  <p className="text-sm text-foreground whitespace-pre-wrap">
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
