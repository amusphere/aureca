import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://backend:8000/api';

interface RouteContext {
  params: Promise<{
    threadUuid: string;
  }>;
}

/**
 * GET /api/chat/threads/[threadUuid]
 * Get chat thread with messages
 */
export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { getToken } = await auth();
    const token = await getToken();

    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { threadUuid } = await context.params;

    // Extract query parameters
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const per_page = searchParams.get('per_page') || '30';

    // Forward request to backend
    const backendUrl = `${API_BASE_URL}/chat/threads/${threadUuid}?page=${page}&per_page=${per_page}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);

      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Thread not found' },
          { status: 404 }
        );
      }

      return NextResponse.json(
        { error: 'Failed to fetch thread' },
        { status: response.status }
      );
    }

    const threadData = await response.json();
    return NextResponse.json(threadData);

  } catch (error) {
    console.error('Error fetching chat thread:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/chat/threads/[threadUuid]
 * Delete a chat thread
 */
export async function DELETE(request: NextRequest, context: RouteContext) {
  try {
    const { getToken } = await auth();
    const token = await getToken();

    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { threadUuid } = await context.params;

    // Forward request to backend
    const backendUrl = `${API_BASE_URL}/chat/threads/${threadUuid}`;

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);

      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Thread not found' },
          { status: 404 }
        );
      }

      return NextResponse.json(
        { error: 'Failed to delete thread' },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);

  } catch (error) {
    console.error('Error deleting chat thread:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}