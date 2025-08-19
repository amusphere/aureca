import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

/**
 * GET /api/chat/threads
 * Get user's chat threads
 */
export async function GET(request: NextRequest) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Extract query parameters
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '1';
    const per_page = searchParams.get('per_page') || '30';

    // Forward request to backend
    const backendUrl = `${BACKEND_URL}/api/chat/threads?page=${page}&per_page=${per_page}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);

      return NextResponse.json(
        { error: 'Failed to fetch threads' },
        { status: response.status }
      );
    }

    const threads = await response.json();
    return NextResponse.json(threads);

  } catch (error) {
    console.error('Error fetching chat threads:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/chat/threads
 * Create a new chat thread
 */
export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();

    // Forward request to backend
    const backendUrl = `${BACKEND_URL}/api/chat/threads`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);

      return NextResponse.json(
        { error: 'Failed to create thread' },
        { status: response.status }
      );
    }

    const thread = await response.json();
    return NextResponse.json(thread, { status: 201 });

  } catch (error) {
    console.error('Error creating chat thread:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}