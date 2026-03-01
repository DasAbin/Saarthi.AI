"use client";

import { useState } from "react";
import { FileCheck, Loader2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { generateGrievance } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

const ISSUE_TYPES = [
  "Water Supply",
  "Road Maintenance",
  "Garbage Collection",
  "Electricity",
  "Sewage",
  "Street Lighting",
  "Public Toilets",
  "Park Maintenance",
  "Other",
];

export default function GrievanceGenerator() {
  const [issueType, setIssueType] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [complaintLetter, setComplaintLetter] = useState("");
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!issueType || !description || !location) {
      toast({
        title: "Missing fields",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setComplaintLetter("");

    try {
      const response = await generateGrievance({
        issue_type: issueType,
        description,
        location,
      });

      if (response.success && response.data) {
        setComplaintLetter(response.data.complaint_letter);
      } else {
        toast({
          title: "Error",
          description: response.message || "Failed to generate complaint letter",
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
    <div className="space-y-6">
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

      {/* Generated Letter */}
      {complaintLetter && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">Generated Complaint Letter</h3>
              <Button variant="outline" size="sm" onClick={downloadPDF}>
                <Download className="mr-2 h-4 w-4" />
                Download
              </Button>
            </div>
            <div className="bg-slate-50 p-6 rounded-md border border-slate-200">
              <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans">
                {complaintLetter}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
