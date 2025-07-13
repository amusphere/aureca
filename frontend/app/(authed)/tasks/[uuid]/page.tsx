import TaskDetailPage from "@/components/pages/TaskDetailPage";
import { Task } from "@/types/Task";
import { apiGet } from "@/utils/api";
import { notFound } from "next/navigation";

interface TaskDetailRouteProps {
  params: Promise<{ uuid: string }>;
}

export default async function TaskDetailRoute({ params }: TaskDetailRouteProps) {
  const { uuid } = await params;

  if (!uuid) {
    notFound();
  }

  try {
    // Fetch task data on server side
    const response = await apiGet(`/tasks/${uuid}`);

    if (response.error) {
      if (response.error.status === 404) {
        notFound();
      }

      // Handle other errors
      return (
        <div className="container mx-auto px-6 py-8">
          <div className="text-center text-red-600">
            タスクの取得に失敗しました: {response.error.message}
          </div>
        </div>
      );
    }

    const task = response.data as Task;

    return <TaskDetailPage task={task} />;
  } catch (error) {
    console.error('Error fetching task:', error);
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="text-center text-red-600">
          タスクの取得中にエラーが発生しました
        </div>
      </div>
    );
  }
}
