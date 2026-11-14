import Link from "next/link";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center px-6 py-12">
      <section className="max-w-md text-center">
        <p className="font-mono text-xs tracking-[0.25em] text-blue-300">DEVSTATE · 404</p>
        <h1 className="mt-4 text-4xl font-bold">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          This route does not exist or may have moved.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-lg bg-blue-400 px-5 py-3 text-sm font-semibold text-slate-950"
        >
          Return home
        </Link>
      </section>
    </main>
  );
}
