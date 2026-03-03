"use client";

import { useState } from "react";
import { FileCheck, Loader2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { generateGrievance } from "@/lib/api/grievance";
import { useToast } from "@/components/ui/use-toast";
import { ISSUE_TYPES } from "@/lib/types";

export default function GrievancePage() {
  const [issueType, setIssueType] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [complaintLetter, setComplaintLetter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!issueType || !description || !location) {
      setError("Please fill all fields");
      toast({
        title: "Missing fields",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setComplaintLetter("");
    setError(null);

    try {
      const response = await generateGrievance({
        issue_type: issueType,
        description,
        location,
      });
      setComplaintLetter(response.complaint_letter);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to generate complaint letter";
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

  const downloadPDF = () => {
    if (!complaintLetter) return;

    const element = document.createElement("a");
    const file = new Blob([complaintLetter], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `complaint_${issueType.replace(/\s+/g, "_")}_${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="container py-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Grievance Generator</h1>
          <p className="text-muted-foreground">
            Generate formal complaint letters for civic issues
          </p>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Issue Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Issue Type</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={issueType}
                  onChange={(e) => setIssueType(e.target.value)}
                  required
                >
                  <option value="">Select issue type</option>
                  {ISSUE_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <Input
                  placeholder="Enter location (e.g., Ward 5, Sector 12, City Name)"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Textarea
                  placeholder="Describe the issue in detail..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="min-h-[120px]"
                  required
                />
              </div>

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileCheck className="mr-2 h-4 w-4" />
                    Generate Complaint Letter
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && <ErrorMessage message={error} className="mb-6" />}

        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {complaintLetter && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Generated Complaint Letter</CardTitle>
                <Button variant="outline" size="sm" onClick={downloadPDF}>
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-muted/50 p-6 rounded-md border border-border">
                <pre className="text-sm text-foreground whitespace-pre-wrap font-sans">
                  {complaintLetter}
                </pre>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
