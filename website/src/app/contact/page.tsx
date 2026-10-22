import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { ContactView } from "@/views/ContactView";

const dict = getDictionary("fr");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.contact.title,
  description: dict.meta.contact.description,
  path: "/contact",
  locale: "fr_FR",
});

export default function Page() {
  return (
    <PageShell lang="fr" dict={dict}>
      <ContactView dict={dict} />
    </PageShell>
  );
}
