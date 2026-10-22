import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { ContactView } from "@/views/ContactView";

const dict = getDictionary("en");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.contact.title,
  description: dict.meta.contact.description,
  path: "/en/contact",
  locale: "en_US",
});

export default function Page() {
  return (
    <PageShell lang="en" dict={dict}>
      <ContactView dict={dict} />
    </PageShell>
  );
}
