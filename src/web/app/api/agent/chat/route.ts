import { NextRequest, NextResponse } from "next/server";

import { postToCommerceAgent } from "../../../../lib/commerce-agent";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const result = await postToCommerceAgent(body);
    return NextResponse.json(result.data, { status: result.status });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to connect to Commerce Agent",
        detail: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 502 }
    );
  }
}
