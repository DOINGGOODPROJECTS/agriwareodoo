import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { HomeView } from "@/views/HomeView";

const dict = getDictionary("fr");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.home.title,
  description: dict.meta.home.description,
  path: "/",
  locale: "fr_FR",
});

export default function Page() {
  return (
    <PageShell lang="fr" dict={dict}>
      <HomeView lang="fr" dict={dict} />
    </PageShell>
  );
}
