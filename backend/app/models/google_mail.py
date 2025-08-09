from pydantic import BaseModel


class DraftModel(BaseModel):
    """Gmailドラフトモデル"""

    id: str
    subject: str | None = None
    body: str | None = None
    to: str | None = None
    cc: str | None = None
    bcc: str | None = None
    thread_id: str | None = None
    snippet: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
