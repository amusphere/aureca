import {
  CalendarIcon,
  CheckIcon,
  MailIcon,
  MessageSquareIcon,
  SparklesIcon
} from "lucide-react";

export default function ServiceDetailSection() {
  return (
    <section id="features" className="py-16 sm:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 sm:mb-24 px-4">
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            AIがもたらす
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              革新的な体験
            </span>
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            従来のタスク管理ツールとは一線を画す、AI駆動の次世代タスク管理システムです
          </p>
        </div>

        {/* Main Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 lg:gap-12">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 sm:p-8 lg:p-10 rounded-3xl border border-blue-100 hover:shadow-lg transition-all duration-300 group">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
              <SparklesIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              AI自動生成
            </h3>
            <p className="text-gray-700 leading-relaxed text-lg mb-6">
              「明日の会議の準備をする」と入力するだけで、AIが具体的なタスクリストを自動生成。複雑なプロジェクトも瞬時に分解します。
            </p>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                自然言語からタスク自動生成
              </li>

              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                優先度の自動判定
              </li>
            </ul>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 sm:p-8 lg:p-10 rounded-3xl border border-green-100 hover:shadow-lg transition-all duration-300 group">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
              <div className="flex items-center gap-1">
                <CalendarIcon className="w-7 h-7 text-white" />
                <MailIcon className="w-7 h-7 text-white" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              マルチサービス連携
            </h3>
            <p className="text-gray-700 leading-relaxed text-lg mb-6">
              メール、カレンダー、チャットツール、既存のタスク管理ツールなど、様々なサービスと連携してタスクを一元管理できます。
            </p>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                メール・チャットからタスク抽出
              </li>
              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                カレンダー・スケジュール同期
              </li>

            </ul>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-violet-50 p-6 sm:p-8 lg:p-10 rounded-3xl border border-purple-100 hover:shadow-lg transition-all duration-300 group">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300">
              <MessageSquareIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              自然言語処理
            </h3>
            <p className="text-gray-700 leading-relaxed text-lg mb-6">
              複雑なコマンドは不要。普段の言葉でタスクを管理し、AIが意図を正確に理解して実行します。
            </p>
            <ul className="space-y-3">
              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                自然言語による直感的操作
              </li>
              <li className="flex items-center gap-3 text-gray-600">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                文脈の理解と学習
              </li>

            </ul>
          </div>
        </div>


      </div>
    </section>
  );
}