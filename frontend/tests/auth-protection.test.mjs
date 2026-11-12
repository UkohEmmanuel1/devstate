import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

test("Next.js Proxy protects all routes except landing, sign-in and sign-up", () => {
  const proxy = read("../proxy.ts");
  assert.match(proxy, /clerkMiddleware\(/);
  assert.match(proxy, /pathname === "\/"/);
  assert.match(proxy, /pathname === "\/sign-in"/);
  assert.match(proxy, /pathname.startsWith\("\/sign-in\/"\)/);
  assert.match(proxy, /pathname === "\/sign-up"/);
  assert.match(proxy, /pathname.startsWith\("\/sign-up\/"\)/);
  assert.match(proxy, /if\s*\(!isPublicPath\(request\.nextUrl\.pathname\)\)\s*\{\s*await auth\.protect\(\)/);
});

test("protected server layouts independently require a Clerk session", () => {
  for (const path of ["../src/app/dashboard/layout.tsx", "../src/app/infrastructure/layout.tsx"]) {
    const layout = read(path);
    assert.match(layout, /await auth\(\)/);
    assert.match(layout, /if\s*\(!userId\)\s*redirect\("\/sign-in"\)/);
  }
});

test("same-origin backend proxy requires Clerk auth and forwards the token server-side", () => {
  const proxy = read("../src/app/api/backend/[...path]/route.ts");
  assert.match(proxy, /import\s*\{\s*auth\s*\}\s*from\s*"@clerk\/nextjs\/server"/);
  assert.match(proxy, /const\s*\{\s*userId\s*,\s*getToken\s*\}\s*=\s*await auth\(\)/);
  assert.match(proxy, /if\s*\(!userId\)[\s\S]*?status:\s*401/);
  assert.match(proxy, /token\s*=\s*await getToken\(\)/);
  assert.match(proxy, /status:\s*503/);
  assert.match(proxy, /Authorization:\s*"Bearer "\s*\+\s*token/);
  assert.doesNotMatch(proxy, /NEXT_PUBLIC_CLERK_SECRET_KEY/);
});

test("frontend example documents server-only Clerk secret key", () => {
  const envExample = read("../.env.example");
  assert.match(envExample, /^CLERK_SECRET_KEY=/m);
  assert.doesNotMatch(envExample, /^NEXT_PUBLIC_CLERK_SECRET_KEY=/m);
});
