import type { Metadata } from "next";
import { getDictionary } from "@/content";
import { buildMetadata } from "@/lib/metadata";
import { PageShell } from "@/components/PageShell";
import { ProductView } from "@/views/ProductView";

const dict = getDictionary("en");

export const metadata: Metadata = buildMetadata({
  title: dict.meta.product.title,
  description: dict.meta.product.description,
  path: "/en/product",
  locale: "en_US",
});

export default function Page() {
  return (
    <PageShell lang="en" dict={dict}>
      <ProductView dict={dict} />
    </PageShell>
  );
}
