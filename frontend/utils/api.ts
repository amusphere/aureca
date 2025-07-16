/* eslint-disable @typescript-eslint/no-explicit-any */
"use server";

import { auth } from '@clerk/nextjs/server';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

// APIのベースURL
const API_BASE_URL = process.env.API_BASE_URL;

// API呼び出し時のデフォルトオプション
const defaultOptions: RequestInit = {
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
};

// JSON レスポンス用の汎用型
type Json = Record<string, any>;

// APIエラーの型定義
interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

/**
 * API呼び出し結果のレスポンス型
 */
export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
}

/**
 * API呼び出しのエラーハンドリング
 */
const handleError = (error: any): ApiError => {
  console.error('API Error:', error);

  if (error instanceof Response) {
    return {
      message: `API error: ${error.statusText}`,
      status: error.status,
    };
  }

  return {
    message: (error as Error).message || 'any API error occurred',
  };
};

const getAccessToken = async (): Promise<string | null> => {
  const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;
  if (authSystem === 'email_password') {
    const store = await cookies();
    const accessToken = store.get('access_token');
    return accessToken?.value || null;
  }
  if (authSystem === 'clerk') {
    const { getToken } = await auth();
    return getToken();
  }
  return null;
};


/**
 * 汎用的なAPI呼び出し関数
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    // headersを必ずオブジェクトとして初期化
    const baseHeaders = { ...(defaultOptions.headers || {}), ...(options.headers || {}) };

    const token = await getAccessToken();
    if (token) {
      baseHeaders['Authorization'] = `Bearer ${token}`;
    }

    const mergedOptions = { ...defaultOptions, ...options, headers: baseHeaders };

    const response = await fetch(url, mergedOptions);

    if (!response.ok) {
      let errorData: Json = {};
      try {
        // APIからのエラーレスポンスをJSONとして解析
        errorData = await response.clone().json() as Json;
      } catch {
        // JSONでない場合はテキストとして取得
        errorData = { message: await response.text() };
      }

      return {
        error: {
          message: (errorData.message as string) || response.statusText,
          status: response.status,
          details: errorData.details ?? errorData,
        },
      };
    }

    // 成功レスポンスがある場合
    if (response.status !== 204) { // 204 No Content
      const data = (await response.json()) as T;
      return { data };
    }

    // 204 No Content の場合
    return { data: null as any as T };

  } catch (err: any) {
    return { error: handleError(err) };
  }
}

/**
 * GET リクエスト
 */
export async function apiGet<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'GET',
    ...options,
  });
}

/**
 * POST リクエスト
 */
export async function apiPost<T>(
  endpoint: string,
  data: any = undefined,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'POST',
    body: data !== undefined ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * ファイルアップロード用 POST (multipart/form-data)
 */
export async function apiPostForm<T>(
  endpoint: string,
  formData: FormData
): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'POST',
    body: formData,
  });
}

/**
 * URLエンコードされたデータをPOSTする
 */
export async function apiPostUrlEncoded<T>(
  endpoint: string,
  params: URLSearchParams,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'POST',
    body: params.toString(),
    headers: {
      ...(options.headers || {}),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    ...options,
  });
}

/**
 * PATCH リクエスト
 */
export async function apiPatch<T>(
  endpoint: string,
  data: any = undefined,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'PATCH',
    body: data !== undefined ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * DELETE リクエスト
 */
export async function apiDelete<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  return fetchApi<T>(endpoint, {
    method: 'DELETE',
    ...options,
  });
}

/**
 * サーバーアクションでAPI呼び出し結果からNextResponseを生成するヘルパー
 */
export async function createApiResponse<T>(apiResponse: ApiResponse<T>): Promise<NextResponse> {
  if (apiResponse.error) {
    const status = apiResponse.error.status || 500;
    return NextResponse.json(
      { message: apiResponse.error.message, details: apiResponse.error.details },
      { status }
    );
  }

  return NextResponse.json(apiResponse.data);
}
