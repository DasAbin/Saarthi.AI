"use client";

import { useState } from "react";
import { Search, Loader2, ExternalLink, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { recommendSchemes, type Scheme } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir",
  "Ladakh", "Puducherry", "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
  "Daman and Diu", "Lakshadweep"
];

const OCCUPATIONS = [
  "Farmer", "Student", "Unemployed", "Self-employed", "Government Employee",
  "Private Employee", "Business Owner", "Homemaker", "Retired", "Other"
];

export default function SchemeRecommendation() {
  const [age, setAge] = useState("");
  const [state, setState] = useState("");
  const [income, setIncome] = useState("");
  const [occupation, setOccupation] = useState("");
  const [loading, setLoading] = useState(false);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!age || !state || !income || !occupation) {
      toast({
        title: "Missing fields",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setSchemes([]);

    try {
      const response = await recommendSchemes({
        age: parseInt(age),
        state,
        income: parseFloat(income),
        occupation,
      });

      if (response.success && response.data) {
        setSchemes(response.data.schemes);
      } else {
        toast({
          title: "Error",
          description: response.message || "Failed to get recommendations",
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
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Age</label>
            <Input
              type="number"
              placeholder="Enter your age"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              min="1"
              max="120"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">State</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={state}
              onChange={(e) => setState(e.target.value)}
              required
            >
              <option value="">Select state</option>
              {INDIAN_STATES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Annual Income (₹)</label>
            <Input
              type="number"
              placeholder="Enter annual income"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              min="0"
              step="1000"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Occupation</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              required
            >
              <option value="">Select occupation</option>
              {OCCUPATIONS.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button type="submit" disabled={loading} className="w-full">
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Finding schemes...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Find Schemes
            </>
          )}
        </Button>
      </form>

      {/* Results */}
      {schemes.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Recommended Schemes</h3>
          {schemes.map((scheme, idx) => (
            <Card key={idx}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{scheme.name}</CardTitle>
                    <CardDescription className="mt-2">{scheme.description}</CardDescription>
                  </div>
                  {scheme.link && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={scheme.link} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {scheme.eligibility && scheme.eligibility.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        Eligibility Criteria
                      </h4>
                      <ul className="space-y-1">
                        {scheme.eligibility.map((item, i) => (
                          <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                            <span className="text-emerald-600 mt-1">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {scheme.apply_steps && scheme.apply_steps.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">How to Apply</h4>
                      <ol className="space-y-1">
                        {scheme.apply_steps.map((step, i) => (
                          <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                            <span className="font-medium text-indigo-600">{i + 1}.</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
