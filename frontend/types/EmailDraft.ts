export interface EmailDraft {
  id: string;
  subject?: string | null;
  body?: string | null;
  to?: string | null;
  cc?: string | null;
  bcc?: string | null;
  thread_id?: string | null;
  snippet?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
