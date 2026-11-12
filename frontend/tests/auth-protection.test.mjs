import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const read = (path) => readFileSync(resolve(process.cwd(), path), "utf8");

test("only landing, sign-in and sign-up routes are public", () => {
  const middleware = read("middleware.ts");
  assert.match(middleware, /createRouteMatcher\(\[.*?"\/".*?"\/sign-in\(\.\*\)".*?"\/sign-up\(\.\*\)"/s);
  assert.match(middleware, /if\s*\(!isPublic\(req\)\)\s*await auth\.protect\(\)/);
});

test("backend API proxy requires a Clerk session and forwards its token server-side", () => {
  const proxy = read("src/app/api/backend/[...path]/route.ts");
  assert.match(proxy, /import\s*\{\s*auth\s*\}\s*from\s*"@clerk\/nextjs\/server"/);
  assert.match(proxy, /const\s*\{\s*userId\s*,\s*getToken\s*\}\s*=\s*await auth\(\)/);
  assert.match(proxy, /if\s*\(!userId\)[\s\S]*?status:\s*401/);
  assert.match(proxy, /const\s+token\s*=\s*await getToken\(\)/);
  assert.match(proxy, /Authorization:\s*"Bearer "\s*\+\s*token/);
  assert.doesNotMatch(proxy, /NEXT_PUBLIC_CLERK_SECRET_KEY/);
});
