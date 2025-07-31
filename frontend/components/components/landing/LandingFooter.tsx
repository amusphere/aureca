import { BrainCircuitIcon } from "lucide-react";
import Link from "next/link";

export default function LandingFooter() {
  const appName = process.env.NEXT_PUBLIC_APP_NAME || "Nadeshiko.AI";
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Main Footer Content */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          {/* Company Info */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <BrainCircuitIcon className="w-5 h-5 text-gray-900" />
            </div>
            <div>
              <span className="text-lg font-bold">{appName}</span>
              <p className="text-sm text-gray-300">by 合同会社アミュスフィア</p>
            </div>
          </div>

          {/* Legal Links */}
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-300">
            <Link href="/company" className="hover:text-white transition-colors">
              会社概要
            </Link>
            <Link href="/terms-of-service" className="hover:text-white transition-colors">
              利用規約
            </Link>
            <Link href="/privacy-policy" className="hover:text-white transition-colors">
              プライバシーポリシー
            </Link>
            <Link href="/legal-notice" className="hover:text-white transition-colors">
              特定商取引法
            </Link>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-gray-800 mt-6 pt-6 text-center">
          <p className="text-sm text-gray-400">
            © {currentYear} {appName}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}