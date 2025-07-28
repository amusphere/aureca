'use client';

import { useEffect } from 'react';
import { useDemo } from '@/components/contexts/DemoContext';
import { DemoTaskListWrapper } from '@/components/components/demo/DemoTaskListWrapper';
import { DemoLimitationBanner } from '@/components/components/demo/DemoLimitationBanner';
import { Button } from '@/components/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/components/ui/card';
import { RefreshCw, ArrowRight, BrainCircuitIcon } from 'lucide-react';
import Link from 'next/link';

export default function DemoPage() {
  const { state, initializeSession, resetSession } = useDemo();

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  if (state.isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 sm:h-12 sm:w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-sm sm:text-base text-muted-foreground">デモ環境を準備中...</p>
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">エラーが発生しました</CardTitle>
            <CardDescription>{state.error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={initializeSession} className="w-full">
              再試行
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー - レスポンシブ対応 */}
      <header className="border-b bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-3 sm:px-4 lg:px-8 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-3">
            {/* ロゴとタイトル - モバイル対応 */}
            <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                <BrainCircuitIcon className="w-4 h-4 sm:w-5 sm:h-5 text-primary-foreground" />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="text-base sm:text-xl font-semibold text-foreground truncate">
                  <span className="hidden sm:inline">タスク管理システム </span>
                  <span className="sm:hidden">タスク管理 </span>
                  <span className="text-primary">デモ版</span>
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground hidden sm:block">
                  認証なしで主要機能をお試しいただけます
                </p>
              </div>
            </div>

            {/* アクションボタン - モバイル対応 */}
            <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={resetSession}
                className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3"
              >
                <RefreshCw className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="hidden sm:inline">リセット</span>
              </Button>
              <Link href="/">
                <Button size="sm" className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3">
                  <span className="text-xs sm:text-sm">
                    <span className="hidden sm:inline">本格利用を開始</span>
                    <span className="sm:hidden">登録</span>
                  </span>
                  <ArrowRight className="h-3 w-3 sm:h-4 sm:w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* 制限事項バナー */}
      <DemoLimitationBanner />

      {/* メインコンテンツ - レスポンシブ対応 */}
      <div className="relative h-full bg-background">
        <main className="h-full overflow-y-auto">
          <div className="container mx-auto px-3 sm:px-4 lg:px-8 py-4 sm:py-6 lg:py-8 pb-16 sm:pb-24">
            <div className="max-w-6xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
              {/* タスクリスト - 本番と同じコンポーネントを使用 */}
              <DemoTaskListWrapper />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}