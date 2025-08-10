import { PricingTable } from "@clerk/nextjs";

export default function SubscriptionPage() {
  return (
    <div className="px-2">
      <div className="pt-6 mb-4">
        <h1 className="text-3xl font-bold">Subscription Plans</h1>
      </div>
      <PricingTable />
    </div>
  );
}
