import GoogleCalendarConnection from "../components/commons/GoogleCalendarConnection";

export default function IntegrationSettingsPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="md:col-span-2 lg:col-span-1">
          <GoogleCalendarConnection />
        </div>

        {/* 他の機能カードをここに追加できます */}
        <div className="p-6 border rounded-lg">
          <h2 className="text-xl font-semibold mb-2">その他の機能</h2>
          <p className="text-gray-600">今後追加される機能がここに表示されます。</p>
        </div>
      </div>
    </div>
  );
}
