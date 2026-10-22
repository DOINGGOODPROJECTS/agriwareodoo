import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { DocumentationView } from "@/views/DocumentationView";

const dict = getDictionary("fr");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.documentation.title,
  description: dict.meta.documentation.description,
  path: "/documentation",
  locale: "fr_FR",
});

export default function Page() {
  return (
    <PageShell lang="fr" dict={dict}>
      <DocumentationView dict={dict} />
    </PageShell>
  );
}
