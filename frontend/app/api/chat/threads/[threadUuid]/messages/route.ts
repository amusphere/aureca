import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://backend:8000/api';

interface RouteContext {
  params: Promise<{
    threadUuid: string;
  }>;
}

/**
 * POST /api/chat/threads/[threadUuid]/messages
 * Send a message to a chat thread
 */
export async function POST(request: NextRequest, context: RouteContext) {
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
    const body = await request.json();

    // Validate request body
    if (!body.content || typeof body.content !== 'string') {
      return NextResponse.json(
        { error: 'Message content is required' },
        { status: 400 }
      );
    }

    // Forward request to backend
    const backendUrl = `${API_BASE_URL}/chat/threads/${threadUuid}/messages`;

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
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
        { error: 'Failed to send message' },
        { status: response.status }
      );
    }

    const message = await response.json();
    return NextResponse.json(message, { status: 201 });

  } catch (error) {
    console.error('Error sending message:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}