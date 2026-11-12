import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

test("landing, sign-in and sign-up are the only public application routes", () => {
  const middleware = read("../middleware.ts");
  assert.match(middleware, /createRouteMatcher\(\[.*?"\/".*?"\/sign-in\(\.\*\)".*?"\/sign-up\(\.\*\)"/s);
  assert.match(middleware, /if\s*\(!isPublic\(req\)\)\s*await auth\.protect\(\)/);
});

test("same-origin backend proxy requires Clerk auth and forwards the token server-side", () => {
  const proxy = read("../src/app/api/backend/[...path]/route.ts");
  assert.match(proxy, /import\s*\{\s*auth\s*\}\s*from\s*"@clerk\/nextjs\/server"/);
  assert.match(proxy, /const\s*\{\s*userId\s*,\s*getToken\s*\}=await auth\(\)/);
  assert.match(proxy, /if\(!userId\)[\s\S]*?status:401/);
  assert.match(proxy, /const token=await getToken\(\)/);
  assert.match(proxy, /Authorization:"Bearer "\+token/);
  assert.doesNotMatch(proxy, /NEXT_PUBLIC_CLERK_SECRET_KEY/);
});

test("frontend example documents server-only Clerk secret key", () => {
  const envExample = read("../.env.example");
  assert.match(envExample, /^CLERK_SECRET_KEY=/m);
  assert.doesNotMatch(envExample, /^NEXT_PUBLIC_CLERK_SECRET_KEY=/m);
});
