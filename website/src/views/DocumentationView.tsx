import type { Dictionary } from "@/types/content";

export function DocumentationView({ dict }: { dict: Dictionary }) {
  const d = dict.documentation;

  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-gray-900">{d.title}</h1>
      <p className="mt-3 text-lg text-gray-600">{d.intro}</p>

      <ul className="mt-10 space-y-4">
        {d.links.map((link) => (
          <li key={link.href} className="rounded-lg border border-gray-200 p-5">
            <a
              href={link.href}
              target={link.external ? "_blank" : undefined}
              rel={link.external ? "noopener noreferrer" : undefined}
              className="text-base font-semibold text-brand-700 underline"
            >
              {link.label}
            </a>
            <p className="mt-1 text-sm text-gray-600">{link.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
