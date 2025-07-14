import { EmailDraft } from '@/types/EmailDraft';
import { apiGet, createApiResponse } from '@/utils/api';

export async function GET(
  request: Request,
  { params }: { params: { task_source_uuid: string } }
) {
  const { task_source_uuid } = params;

  const result = await apiGet<EmailDraft>(`/mail/drafts/${task_source_uuid}`);
  return createApiResponse(result);
}
