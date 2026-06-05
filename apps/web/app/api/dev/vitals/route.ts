import { NextResponse } from "next/server";

type VitalsPayload = {
  name?: string;
  value?: number;
  rating?: string;
  path?: string;
};

export async function POST(req: Request) {
  if (process.env.NODE_ENV !== "development") {
    return NextResponse.json({ ok: false }, { status: 404 });
  }

  let body: VitalsPayload;
  try {
    body = (await req.json()) as VitalsPayload;
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 });
  }

  const { name, value, rating, path } = body;
  if (!name || value === undefined || !rating) {
    return NextResponse.json({ ok: false }, { status: 400 });
  }

  if (rating === "needs-improvement" || rating === "poor") {
    const route = path ?? "/";
    const valueText =
      name === "CLS" ? Number(value).toFixed(4) : `${Math.round(value)}ms`;
    console.warn(
      `[WebVitals ⚠] ${route} ${name}=${valueText} (${rating})`,
    );
  }

  return NextResponse.json({ ok: true });
}
