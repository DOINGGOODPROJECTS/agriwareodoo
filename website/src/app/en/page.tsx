import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { HomeView } from "@/views/HomeView";

const dict = getDictionary("en");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.home.title,
  description: dict.meta.home.description,
  path: "/en",
  locale: "en_US",
});

export default function Page() {
  return (
    <PageShell lang="en" dict={dict}>
      <HomeView lang="en" dict={dict} />
    </PageShell>
  );
}
