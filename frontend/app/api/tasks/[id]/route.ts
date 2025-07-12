import { apiPatch } from '@/utils/api';
import { NextRequest, NextResponse } from 'next/server';

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const taskId = params.id;

    if (!taskId) {
      return NextResponse.json(
        { error: 'Task ID is required' },
        { status: 400 }
      );
    }

    // バックエンドAPIに更新リクエストを送信
    const response = await apiPatch(`/tasks/${taskId}`, body);

    if (response.error) {
      return NextResponse.json(
        { error: response.error.message || 'Failed to update task' },
        { status: response.error.status || 500 }
      );
    }

    return NextResponse.json(response.data);

  } catch (error) {
    console.error('Error updating task:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
