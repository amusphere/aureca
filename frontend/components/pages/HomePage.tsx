import AIChat from "@/components/components/commons/AIChat";
import { AIUpgradePrompt } from "@/components/components/commons/AIUpgradePrompt";
import { TaskList } from "@/components/components/tasks/TaskList";
import { Protect } from "@clerk/nextjs";

export default async function HomePage() {

  return (
    <div className="relative h-full bg-background">
      {/* Main Content Area */}
      <main className="h-full overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 pb-24">
          <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8">
            <Protect condition={(has) => has({ plan: "free" })}>
              <AIUpgradePrompt />
            </Protect>
            <TaskList />
          </div>
        </div>
      </main>

      <Protect condition={(has) => !has({ plan: "free" })}>
        <AIChat />
      </Protect>
    </div>
  );
}
