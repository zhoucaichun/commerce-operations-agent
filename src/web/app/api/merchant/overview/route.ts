import { NextRequest, NextResponse } from "next/server";
import { postToCommerceEndpoint } from "../../../../lib/commerce-agent";

export async function POST(request: NextRequest) {
  try {
    const result = await postToCommerceEndpoint("/api/v1/demo/console/overview", await request.json());
    return NextResponse.json(result.data, { status: result.status });
  } catch (error) {
    return NextResponse.json({ detail: error instanceof Error ? error.message : "Merchant service unavailable" }, { status: 502 });
  }
}
