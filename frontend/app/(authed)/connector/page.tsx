import IntegrationsPage from "@/components/pages/IntegrationsPage";
import { Suspense } from "react";


export default function ConnectorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <IntegrationsPage />
    </Suspense>
  );
};
