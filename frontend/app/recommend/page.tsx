"use client";

import { useState } from "react";
import { Search, Loader2, ExternalLink, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { recommendSchemes } from "@/lib/api/schemes";
import { useToast } from "@/components/ui/use-toast";
import type { Scheme } from "@/lib/types";
import { INDIAN_STATES, OCCUPATIONS } from "@/lib/types";

export default function RecommendPage() {
  const [age, setAge] = useState("");
  const [state, setState] = useState("");
  const [income, setIncome] = useState("");
  const [occupation, setOccupation] = useState("");
  const [loading, setLoading] = useState(false);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!age || !state || !income || !occupation) {
      setError("Please fill all fields");
      toast({
        title: "Missing fields",
        description: "Please fill all fields",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setSchemes([]);
    setError(null);

    try {
      const response = await recommendSchemes({
        age: parseInt(age),
        state,
        income: parseFloat(income),
        occupation,
      });
      setSchemes(response.schemes);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to get recommendations";
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
          <h1 className="text-3xl font-bold mb-2">Scheme Finder</h1>
          <p className="text-muted-foreground">
            Discover government schemes tailored to your profile
          </p>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Your Profile</CardTitle>
            <CardDescription>
              Fill in your details to get personalized recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>

        {error && <ErrorMessage message={error} className="mb-6" />}

        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {schemes.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Recommended Schemes</h2>
            {schemes.map((scheme, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{scheme.name}</CardTitle>
                      <CardDescription className="mt-2">
                        {scheme.description}
                      </CardDescription>
                    </div>
                    {scheme.link && (
                      <Button variant="outline" size="sm" asChild>
                        <a
                          href={scheme.link}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
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
                            <li
                              key={i}
                              className="text-sm text-foreground flex items-start gap-2"
                            >
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
                            <li
                              key={i}
                              className="text-sm text-foreground flex items-start gap-2"
                            >
                              <span className="font-medium text-primary">
                                {i + 1}.
                              </span>
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
    </div>
  );
}
