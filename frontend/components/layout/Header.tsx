"use client";

import Link from "next/link";
import { MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <MessageSquare className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">Saarthi.AI</span>
        </Link>

        <nav className="flex items-center gap-4">
          <Link href="/chat">
            <Button variant="ghost" size="sm">
              Chat
            </Button>
          </Link>
          <Link href="/pdf">
            <Button variant="ghost" size="sm">
              Documents
            </Button>
          </Link>
          <Link href="/voice">
            <Button variant="ghost" size="sm">
              Voice
            </Button>
          </Link>
          <Link href="/recommend">
            <Button variant="ghost" size="sm">
              Schemes
            </Button>
          </Link>
          <Link href="/grievance">
            <Button variant="ghost" size="sm">
              Grievance
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
