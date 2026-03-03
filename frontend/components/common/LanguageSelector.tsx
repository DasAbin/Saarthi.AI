"use client";

import { Button } from "@/components/ui/button";
import { LANGUAGES, type Language } from "@/lib/types";
import { cn } from "@/lib/utils";

interface LanguageSelectorProps {
  value: Language;
  onChange: (language: Language) => void;
  className?: string;
}

export function LanguageSelector({
  value,
  onChange,
  className,
}: LanguageSelectorProps) {
  return (
    <div className={cn("flex gap-2", className)}>
      {LANGUAGES.map((lang) => (
        <Button
          key={lang.code}
          variant={value === lang.code ? "default" : "outline"}
          size="sm"
          onClick={() => onChange(lang.code)}
        >
          {lang.native}
        </Button>
      ))}
    </div>
  );
}
