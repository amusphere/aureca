"use client";

import TaskDetailPage from "@/components/pages/TaskDetailPage";
import { useParams } from "next/navigation";

export default function TaskDetailRoute() {
  const params = useParams();
  const uuid = params.uuid as string;

  if (!uuid) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="text-center text-red-600">
          無効なタスクIDです
        </div>
      </div>
    );
  }

  return <TaskDetailPage taskUuid={uuid} />;
}
