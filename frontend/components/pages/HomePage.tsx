import AIChat from "@/components/components/commons/AIChat";
import { AIUpgradePrompt } from "@/components/components/commons/AIUpgradePrompt";
import { TaskList } from "@/components/components/tasks/TaskList";
import { PremiumGuard } from "@/components/components/commons/PremiumGuard";

export default function HomePage() {
  return (
    <div className="relative h-full bg-background">
      {/* Main Content Area */}
      <main className="h-full overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 pb-32">
          <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
            {/* Show AIUpgradePrompt for non-premium users */}
            <PremiumGuard
              fallback={<AIUpgradePrompt />}
              showUpgrade={false}
            >
              {/* Premium users don't see the upgrade prompt */}
              {null}
            </PremiumGuard>
            <TaskList />
          </div>
        </div>
      </main>

      {/* Show AIChat only for premium users */}
      <PremiumGuard showUpgrade={false}>
        <AIChat />
      </PremiumGuard>
    </div>
  );
}
