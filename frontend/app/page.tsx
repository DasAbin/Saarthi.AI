"use client";

import { FeatureGrid } from "@/components/layout/FeatureGrid";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-12 sm:py-20 lg:py-24">
        <div className="container">
          <div className="text-center">
            <div className="inline-flex items-center rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 mb-6">
              <Mic className="mr-2" size={18} />
              Voice-first • Multilingual • AI-Powered
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Saarthi.AI
              <span className="block text-indigo-600 mt-2 text-3xl sm:text-4xl">
                Your AI Guide to Government Schemes
              </span>
            </h1>

            <p className="mt-4 text-lg font-medium text-slate-700">
              Powered by Amazon Bedrock
            </p>

            <p className="mt-4 text-md text-slate-600 max-w-2xl mx-auto">
              Access government schemes, understand policies, analyze documents,
              and file grievances—all in your language, powered by AI.
            </p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-12">
        <div className="container">
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-bold mb-2">Features</h2>
            <p className="text-muted-foreground">
              Choose a feature to get started
            </p>
          </div>
          <FeatureGrid />
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-indigo-900 py-16">
        <div className="container text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to experience better governance?
          </h2>
          <p className="mt-4 text-lg text-indigo-100 max-w-2xl mx-auto">
            Saarthi.AI helps citizens access government schemes and understand
            documents in their language.
          </p>
        </div>
      </section>
    </div>
  );
}
