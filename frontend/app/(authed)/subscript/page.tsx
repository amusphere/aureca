"use client"

import { PricingTable } from "@clerk/nextjs";

export default function SubscriptionPage() {
  return (
    <div className="px-2">
      <style jsx global>{`
        .cl-pricingTableCardDescription {
          white-space: pre-line;
        }
      `}</style>

      <div className="pt-6 mb-4">
        <h1 className="text-3xl font-bold">プラン内容</h1>
      </div>
      <PricingTable />
    </div>
  );
}
