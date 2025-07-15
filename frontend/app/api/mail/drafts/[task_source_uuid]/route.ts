import { EmailDraft } from '@/types/EmailDraft';
import { apiDelete, apiGet, apiPost, createApiResponse } from '@/utils/api';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ task_source_uuid: string }> }
) {
  const { task_source_uuid } = await params;

  const result = await apiGet<EmailDraft>(`/mail/drafts/${task_source_uuid}`);
  return createApiResponse(result);
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ task_source_uuid: string }> }
) {
  const { task_source_uuid } = await params;

  const result = await apiPost<EmailDraft>(`/mail/drafts/${task_source_uuid}`, {});
  return createApiResponse(result);
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ task_source_uuid: string }> }
) {
  const { task_source_uuid } = await params;

  const result = await apiDelete(`/mail/drafts/${task_source_uuid}`);
  return createApiResponse(result);
}
