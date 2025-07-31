
import ContactSection from "@/components/components/landing/ContactSection";
import HeroSection from "@/components/components/landing/HeroSection";
import LandingFooter from "@/components/components/landing/LandingFooter";
import LandingHeader from "@/components/components/landing/LandingHeader";
import PricingSection from "@/components/components/landing/PricingSection";
import ServiceDetailSection from "@/components/components/landing/ServiceDetailSection";
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

export default function LandingPage() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Nadeshiko.AI",
    "applicationCategory": "ProductivityApplication",
    "description": "AIを活用したタスク管理アプリケーション",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "JPY"
    }
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <div className="min-h-screen bg-white">
        <LandingHeader />
        <main>
          <HeroSection />
          <ServiceDetailSection />
          <PricingSection />
          <ContactSection />
        </main>
        <LandingFooter />
      </div>
    </>
  );
}
