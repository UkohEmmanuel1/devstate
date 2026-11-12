import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

const API = process.env.DEVSTATE_API_URL;
const MAX_BODY_BYTES = 1024 * 1024;

async function proxy(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  if (!API) {
    return NextResponse.json({ detail: "Backend not configured" }, { status: 503 });
  }

  const { userId, getToken } = await auth();
  if (!userId) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const token = await getToken();
  if (!token) {
    return NextResponse.json({ detail: "Clerk session token unavailable" }, { status: 401 });
  }

  const { path } = await ctx.params;
  if (
    !path.length ||
    path.some((segment) =>
      !segment || segment === "." || segment === ".." ||
      segment.includes("/") || segment.includes("\\")
    )
  ) {
    return NextResponse.json({ detail: "Invalid API path" }, { status: 400 });
  }

  let base: URL;
  let target: URL;
  try {
    base = new URL(API.endsWith("/") ? API : API + "/");
    target = new URL(
      path.map((segment) => encodeURIComponent(segment)).join("/") + req.nextUrl.search,
      base,
    );
  } catch {
    return NextResponse.json({ detail: "Backend URL is invalid" }, { status: 503 });
  }

  if (target.origin !== base.origin || !target.pathname.startsWith(base.pathname)) {
    return NextResponse.json({ detail: "Invalid API path" }, { status: 400 });
  }

  const headers = new Headers({ Authorization: "Bearer " + token });
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  let body: ArrayBuffer | undefined;
  if (!["GET", "HEAD"].includes(req.method)) {
    body = await req.arrayBuffer();
    if (body.byteLength > MAX_BODY_BYTES) {
      return NextResponse.json({ detail: "Request body is too large" }, { status: 413 });
    }
  }

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(10_000),
    });
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
