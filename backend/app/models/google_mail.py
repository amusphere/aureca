from typing import Optional

from pydantic import BaseModel


class DraftModel(BaseModel):
    """Gmailドラフトモデル"""

    id: str
    subject: Optional[str] = None
    body: Optional[str] = None
    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    thread_id: Optional[str] = None
    snippet: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
