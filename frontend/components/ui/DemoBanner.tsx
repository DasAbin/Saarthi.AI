"use client";

import { useState } from "react";
import { AlertCircle, X } from "lucide-react";

export function DemoBanner() {
    const [isVisible, setIsVisible] = useState(true);

    // If the API Gateway URL is set, we are connected to the real backend, so hide the banner
    if (process.env.NEXT_PUBLIC_API_GATEWAY_URL || !isVisible) {
        return null;
    }

    return (
        <div className="bg-yellow-100 border-b border-yellow-200 px-4 py-3 flex items-start sm:items-center justify-between z-50">
            <div className="flex items-center space-x-3 max-w-7xl mx-auto w-full">
                <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                <p className="text-sm font-medium text-yellow-800">
                    ⚠️ Running in demo mode — connect to AWS for full functionality. Set <code className="bg-yellow-200 px-1 py-0.5 rounded text-xs font-mono">NEXT_PUBLIC_API_GATEWAY_URL</code> in your environment variables.
                </p>
            </div>
            <button
                onClick={() => setIsVisible(false)}
                className="text-yellow-600 hover:text-yellow-800 focus:outline-none focus:ring-2 focus:ring-yellow-600 rounded p-1"
                aria-label="Dismiss demo banner"
            >
                <X className="h-5 w-5" />
            </button>
        </div>
    );
}
