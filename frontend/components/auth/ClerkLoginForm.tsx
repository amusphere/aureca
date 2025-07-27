import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/components/ui/card";
import { SignInButton } from "@clerk/nextjs";
import { BrainCircuitIcon, CalendarIcon, CheckCircleIcon, MailIcon, SparklesIcon, ZapIcon } from "lucide-react";

export default function ClerkLoginForm() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Enhanced background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Primary orbs */}
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-emerald-500/15 to-cyan-500/15 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-gradient-to-r from-violet-500/10 to-pink-500/10 rounded-full blur-3xl animate-pulse delay-500" />

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]" />

        {/* Floating particles */}
        <div className="absolute top-1/4 left-1/3 w-2 h-2 bg-blue-400/40 rounded-full animate-ping" />
        <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-purple-400/60 rounded-full animate-ping delay-700" />
        <div className="absolute bottom-1/3 left-1/5 w-1.5 h-1.5 bg-emerald-400/50 rounded-full animate-ping delay-1200" />
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 sm:px-6 lg:px-8">
        {/* Main login card */}
        <div className="w-full max-w-lg space-y-8 animate-fade-in-up">
          <Card className="border border-white/10 shadow-2xl bg-white/5 backdrop-blur-2xl relative overflow-hidden group hover:bg-white/[0.07] transition-all duration-700">
            {/* Enhanced card decorative gradients */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-tl from-emerald-500/3 via-transparent to-cyan-500/3 pointer-events-none" />

            {/* Animated border */}
            <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-emerald-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-700 blur-sm" />

            <CardHeader className="relative z-10 text-center space-y-8 pt-12 pb-8">
              {/* Enhanced logo area with multiple layers */}
              <div className="relative mx-auto">
                {/* Outer glow ring */}
                <div className="absolute inset-0 w-24 h-24 bg-gradient-to-r from-blue-500/30 to-purple-600/30 rounded-3xl blur-xl animate-pulse" />

                {/* Main logo container */}
                <div className="relative w-20 h-20 bg-gradient-to-br from-blue-500 via-purple-600 to-emerald-500 rounded-2xl flex items-center justify-center shadow-2xl transform hover:scale-110 transition-transform duration-500 group-hover:rotate-3">
                  <BrainCircuitIcon className="w-10 h-10 text-white drop-shadow-lg" />

                  {/* Inner sparkle effects */}
                  <div className="absolute top-2 right-2 w-1 h-1 bg-white/80 rounded-full animate-ping" />
                  <div className="absolute bottom-3 left-3 w-0.5 h-0.5 bg-white/60 rounded-full animate-ping delay-500" />
                </div>
              </div>

              {/* Minimal title */}
              <div className="space-y-3">
                <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent tracking-tight">
                  {process.env.NEXT_PUBLIC_APP_NAME}
                </h1>
                <div className="flex items-center justify-center gap-2 text-white/60">
                  <div className="w-8 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
                  <ZapIcon className="w-4 h-4" />
                  <div className="w-8 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
                </div>
              </div>
            </CardHeader>

            <CardContent className="relative z-10 space-y-8 pb-12 px-8">
              {/* Visual feature showcase - icon-focused design */}
              <div className="grid grid-cols-3 gap-6 mb-8">
                {/* AI Feature */}
                <div className="group/feature text-center space-y-3">
                  <div className="relative mx-auto w-16 h-16 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-2xl flex items-center justify-center border border-white/10 group-hover/feature:border-blue-400/30 transition-all duration-500 group-hover/feature:scale-110">
                    <SparklesIcon className="w-7 h-7 text-blue-400 group-hover/feature:text-blue-300 transition-colors duration-300" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-400/60 rounded-full animate-pulse" />
                  </div>
                  <div className="text-xs text-white/70 font-medium">AI</div>
                </div>

                {/* Smart Management */}
                <div className="group/feature text-center space-y-3">
                  <div className="relative mx-auto w-16 h-16 bg-gradient-to-br from-emerald-500/20 to-green-600/20 rounded-2xl flex items-center justify-center border border-white/10 group-hover/feature:border-emerald-400/30 transition-all duration-500 group-hover/feature:scale-110">
                    <CheckCircleIcon className="w-7 h-7 text-emerald-400 group-hover/feature:text-emerald-300 transition-colors duration-300" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400/60 rounded-full animate-pulse delay-300" />
                  </div>
                  <div className="text-xs text-white/70 font-medium">Smart</div>
                </div>

                {/* Integration */}
                <div className="group/feature text-center space-y-3">
                  <div className="relative mx-auto w-16 h-16 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-2xl flex items-center justify-center border border-white/10 group-hover/feature:border-cyan-400/30 transition-all duration-500 group-hover/feature:scale-110">
                    <div className="flex items-center justify-center gap-1">
                      <CalendarIcon className="w-5 h-5 text-cyan-400 group-hover/feature:text-cyan-300 transition-colors duration-300" />
                      <MailIcon className="w-5 h-5 text-cyan-400 group-hover/feature:text-cyan-300 transition-colors duration-300" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-cyan-400/60 rounded-full animate-pulse delay-600" />
                  </div>
                  <div className="text-xs text-white/70 font-medium">Connect</div>
                </div>
              </div>

              {/* Enhanced login button */}
              <SignInButton mode="modal">
                <Button
                  className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-600 via-purple-600 to-emerald-600 hover:from-blue-500 hover:via-purple-500 hover:to-emerald-500 text-white shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 ease-out hover:scale-[1.02] active:scale-[0.98] group/btn border-0 relative overflow-hidden"
                  size="lg"
                >
                  {/* Button background animation */}
                  <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000" />

                  <div className="relative flex items-center justify-center gap-3">
                    <span>Sign In</span>
                  </div>
                </Button>
              </SignInButton>

              {/* Terms of Service link */}
              <div className="text-center">
                <a
                  href="/terms-of-service"
                  className="text-sm text-white/60 hover:text-white/80 transition-colors duration-300 underline underline-offset-4 hover:underline-offset-2"
                >
                  特定商取引法に基づく表記
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}