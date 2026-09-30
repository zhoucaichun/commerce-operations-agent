import { NextResponse } from "next/server";

import { postToCommerceEndpoint } from "../../../../../lib/commerce-agent";

export async function GET(_: Request, { params }: { params: Promise<{ merchantId: string }> }) {
  const { merchantId } = await params;
  try {
    const result = await postToCommerceEndpoint(`/api/v1/widget/config/${encodeURIComponent(merchantId)}`, undefined, "GET");
    return NextResponse.json(result.data, { status: result.status });
  } catch (error) {
    return NextResponse.json({ detail: error instanceof Error ? error.message : "Widget service unavailable" }, { status: 502 });
  }
}
