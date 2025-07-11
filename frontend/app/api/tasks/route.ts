import { apiGet } from '@/utils/api';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const completed = searchParams.get('completed');
    const expires_at = searchParams.get('expires_at');

    // クエリパラメータを構築
    const queryParams = new URLSearchParams();
    if (completed !== null) {
      queryParams.append('completed', completed);
    }
    if (expires_at !== null) {
      queryParams.append('expires_at', expires_at);
    }

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/tasks?${queryString}` : '/tasks';

    // バックエンドAPIから直接取得
    const response = await apiGet(endpoint);

    if (response.error) {
      return NextResponse.json(
        { error: response.error.message || 'Failed to fetch tasks' },
        { status: response.error.status || 500 }
      );
    }

    return NextResponse.json(response.data);

  } catch (error) {
    console.error('Error fetching tasks:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
