import AuthedLayout from '@/components/components/commons/AuthedLayout';
import HomePage from '@/components/pages/HomePage';
import LandingPage from '@/components/pages/LandingPage';
import { SignedIn, SignedOut } from '@clerk/nextjs';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Nadeshiko.AI - AIタスク管理アプリケーション",
  description: "AIを活用したスマートなタスク管理で、あなたの生産性を向上させます。様々なサービスと連携してタスクを自動生成。",
  keywords: ["AI", "タスク管理", "生産性", "サービス連携", "自動化"],
  openGraph: {
    title: "Nadeshiko.AI - AIタスク管理アプリケーション",
    description: "AIを活用したスマートなタスク管理で、あなたの生産性を向上させます。",
    type: "website",
    locale: "ja_JP",
  },
};

export default function RootPage() {
  return (
    <>
      <SignedOut>
        <LandingPage />
      </SignedOut>
      <SignedIn>
        <AuthedLayout>
          <HomePage />
        </AuthedLayout>
      </SignedIn>
    </>
  );
}