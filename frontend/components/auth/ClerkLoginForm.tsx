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
      <section className="pt-24 pb-20 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="space-y-10">
            <div className="space-y-6">
              <h1 className="text-6xl sm:text-7xl font-bold text-gray-900 tracking-tight leading-tight">
                AIが変える
                <br />
                <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  タスク管理
                </span>
              </h1>
              <p className="text-xl sm:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed font-light">
                カレンダーやメールと連携し、AIがあなたの生産性を最大化します。
              </p>
            </div>

            <div className="flex justify-center">
              <SignInButton mode="modal">
                <Button size="lg" className="bg-gray-900 hover:bg-gray-800 text-white px-10 py-4 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200">
                  無料で始める
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Button>
              </SignInButton>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              すべてが一つの場所に
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              散らばったタスクを統合し、AIの力で効率的に管理
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-10 rounded-3xl border border-blue-100 hover:shadow-lg transition-all duration-300 group">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
                <SparklesIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                AI自動生成
              </h3>
              <p className="text-gray-700 leading-relaxed text-lg">
                「明日の会議の準備をする」と入力するだけで、AIが具体的なタスクリストを自動生成
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-10 rounded-3xl border border-green-100 hover:shadow-lg transition-all duration-300 group">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
                <div className="flex items-center gap-1">
                  <CalendarIcon className="w-7 h-7 text-white" />
                  <MailIcon className="w-7 h-7 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                スマート連携
              </h3>
              <p className="text-gray-700 leading-relaxed text-lg">
                カレンダーやメールから自動でタスクを抽出。重要な予定を見逃しません
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-violet-50 p-10 rounded-3xl border border-purple-100 hover:shadow-lg transition-all duration-300 group">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
                <ZapIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                自然言語処理
              </h3>
              <p className="text-gray-700 leading-relaxed text-lg">
                複雑なコマンドは不要。普段の言葉でタスクを管理し、AIが意図を理解します
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              なぜ{appName}なのか
            </h2>
          </div>

          <div className="space-y-10">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-6">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-500 rounded-2xl flex items-center justify-center flex-shrink-0">
                <CheckIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  時間を節約
                </h3>
                <p className="text-gray-700 text-lg leading-relaxed">
                  手動でのタスク入力や整理にかかる時間を大幅に削減。AIが自動で最適化します。
                </p>
              </div>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-6">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-500 rounded-2xl flex items-center justify-center flex-shrink-0">
                <CheckIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  見逃しを防止
                </h3>
                <p className="text-gray-700 text-lg leading-relaxed">
                  メールや予定から重要なタスクを自動抽出。大切な締切を見逃すことがありません。
                </p>
              </div>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-6">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-500 rounded-2xl flex items-center justify-center flex-shrink-0">
                <CheckIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  直感的な操作
                </h3>
                <p className="text-gray-700 text-lg leading-relaxed">
                  複雑な設定は不要。自然な日本語でタスクを管理し、すぐに使い始められます。
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-gray-900 via-gray-800 to-black">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="space-y-10">
            <div className="space-y-6">
              <h2 className="text-5xl sm:text-6xl font-bold text-white leading-tight">
                今すぐ始めましょう
              </h2>
              <p className="text-xl sm:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed font-light">
                無料で{appName}を体験し、AIがもたらす生産性の向上を実感してください
              </p>
            </div>

            <div className="flex justify-center">
              <SignInButton mode="modal">
                <Button size="lg" className="bg-white hover:bg-gray-100 text-gray-900 px-12 py-5 text-xl font-semibold rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105">
                  無料アカウント作成
                  <ArrowRightIcon className="w-6 h-6 ml-3" />
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

            <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-8 text-sm text-gray-600">
              <a
                href="/terms-of-service"
                className="hover:text-gray-900 transition-colors duration-200"
              >
                利用規約
              </a>
              <a
                href="/privacy-policy"
                className="hover:text-gray-900 transition-colors duration-200"
              >
                プライバシーポリシー
              </a>
              <a
                href="/legal-notice"
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