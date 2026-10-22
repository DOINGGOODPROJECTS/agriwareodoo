import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { DocumentationView } from "@/views/DocumentationView";

const dict = getDictionary("en");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.documentation.title,
  description: dict.meta.documentation.description,
  path: "/en/documentation",
  locale: "en_US",
});

export default function Page() {
  return (
    <PageShell lang="en" dict={dict}>
      <DocumentationView dict={dict} />
    </PageShell>
  );
}
