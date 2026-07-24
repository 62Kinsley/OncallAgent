from pydantic import BaseModel


class Incident(BaseModel):
    incident_id: str
    title: str
    severity: str
    service: str
    started_at: str
    summary: str
    initial_context: str = ""
