import { Button } from "@/components/components/ui/button";
import { SignUpButton } from "@clerk/nextjs";
import { CheckIcon, StarIcon } from "lucide-react";

export default function PricingSection() {
  return (
    <section id="pricing" className="py-16 sm:py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16 sm:mb-20 px-4">
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            シンプルで
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              透明な料金体系
            </span>
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            あなたのニーズに合わせて最適なプランをお選びください。
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 gap-6 sm:gap-8 max-w-5xl mx-auto">
          {/* Standard Plan - Popular */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-lg border-2 border-blue-500 hover:shadow-xl transition-all duration-300 relative">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-full text-sm font-semibold flex items-center gap-2">
                <StarIcon className="w-4 h-4" />
                おすすめ
              </div>
            </div>

            <div className="text-center mb-8 pt-4">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">スタンダードプラン</h3>
              <p className="text-gray-600 mb-6">個人・小規模チーム向け</p>
              <div className="mb-6">
                <div className="space-y-2">
                  <div>
                    <span className="text-4xl font-bold text-gray-900">$10</span>
                    <span className="text-gray-600 ml-2">/月</span>
                  </div>
                  <div className="text-sm text-gray-500">
                    年間契約: <span className="font-semibold text-gray-700">$8/月</span>
                  </div>
                </div>
              </div>
              <SignUpButton mode="modal">
                <Button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white py-3 text-lg font-semibold rounded-xl">
                  14日間無料で試す
                </Button>
              </SignUpButton>
              <p className="text-xs text-gray-500 mt-3 text-center">
                14日間無料トライアル後、自動的に課金開始
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-gray-700">無制限タスク</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-gray-700">高度なAI機能</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-gray-700">マルチサービス連携</span>
              </div>

            </div>
          </div>

          {/* Team Plan - Coming Soon */}
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-3xl p-6 sm:p-8 shadow-sm border border-gray-200 relative">

            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-700 mb-2">チームプラン</h3>
              <p className="text-gray-500 mb-6">複数人での利用に</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-500">準備中</span>
              </div>
            </div>



            <div className="mt-8">
              <p className="text-center text-sm text-gray-500">
                より多くの機能を準備中です。<br />
                リリース時期についてはお問い合わせください。
              </p>
            </div>
          </div>
        </div>


      </div>
    </section>
  );
}