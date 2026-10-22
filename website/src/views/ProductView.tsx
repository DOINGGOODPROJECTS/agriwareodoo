import Image from "next/image";
import type { Dictionary } from "@/types/content";

export function ProductView({ dict }: { dict: Dictionary }) {
  const d = dict.product;

  return (
    <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-gray-900">{d.title}</h1>
      <p className="mt-3 text-lg text-gray-600">{d.intro}</p>

      <section className="mt-12">
        <h2 className="text-xl font-bold text-gray-900">{d.overview.title}</h2>
        <p className="mt-2 text-gray-700">{d.overview.body}</p>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.version.title}</h2>
        <p className="mt-2 text-gray-700">{d.version.body}</p>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.architecture.title}</h2>
        <p className="mt-2 text-gray-700">{d.architecture.body}</p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 rounded-lg bg-gray-50 p-6">
          <div className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold">
            {d.architecture.diagram.wms}
          </div>
          <span className="text-xs text-gray-400">{d.architecture.diagram.api} →</span>
          <div className="rounded-md border border-brand-300 bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-800">
            {d.architecture.diagram.connector}
          </div>
          <span className="text-xs text-gray-400">ORM →</span>
          <div className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold">
            {d.architecture.diagram.odoo}
          </div>
          <span className="text-xs text-gray-400">→</span>
          <div className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold">
            {d.architecture.diagram.db}
          </div>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.api.title}</h2>
        <p className="mt-2 text-gray-700">{d.api.body}</p>
        <ul className="mt-4 space-y-2">
          {d.api.capabilities.map((item) => (
            <li key={item} className="rounded-md bg-gray-50 px-3 py-2 font-mono text-sm text-gray-800">
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.auth.title}</h2>
        <p className="mt-2 text-gray-700">{d.auth.body}</p>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.operations.title}</h2>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-gray-700">
          {d.operations.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.limitations.title}</h2>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-gray-700">
          {d.limitations.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-bold text-gray-900">{d.screenshots.title}</h2>
        <div className="mt-6 space-y-8">
          {d.screenshots.items.map((shot) => (
            <figure key={shot.src}>
              <Image
                src={shot.src}
                alt={shot.alt}
                width={1200}
                height={700}
                className="w-full rounded-lg border border-gray-200"
              />
              <figcaption className="mt-2 text-sm text-gray-500">{shot.caption}</figcaption>
            </figure>
          ))}
        </div>
      </section>
    </div>
  );
}
