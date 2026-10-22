import type { Dictionary, Lang } from "@/types/content";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { HtmlLangSync } from "./HtmlLangSync";

export function PageShell({
  lang,
  dict,
  children,
}: {
  lang: Lang;
  dict: Dictionary;
  children: React.ReactNode;
}) {
  return (
    <>
      <HtmlLangSync lang={lang} />
      <Header lang={lang} dict={dict} />
      <main>{children}</main>
      <Footer lang={lang} dict={dict} />
    </>
  );
}
