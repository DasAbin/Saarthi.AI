import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { DemoBanner } from "@/components/ui/DemoBanner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Saarthi.AI - AI-Powered Public Service Assistant",
  description:
    "Multilingual civic information, government scheme discovery, PDF policy analysis, voice interaction, and community grievance automation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          <div className="flex min-h-screen flex-col">
            <DemoBanner />
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
          <Toaster />
        </ErrorBoundary>
      </body>
    </html>
  );
}
