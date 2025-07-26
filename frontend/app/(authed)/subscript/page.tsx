"use client";

import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import { Badge } from "@/components/components/ui/badge";
import { Check, Sparkles, Zap, MessageSquare, Calendar, Mail, Brain } from "lucide-react";

export default function SubscriptionPage() {
  const handleUpgrade = (plan: string) => {
    // TODO: Implement actual upgrade logic
    console.log(`Upgrading to ${plan} plan`);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">
          AI機能でタスク管理を次のレベルへ
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          有料プランにアップグレードして、AI アシスタント機能を使ってタスク管理を効率化しましょう
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {/* Free Plan */}
        <Card className="relative">
          <CardHeader>
            <CardTitle className="text-2xl">フリープラン</CardTitle>
            <CardDescription>基本的なタスク管理機能</CardDescription>
            <div className="text-3xl font-bold">¥0<span className="text-base font-normal">/月</span></div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Check className="h-4 w-4 text-green-500" />
                <span className="text-sm">基本的なタスク作成・管理</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="h-4 w-4 text-green-500" />
                <span className="text-sm">カレンダー連携</span>
              </div>
              <div className="flex items-center space-x-2">
                <Check className="h-4 w-4 text-green-500" />
                <span className="text-sm">基本的な通知機能</span>
              </div>
            </div>
            <Button variant="outline" className="w-full" disabled>
              現在のプラン
            </Button>
          </CardContent>
        </Card>

        {/* Pro Plan */}
        <Card className="relative border-primary shadow-lg">
          <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
            <Badge className="bg-primary text-primary-foreground px-3 py-1">
              おすすめ
            </Badge>
          </div>
          <CardHeader>
            <CardTitle className="text-2xl flex items-center">
              プロプラン
              <Sparkles className="ml-2 h-5 w-5 text-primary" />
            </CardTitle>
            <CardDescription>AI機能でスマートなタスク管理</CardDescription>
            <div className="text-3xl font-bold">¥980<span className="text-base font-normal">/月</span></div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Check className="h-4 w-4 text-green-500" />
                <span className="text-sm">フリープランの全機能</span>
              </div>
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">自然言語でタスク作成</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">スマートなスケジュール提案</span>
              </div>
              <div className="flex items-center space-x-2">
                <Mail className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium">メール自動解析</span>
              </div>
              <div className="flex items-center space-x-2">
                <Brain className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium">優先度の自動判定</span>
              </div>
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">高度なAIアシスタント</span>
              </div>
            </div>
            <Button onClick={() => handleUpgrade('pro')} className="w-full">
              <Sparkles className="mr-2 h-4 w-4" />
              プロプランにアップグレード
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Feature Details */}
      <div className="mt-16">
        <h2 className="text-3xl font-bold text-center mb-8">AI機能の詳細</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="text-center">
              <MessageSquare className="h-8 w-8 text-blue-500 mx-auto mb-2" />
              <CardTitle className="text-lg">自然言語でタスク作成</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center">
                「明日の会議の資料を準備する」と話すだけで、適切な期限と詳細を持つタスクが自動作成されます
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Calendar className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <CardTitle className="text-lg">スマートスケジュール</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center">
                カレンダーの空き時間を分析して、最適なタスクの実行時間を自動提案します
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Mail className="h-8 w-8 text-purple-500 mx-auto mb-2" />
              <CardTitle className="text-lg">メール自動解析</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center">
                重要なメールから自動でアクションアイテムを抽出し、タスクとして追加します
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <Brain className="h-8 w-8 text-orange-500 mx-auto mb-2" />
              <CardTitle className="text-lg">優先度自動判定</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground text-center">
                AIがタスクの重要度と緊急度を分析し、最適な優先順位を自動設定します
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
