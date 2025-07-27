import { Button } from "@/components/components/ui/button";
import { SignInButton } from "@clerk/nextjs";
import {
  ArrowRightIcon,
  BrainCircuitIcon,
  CalendarIcon,
  CheckIcon,
  MailIcon,
  SparklesIcon,
  ZapIcon
} from "lucide-react";

export default function ClerkLoginForm() {
  const appName = process.env.NEXT_PUBLIC_APP_NAME;

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
                <BrainCircuitIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-gray-900">{appName}</span>
            </div>
            <div className="flex items-center gap-4">
              <SignInButton mode="modal">
                <Button className="bg-gray-900 hover:bg-gray-800 text-white">
                  サインイン
                </Button>
              </SignInButton>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 tracking-tight">
                AIが変える
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  タスク管理
                </span>
              </h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                カレンダーやメールと連携しAIがあなたの生産性を最大化します。
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <SignInButton mode="modal">
                <Button size="lg" className="bg-gray-900 hover:bg-gray-800 text-white px-8 py-3 text-lg">
                  無料で始める
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Button>
              </SignInButton>
              <Button variant="outline" size="lg" className="px-8 py-3 text-lg">
                デモを見る
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              すべてが一つの場所に
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              散らばったタスクを統合し、AIの力で効率的に管理
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                <SparklesIcon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                AI自動生成
              </h3>
              <p className="text-gray-600 leading-relaxed">
                「明日の会議の準備をする」と入力するだけで、AIが具体的なタスクリストを自動生成
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                <div className="flex items-center gap-1">
                  <CalendarIcon className="w-5 h-5 text-green-600" />
                  <MailIcon className="w-5 h-5 text-green-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                スマート連携
              </h3>
              <p className="text-gray-600 leading-relaxed">
                カレンダーやメールから自動でタスクを抽出。重要な予定を見逃しません
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                <ZapIcon className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                自然言語処理
              </h3>
              <p className="text-gray-600 leading-relaxed">
                複雑なコマンドは不要。普段の言葉でタスクを管理し、AIが意図を理解します
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              なぜ{appName}なのか
            </h2>
          </div>

          <div className="space-y-8">
            <div className="flex items-start gap-4">
              <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <CheckIcon className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  時間を節約
                </h3>
                <p className="text-gray-600">
                  手動でのタスク入力や整理にかかる時間を大幅に削減。AIが自動で最適化します。
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <CheckIcon className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  見逃しを防止
                </h3>
                <p className="text-gray-600">
                  メールや予定から重要なタスクを自動抽出。大切な締切を見逃すことがありません。
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <CheckIcon className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  直感的な操作
                </h3>
                <p className="text-gray-600">
                  複雑な設定は不要。自然な日本語でタスクを管理し、すぐに使い始められます。
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold text-white">
                今すぐ始めましょう
              </h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                無料で{appName}を体験し、AIがもたらす生産性の向上を実感してください
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <SignInButton mode="modal">
                <Button size="lg" className="bg-white hover:bg-gray-100 text-gray-900 px-8 py-3 text-lg">
                  無料アカウント作成
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Button>
              </SignInButton>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
                <BrainCircuitIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-gray-900">{appName}</span>
            </div>

            <div className="flex items-center gap-8 text-sm text-gray-600">
              <a
                href="/privacy-policy"
                className="hover:text-gray-900 transition-colors duration-200"
              >
                プライバシーポリシー
              </a>
              <a
                href="/terms-of-service"
                className="hover:text-gray-900 transition-colors duration-200"
              >
                特定商取引法に基づく表記
              </a>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-100 text-center text-sm text-gray-500">
            © 2025 {appName}. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}