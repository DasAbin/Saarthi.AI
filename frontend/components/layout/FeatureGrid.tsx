"use client";

import Link from "next/link";
import {
  MessageSquare,
  FileText,
  Mic,
  Search,
  FileCheck,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const features = [
  {
    id: "chat",
    title: "Ask AI",
    description: "Get answers about government schemes and policies",
    icon: MessageSquare,
    href: "/chat",
    color: "text-indigo-600",
    bgColor: "bg-indigo-100",
  },
  {
    id: "pdf",
    title: "Document Analyzer",
    description: "Upload and analyze government policy documents (PDF, Word, images)",
    icon: FileText,
    href: "/pdf",
    color: "text-amber-600",
    bgColor: "bg-amber-100",
  },
  {
    id: "voice",
    title: "Voice Assistant",
    description: "Speak naturally and get voice responses",
    icon: Mic,
    href: "/voice",
    color: "text-blue-600",
    bgColor: "bg-blue-100",
  },
  {
    id: "recommend",
    title: "Scheme Finder",
    description: "Discover schemes tailored to your profile",
    icon: Search,
    href: "/recommend",
    color: "text-emerald-600",
    bgColor: "bg-emerald-100",
  },
  {
    id: "grievance",
    title: "Grievance Generator",
    description: "Generate formal complaint letters automatically",
    icon: FileCheck,
    href: "/grievance",
    color: "text-violet-600",
    bgColor: "bg-violet-100",
  },
];

export function FeatureGrid() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {features.map((feature) => {
        const Icon = feature.icon;
        return (
          <Link key={feature.id} href={feature.href}>
            <Card className="h-full transition-all hover:shadow-lg cursor-pointer">
              <CardHeader>
                <div
                  className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${feature.bgColor} ${feature.color} mb-4`}
                >
                  <Icon className="h-6 w-6" />
                </div>
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  Try Now
                </Button>
              </CardContent>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
