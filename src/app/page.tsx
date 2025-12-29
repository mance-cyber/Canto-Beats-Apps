import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import HeroSection from '@/components/sections/hero-section';
import DemoSection from '@/components/sections/demo-section';
import FeaturesSection from '@/components/sections/features-section';
import ComparisonSection from '@/components/sections/comparison-section';
import DownloadSection from '@/components/sections/download-section';
import PricingSection from '@/components/sections/pricing-section';
import FaqSection from '@/components/sections/faq-section';

export default function Home() {
  return (
    <div className="flex min-h-dvh w-full flex-col">
      <Header />
      <main className="flex-1">
        <HeroSection />
        <DemoSection />
        <FeaturesSection />
        <ComparisonSection />
        <DownloadSection />
        <PricingSection />
        <FaqSection />
      </main>
      <Footer />
    </div>
  );
}
