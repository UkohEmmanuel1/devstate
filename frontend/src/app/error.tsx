"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("DevState route error:", error);
  }, [error]);

  return (
    <main className="grid min-h-screen place-items-center px-6 py-12">
      <section
        role="alert"
        className="w-full max-w-lg rounded-2xl border border-[#34445a] bg-[#111923] p-8 text-center"
      >
        <div className="mx-auto grid size-12 place-items-center rounded-xl bg-amber-400/10 text-amber-300">
          <AlertTriangle aria-hidden="true" size={22} />
        </div>
        <h1 className="mt-5 text-xl font-semibold">Something went wrong</h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          DevState could not load this page. Your data has not been intentionally changed.
          Try again, or return to the dashboard.
        </p>
        {error.digest ? (
          <p className="mt-3 font-mono text-xs text-slate-500">
            Reference: {error.digest}
          </p>
        ) : null}
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={() => reset()}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-400 px-4 py-2.5 text-sm font-semibold text-slate-950"
          >
            <RefreshCw size={15} aria-hidden="true" />
            Try again
          </button>
          <a
            href="/dashboard"
            className="rounded-lg border border-[#34445a] px-4 py-2.5 text-sm text-slate-200"
          >
            Dashboard
          </a>
        </div>
      </section>
    </main>
  );
}
