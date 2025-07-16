import IntegrationSettingsPage from "@/components/pages/IntegrationSettingsPage";

// Force dynamic rendering since this route uses cookies for auth
export const dynamic = 'force-dynamic';

export default function SettingsPage() {
  return <IntegrationSettingsPage />;
};
