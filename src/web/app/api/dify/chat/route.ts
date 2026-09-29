import { NextRequest, NextResponse } from "next/server";
import { postToDify } from "../../../../lib/dify";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = await postToDify(body);

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to connect to Dify",
        detail: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}
