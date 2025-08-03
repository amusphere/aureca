"use client";

import { useAIChatUsage } from "@/components/hooks/useAIChatUsage";
import { Badge } from "@/components/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Button } from "@/components/components/ui/button";
import { AlertCircle, RefreshCw } from "lucide-react";

/**
 * Component to display AI Chat usage information
 * Used for testing and debugging the useAIChatUsage hook
 *
 * Requirements covered:
 * - 4.1: Display remaining usage count and daily limit
 * - 4.2: Show usage status and restrictions
 * - 5.1: Display error messages
 * - 5.2: Real-time updates and refresh functionality
 */
export function AIChatUsageDisplay() {
  const {
    usage,
    loading,
    error,
    canUseChat,
    isUsageExhausted,
    checkUsage,
    refreshUsage,
    incrementUsage,
    clearError
  } = useAIChatUsage();

  const handleTestIncrement = async () => {
    const result = await incrementUsage();
    console.log('Increment result:', result);
  };

  if (loading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            AI Chat 利用状況
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">読み込み中...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-md border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            エラー
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-destructive">{error.error}</p>
          <p className="text-xs text-muted-foreground">
            エラーコード: {error.errorCode}
          </p>
          <p className="text-xs text-muted-foreground">
            リセット時刻: {new Date(error.resetTime).toLocaleString('ja-JP')}
          </p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={clearError}>
              エラーをクリア
            </Button>
            <Button size="sm" onClick={refreshUsage}>
              再試行
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!usage) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>AI Chat 利用状況</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">利用状況を取得できませんでした</p>
          <Button size="sm" className="mt-2" onClick={checkUsage}>
            再読み込み
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          AI Chat 利用状況
          <Badge variant={canUseChat ? "default" : "destructive"}>
            {canUseChat ? "利用可能" : "利用不可"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Usage Statistics */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">残り回数:</span>
            <span className={`text-sm font-bold ${isUsageExhausted ? 'text-destructive' : 'text-primary'}`}>
              {usage.remainingCount} / {usage.dailyLimit}
            </span>
          </div>

          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                isUsageExhausted ? 'bg-destructive' : 'bg-primary'
              }`}
              style={{
                width: `${Math.max(0, (usage.remainingCount / usage.dailyLimit) * 100)}%`
              }}
            />
          </div>
        </div>

        {/* Reset Time */}
        <div className="text-xs text-muted-foreground">
          リセット時刻: {new Date(usage.resetTime).toLocaleString('ja-JP')}
        </div>

        {/* Status Messages */}
        {isUsageExhausted && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-sm text-destructive font-medium">
              本日の利用回数上限に達しました
            </p>
            <p className="text-xs text-destructive/80 mt-1">
              明日の00:00にリセットされます
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={refreshUsage}>
            <RefreshCw className="h-3 w-3 mr-1" />
            更新
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleTestIncrement}
            disabled={!canUseChat}
          >
            テスト実行
          </Button>
        </div>

        {/* Debug Information */}
        {process.env.NODE_ENV === 'development' && (
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground">
              デバッグ情報
            </summary>
            <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto">
              {JSON.stringify({ usage, canUseChat, isUsageExhausted }, null, 2)}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  );
}