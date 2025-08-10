"use client";

import { useState } from "react";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Calendar, MessageSquare, Sparkles, Zap, X } from "lucide-react";
import { useRouter } from "next/navigation";

export function AIUpgradePrompt() {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(true);

  const handleUpgrade = () => {
    router.push("/subscript");
  };

  const handleClose = () => {
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Card className="border-2 border-dashed border-primary/20 bg-gradient-to-br from-primary/5 to-secondary/5 relative">
      <CardHeader className="text-center pb-4">
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-8 w-8 p-0 hover:bg-muted"
          onClick={handleClose}
        >
          <X className="h-4 w-4" />
        </Button>
        <CardTitle className="text-xl font-semibold">
          AI機能でタスク管理をもっと便利に！
        </CardTitle>
        <CardDescription className="text-base">
          有料プランにアップグレードして、AI アシスタント機能を使ってみませんか？
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex items-start space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
              <MessageSquare className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <h4 className="font-medium text-sm">自然言語でタスク作成</h4>
              <p className="text-xs text-muted-foreground">
                「明日の会議の資料を準備する」と話すだけでタスクが作成されます
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100">
              <Calendar className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <h4 className="font-medium text-sm">スマートなスケジュール提案</h4>
              <p className="text-xs text-muted-foreground">
                カレンダーと連携して最適なタスクの実行時間を提案
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100">
              <Zap className="h-4 w-4 text-purple-600" />
            </div>
            <div>
              <h4 className="font-medium text-sm">メール自動解析</h4>
              <p className="text-xs text-muted-foreground">
                重要なメールから自動でタスクを抽出・作成
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-100">
              <Sparkles className="h-4 w-4 text-orange-600" />
            </div>
            <div>
              <h4 className="font-medium text-sm">優先度の自動判定</h4>
              <p className="text-xs text-muted-foreground">
                AIがタスクの重要度と緊急度を分析して優先順位を提案
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <Button onClick={handleUpgrade} className="flex-1">
            <Sparkles className="mr-2 h-4 w-4" />
            有料プランにアップグレード
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}