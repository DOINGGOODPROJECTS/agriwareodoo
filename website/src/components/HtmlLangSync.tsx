"use client";

import { useEffect } from "react";
import type { Lang } from "@/types/content";

/**
 * The root layout's <html> tag is shared by every route (French default,
 * unprefixed; English under /en), so its `lang` attribute can't vary by
 * route on the server during static export. This corrects it client-side
 * on mount so assistive tech reading a live page gets the right value;
 * the initial static HTML byte still says "fr" until this runs.
 */
export function HtmlLangSync({ lang }: { lang: Lang }) {
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return null;
}
