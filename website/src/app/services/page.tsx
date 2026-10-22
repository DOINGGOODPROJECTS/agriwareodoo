import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { ServicesView } from "@/views/ServicesView";

const dict = getDictionary("fr");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.services.title,
  description: dict.meta.services.description,
  path: "/services",
  locale: "fr_FR",
});

export default function Page() {
  return (
    <PageShell lang="fr" dict={dict}>
      <ServicesView lang="fr" dict={dict} />
    </PageShell>
  );
}
