import { Suspense } from "react";
import IntegrationSettingsPage from "@/components/pages/IntegrationSettingsPage";

function SettingsPageContent() {
  return <IntegrationSettingsPage />;
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SettingsPageContent />
    </Suspense>
  );
};
