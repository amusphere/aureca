from sqlmodel import Session


class AiTaskService:

    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id
