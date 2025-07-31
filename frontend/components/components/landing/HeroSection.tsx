import { Button } from "@/components/components/ui/button";
import { SignUpButton } from "@clerk/nextjs";
import { ArrowRightIcon } from "lucide-react";

export default function HeroSection() {
  const appName = process.env.NEXT_PUBLIC_APP_NAME || "Nadeshiko.AI";

  return (
    <section className="pt-16 pb-20 sm:pt-24 sm:pb-32 bg-gradient-to-b from-white via-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="space-y-8 sm:space-y-12">
            {/* Main Headline */}
            <div className="space-y-6">
              <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 tracking-tight leading-tight px-2">
                AIが変える
                <br />
                <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  タスク管理の未来
                </span>
              </h1>
              <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-600 max-w-4xl mx-auto leading-relaxed font-light px-4">
                {appName}は、AIを活用したスマートなタスク管理で、あなたの生産性を最大化します。
                <br className="hidden sm:block" />
                様々なサービスと連携してタスクを自動生成し、自然言語で直感的に操作できます。
              </p>
            </div>

            {/* CTA Button */}
            <div className="flex justify-center px-4">
              <SignUpButton mode="modal">
                <Button
                  size="lg"
                  className="w-full sm:w-auto bg-gray-900 hover:bg-gray-800 text-white px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 max-w-xs sm:max-w-none"
                >
                  14日間無料で体験する
                  <ArrowRightIcon className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                </Button>
              </SignUpButton>
            </div>


          </div>
        </div>
      </div>

      {/* Background Decoration */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-purple-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 w-72 h-72 bg-indigo-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-4000"></div>
        </div>
      </div>
    </section>
  );
}