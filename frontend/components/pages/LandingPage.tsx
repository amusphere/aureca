import ContactSection from "@/components/components/landing/ContactSection";
import HeroSection from "@/components/components/landing/HeroSection";
import LandingFooter from "@/components/components/landing/LandingFooter";
import LandingHeader from "@/components/components/landing/LandingHeader";
import PricingSection from "@/components/components/landing/PricingSection";
import ServiceDetailSection from "@/components/components/landing/ServiceDetailSection";


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
