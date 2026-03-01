"use client";

import { useState } from "react";
import { MessageSquare, FileText, Mic, Search, FileCheck, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import AskAI from "@/components/features/AskAI";
import PDFAnalyzer from "@/components/features/PDFAnalyzer";
import VoiceAssistant from "@/components/features/VoiceAssistant";
import SchemeRecommendation from "@/components/features/SchemeRecommendation";
import GrievanceGenerator from "@/components/features/GrievanceGenerator";

type Feature = "ask" | "pdf" | "voice" | "schemes" | "grievance";

const FEATURES: Array<{
  id: Feature;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}> = [
  {
    id: "ask",
    title: "Ask AI",
    description: "Get answers about government schemes and policies in your language",
    icon: <MessageSquare className="h-6 w-6" />,
    color: "text-indigo-600",
    bgColor: "bg-indigo-100",
  },
  {
    id: "pdf",
    title: "PDF Analyzer",
    description: "Upload government policy PDFs and get instant summaries and insights",
    icon: <FileText className="h-6 w-6" />,
    color: "text-amber-600",
    bgColor: "bg-amber-100",
  },
  {
    id: "voice",
    title: "Voice Assistant",
    description: "Speak naturally and get voice responses in Hindi, English, or Marathi",
    icon: <Mic className="h-6 w-6" />,
    color: "text-blue-600",
    bgColor: "bg-blue-100",
  },
  {
    id: "schemes",
    title: "Scheme Finder",
    description: "Discover government schemes tailored to your profile and eligibility",
    icon: <Search className="h-6 w-6" />,
    color: "text-emerald-600",
    bgColor: "bg-emerald-100",
  },
  {
    id: "grievance",
    title: "Grievance Generator",
    description: "Generate formal complaint letters for civic issues automatically",
    icon: <FileCheck className="h-6 w-6" />,
    color: "text-violet-600",
    bgColor: "bg-violet-100",
  },
];

export default function Home() {
  const [expanded, setExpanded] = useState<Feature | null>("ask");

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-12 sm:py-20 lg:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 mb-6">
              <Mic className="mr-2" size={18} />
              Voice-first • Multilingual • AI-Powered
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Saarthi.AI
              <span className="block text-indigo-600 mt-2">Your AI-Powered Public Service Assistant</span>
            </h1>

            <p className="mt-6 text-lg text-slate-600 max-w-2xl mx-auto">
              Access government schemes, understand policies, analyze documents, and file grievances—all in your language, powered by AI.
            </p>

            {/* Quick action pills */}
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              {FEATURES.map((feature) => (
                <Button
                  key={feature.id}
                  onClick={() => setExpanded(feature.id)}
                  variant={expanded === feature.id ? "default" : "outline"}
                  className="rounded-full"
                >
                  {feature.icon}
                  <span className="ml-2">{feature.title}</span>
                </Button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="pb-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-12">
            {FEATURES.map((feature) => (
              <Card
                key={feature.id}
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  expanded === feature.id ? "ring-2 ring-indigo-500" : ""
                }`}
                onClick={() => setExpanded(expanded === feature.id ? null : feature.id)}
              >
                <CardHeader>
                  <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${feature.bgColor} ${feature.color} mb-4`}>
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>

          {/* Expanded Feature Content */}
          {expanded && (
            <Card className="mt-8">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${FEATURES.find(f => f.id === expanded)?.bgColor} ${FEATURES.find(f => f.id === expanded)?.color}`}>
                      {FEATURES.find(f => f.id === expanded)?.icon}
                    </div>
                    <CardTitle className="text-2xl">{FEATURES.find(f => f.id === expanded)?.title}</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setExpanded(null)}
                  >
                    {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {expanded === "ask" && <AskAI />}
                {expanded === "pdf" && <PDFAnalyzer />}
                {expanded === "voice" && <VoiceAssistant />}
                {expanded === "schemes" && <SchemeRecommendation />}
                {expanded === "grievance" && <GrievanceGenerator />}
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-2">Saarthi.AI</h2>
          <p className="text-slate-400">
            Empowering citizens with AI-powered access to government services
          </p>
        </div>
      </footer>
    </div>
  );
}
