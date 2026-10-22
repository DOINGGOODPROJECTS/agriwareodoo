import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { ServicesView } from "@/views/ServicesView";

const dict = getDictionary("en");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.services.title,
  description: dict.meta.services.description,
  path: "/en/services",
  locale: "en_US",
});

export default function Page() {
  return (
    <PageShell lang="en" dict={dict}>
      <ServicesView lang="en" dict={dict} />
    </PageShell>
  );
}
