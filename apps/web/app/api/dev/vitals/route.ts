import { NextResponse } from "next/server";

/**
 * Deprecated stub — vitals alerts are console-only (no HTTP beacon).
 * Returns 204 immediately so stale dev bundles do not 404 or block the server.
 */
export async function POST() {
  if (process.env.NODE_ENV !== "development") {
    return NextResponse.json({ ok: false }, { status: 404 });
  }

  return new NextResponse(null, { status: 204 });
}
