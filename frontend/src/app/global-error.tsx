"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("DevState application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0b1018] text-slate-100">
        <main className="grid min-h-screen place-items-center px-6 py-12">
          <section
            role="alert"
            className="w-full max-w-lg rounded-2xl border border-[#34445a] bg-[#111923] p-8 text-center"
          >
            <p className="font-mono text-xs tracking-[0.25em] text-blue-300">
              DEVSTATE · APPLICATION ERROR
            </p>
            <h1 className="mt-4 text-2xl font-bold">DevState could not start</h1>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              An unexpected application error interrupted this page. You can try loading it again.
            </p>
            {error.digest ? (
              <p className="mt-3 font-mono text-xs text-slate-500">
                Reference: {error.digest}
              </p>
            ) : null}
            <button
              type="button"
              onClick={() => reset()}
              className="mt-6 rounded-lg bg-blue-400 px-5 py-3 text-sm font-semibold text-slate-950"
            >
              Try again
            </button>
          </section>
        </main>
      </body>
    </html>
  );
}
