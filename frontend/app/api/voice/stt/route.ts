import { NextRequest, NextResponse } from "next/server";

const API_GATEWAY_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ||
  "https://your-api-gateway-url.execute-api.region.amazonaws.com/prod";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const audio = formData.get("audio") as File;

    if (!audio) {
      return NextResponse.json(
        { success: false, message: "No audio file provided" },
        { status: 400 }
      );
    }

    const buffer = await audio.arrayBuffer();
    const base64 = Buffer.from(buffer).toString("base64");

    const response = await fetch(`${API_GATEWAY_URL}/voice/stt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        audio: base64,
        contentType: audio.type,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { success: false, message: error.message || "API error" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Internal error",
      },
      { status: 500 }
    );
  }
}
