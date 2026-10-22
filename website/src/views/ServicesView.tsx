import Link from "next/link";
import type { Dictionary, Lang } from "@/types/content";

function withLang(path: string, lang: Lang): string {
  return lang === "en" ? `/en${path}` : path;
}

export function ServicesView({ lang, dict }: { lang: Lang; dict: Dictionary }) {
  const d = dict.services;

  return (
    <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-gray-900">{d.title}</h1>
      <p className="mt-3 text-lg text-gray-600">{d.intro}</p>
      <p className="mt-4 rounded-md bg-brand-50 px-4 py-3 text-sm font-medium text-brand-800">
        {d.freeNote}
      </p>

      <ul className="mt-10 space-y-6">
        {d.packages.map((pkg) => (
          <li key={pkg.name} className="rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900">{pkg.name}</h2>
            <p className="mt-2 text-gray-700">{pkg.description}</p>
          </li>
        ))}
      </ul>

      <div className="mt-10 space-y-2 text-sm text-gray-500">
        <p>{d.optionalNote}</p>
        <p>{d.noPricingNote}</p>
      </div>

      <Link
        href={withLang("/contact", lang)}
        className="mt-8 inline-block rounded-md bg-brand-600 px-6 py-3 text-base font-semibold text-white hover:bg-brand-700"
      >
        {d.cta}
      </Link>
    </div>
  );
}
