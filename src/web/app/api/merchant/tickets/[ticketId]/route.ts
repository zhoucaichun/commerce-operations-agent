import { NextRequest, NextResponse } from "next/server";
import { postToCommerceEndpoint } from "../../../../../lib/commerce-agent";

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  try {
    const result = await postToCommerceEndpoint(`/api/v1/demo/console/tickets/${encodeURIComponent(ticketId)}`, await request.json(), "PATCH");
    return NextResponse.json(result.data, { status: result.status });
  } catch (error) {
    return NextResponse.json({ detail: error instanceof Error ? error.message : "Merchant service unavailable" }, { status: 502 });
  }
}
