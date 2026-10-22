"use client";

import { useState } from "react";
import type { Dictionary } from "@/types/content";

type FormState = {
  companyName: string;
  contactName: string;
  email: string;
  country: string;
  existingErp: string;
  existingWms: string;
  requiredIntegration: string;
  projectDescription: string;
};

const initialState: FormState = {
  companyName: "",
  contactName: "",
  email: "",
  country: "",
  existingErp: "",
  existingWms: "",
  requiredIntegration: "",
  projectDescription: "",
};

export function ContactView({ dict }: { dict: Dictionary }) {
  const d = dict.contact;
  const [form, setForm] = useState<FormState>(initialState);

  const update =
    (field: keyof FormState) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  // Submission is intentionally disabled: no backend or authorized form
  // provider is configured yet. This handler exists only to prevent a
  // native page reload if the disabled button is somehow triggered; it
  // does not send, store, or log any field value anywhere.
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold text-gray-900">{d.title}</h1>
      <p className="mt-3 text-lg text-gray-600">{d.intro}</p>

      <div
        role="alert"
        className="mt-8 rounded-lg border border-amber-300 bg-amber-50 p-4"
      >
        <p className="font-semibold text-amber-900">{d.formDisabledTitle}</p>
        <p className="mt-1 text-sm text-amber-800">{d.formDisabledBody}</p>
        <p className="mt-2 text-sm text-amber-800">{d.alternateContact}</p>
      </div>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit} noValidate={false}>
        <div>
          <label htmlFor="companyName" className="block text-sm font-medium text-gray-700">
            {d.fields.companyName}
          </label>
          <input
            id="companyName"
            name="companyName"
            type="text"
            required
            value={form.companyName}
            onChange={update("companyName")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div>
          <label htmlFor="contactName" className="block text-sm font-medium text-gray-700">
            {d.fields.contactName}
          </label>
          <input
            id="contactName"
            name="contactName"
            type="text"
            required
            value={form.contactName}
            onChange={update("contactName")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            {d.fields.email}
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={form.email}
            onChange={update("email")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div>
          <label htmlFor="country" className="block text-sm font-medium text-gray-700">
            {d.fields.country}
          </label>
          <input
            id="country"
            name="country"
            type="text"
            required
            value={form.country}
            onChange={update("country")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label htmlFor="existingErp" className="block text-sm font-medium text-gray-700">
              {d.fields.existingErp}
            </label>
            <input
              id="existingErp"
              name="existingErp"
              type="text"
              value={form.existingErp}
              onChange={update("existingErp")}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label htmlFor="existingWms" className="block text-sm font-medium text-gray-700">
              {d.fields.existingWms}
            </label>
            <input
              id="existingWms"
              name="existingWms"
              type="text"
              value={form.existingWms}
              onChange={update("existingWms")}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="requiredIntegration" className="block text-sm font-medium text-gray-700">
            {d.fields.requiredIntegration}
          </label>
          <input
            id="requiredIntegration"
            name="requiredIntegration"
            type="text"
            value={form.requiredIntegration}
            onChange={update("requiredIntegration")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div>
          <label htmlFor="projectDescription" className="block text-sm font-medium text-gray-700">
            {d.fields.projectDescription}
          </label>
          <textarea
            id="projectDescription"
            name="projectDescription"
            rows={5}
            value={form.projectDescription}
            onChange={update("projectDescription")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <button
          type="submit"
          disabled
          aria-disabled="true"
          title={d.formDisabledTitle}
          className="w-full cursor-not-allowed rounded-md bg-gray-300 px-6 py-3 text-base font-semibold text-gray-600"
        >
          {d.submit}
        </button>
      </form>

      <div className="mt-10 border-t border-gray-200 pt-6">
        <h2 className="text-base font-semibold text-gray-900">{d.privacyTitle}</h2>
        <p className="mt-2 text-sm text-gray-600">{d.privacyBody}</p>
      </div>
    </div>
  );
}
