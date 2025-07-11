"use client";

import { useState } from "react";
import AIChatModal from "../components/chat/AIChatModal";
import FloatingChatButton from "../components/chat/ChatButton";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

const DASHBOARD_CARDS = [
  {
    id: "tasks",
    title: "タスク管理",
    description: "タスクを管理し、進捗を追跡できます。",
    icon: "📋",
  },
  {
    id: "calendar",
    title: "カレンダー",
    description: "予定とイベントを確認できます。",
    icon: "📅",
  },
  {
    id: "email",
    title: "メール",
    description: "重要なメールをチェックできます。",
    icon: "📧",
  },
] as const;

export default function DashboardPage() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const openChat = () => setIsChatOpen(true);
  const closeChat = () => setIsChatOpen(false);

  return (
    <div className="relative min-h-screen bg-background">
      {/* Main Content Area */}
      <main className="container mx-auto px-6 py-8">
        <div className="max-w-7xl mx-auto">

          {/* Dashboard Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DASHBOARD_CARDS.map((card) => (
              <Card key={card.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl" role="img" aria-label={card.title}>
                      {card.icon}
                    </span>
                    <CardTitle className="text-xl">{card.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription>{card.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>

      {/* Floating Chat Button */}
      <FloatingChatButton
        onClick={openChat}
        hasUnreadMessages={false}
      />

      {/* AI Chat Modal */}
      <AIChatModal
        isOpen={isChatOpen}
        onClose={closeChat}
      />
    </div>
  );
}
