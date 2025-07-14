"use server";

import { apiPost, createApiResponse } from '@/utils/api';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ task_source_uuid: string }> }
) {
  try {
    const { task_source_uuid } = await params;

    if (!task_source_uuid) {
      return NextResponse.json(
        { success: false, error: 'task_source_uuidが必要です' },
        { status: 400 }
      );
    }

    // バックエンドのmail APIエンドポイントにapiPostを使ってリクエストを送信
    const apiResponse = await apiPost(`/mail/drafts/${task_source_uuid}`, {});

    // apiResponseを使ってNextResponseを生成
    return createApiResponse(apiResponse);

  } catch (error) {
    console.error('Email Draft Generation API Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : '内部サーバーエラー'
      },
      { status: 500 }
    );
  }
}
