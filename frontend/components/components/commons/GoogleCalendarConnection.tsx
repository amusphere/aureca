"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { CheckCircle, ExternalLink, XCircle } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

interface GoogleConnectionStatus {
  connected: boolean;
  user_id?: number;
  error?: string;
}

export default function GoogleCalendarConnection() {
  const [status, setStatus] = useState<GoogleConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [disconnecting, setDisconnecting] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL パラメータをチェックして通知を表示
  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");

    if (connected === "true") {
      toast.success("Googleアカウントが正常に連携されました。");
      // URL パラメータをクリア
      router.replace("/home", { scroll: false });
    } else if (error) {
      toast.error(`Google連携でエラーが発生しました: ${decodeURIComponent(error)}`);
      // URL パラメータをクリア
      router.replace("/home", { scroll: false });
    }
  }, [searchParams, router]);

  // 連携状況を取得
  const fetchConnectionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/auth/google/status");
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error("Failed to fetch Google connection status:", error);
      setStatus({ connected: false, error: "状態の取得に失敗しました" });
    } finally {
      setLoading(false);
    }
  };

  // 初回ロード時に状況を取得
  useEffect(() => {
    fetchConnectionStatus();
  }, []);

  // Google認証を開始
  const handleConnect = () => {
    window.location.href = "/api/auth/google";
  };

  // Google連携を解除
  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const response = await fetch("/api/auth/google/disconnect", {
        method: "DELETE",
      });
      const data = await response.json();

      if (data.success) {
        toast.success("Googleアカウントの連携が解除されました。");
        setStatus({ connected: false });
      } else {
        throw new Error(data.error || "連携解除に失敗しました");
      }
    } catch (error) {
      console.error("Failed to disconnect Google account:", error);
      toast.error("連携解除中にエラーが発生しました。");
    } finally {
      setDisconnecting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Google Calendar 連携</CardTitle>
          <CardDescription>
            Google Calendarとの連携状況を確認しています...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse h-10 bg-gray-200 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Google Calendar 連携
          {status?.connected ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
        </CardTitle>
        <CardDescription>
          {status?.connected
            ? "Google Calendarとの連携が有効です"
            : "Google Calendarと連携してスケジュール管理を行いましょう"
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        {status?.connected ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Google Calendarへのアクセスが許可されています。
              カレンダーイベントの読み取りと作成が可能です。
            </p>
            <Button
              variant="outline"
              onClick={handleDisconnect}
              disabled={disconnecting}
            >
              {disconnecting ? "解除中..." : "連携を解除"}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Google Calendarと連携することで、スケジュール管理機能を利用できます。
            </p>
            {status?.error && (
              <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                エラー: {status.error}
              </div>
            )}
            <Button onClick={handleConnect} className="flex items-center gap-2">
              <ExternalLink className="h-4 w-4" />
              Google アカウントと連携
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
