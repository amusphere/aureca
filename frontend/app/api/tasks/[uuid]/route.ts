import { apiDelete, apiPatch } from '@/utils/api';
import { NextRequest, NextResponse } from 'next/server';

export async function PATCH(
  request: NextRequest,
  { params }: { params: { uuid: string } }
) {
  try {
    const { uuid } = params;
    const body = await request.json();

    // バックエンドのPATCH /{task_uuid}エンドポイントを使用
    const response = await apiPatch(`/tasks/${uuid}`, body);

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

export async function DELETE(
  request: NextRequest,
  { params }: { params: { uuid: string } }
) {
  try {
    const { uuid } = params;

    // バックエンドのDELETE /{task_uuid}エンドポイントを使用
    const response = await apiDelete(`/tasks/${uuid}`);

    if (response.error) {
      return NextResponse.json(
        { error: response.error.message || 'Failed to delete task' },
        { status: response.error.status || 500 }
      );
    }

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error('Error deleting task:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
