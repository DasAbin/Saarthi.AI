"use client";

export function Footer() {
  return (
    <footer className="border-t bg-muted/50">
      <div className="container py-8">
        <div className="flex flex-col items-center justify-center gap-4 text-center">
          <h3 className="text-lg font-semibold">Saarthi.AI</h3>
          <p className="text-sm text-muted-foreground">
            AI-Powered Public Service Assistant
          </p>
          <p className="text-xs text-muted-foreground">
            Built for AI for Bharat Hackathon
          </p>
        </div>
      </div>
    </footer>
  );
}
