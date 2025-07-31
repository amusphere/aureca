"use client";

import { Button } from "@/components/components/ui/button";
import { SignInButton, SignUpButton } from "@clerk/nextjs";
import { BrainCircuitIcon, MenuIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function LandingHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const appName = process.env.NEXT_PUBLIC_APP_NAME || "Nadeshiko.AI";

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
              <BrainCircuitIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-gray-900">{appName}</span>
          </Link>



          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <SignInButton mode="modal">
              <Button variant="ghost" className="text-gray-600 hover:text-gray-900">
                ログイン
              </Button>
            </SignInButton>
            <SignUpButton mode="modal">
              <Button className="bg-gray-900 hover:bg-gray-800 text-white">
                サインアップ
              </Button>
            </SignUpButton>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="メニューを開く"
          >
            {isMenuOpen ? (
              <XIcon className="w-6 h-6" />
            ) : (
              <MenuIcon className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-100 py-4">
            <div className="flex flex-col gap-3">
              <SignInButton mode="modal">
                <Button variant="ghost" className="w-full justify-start text-gray-600 hover:text-gray-900" onClick={() => setIsMenuOpen(false)}>
                  ログイン
                </Button>
              </SignInButton>
              <SignUpButton mode="modal">
                <Button className="w-full bg-gray-900 hover:bg-gray-800 text-white" onClick={() => setIsMenuOpen(false)}>
                  サインアップ
                </Button>
              </SignUpButton>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}