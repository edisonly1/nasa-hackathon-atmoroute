from pydantic import BaseModel, Field

class ExportQuery(BaseModel):
    format: str = Field("csv", pattern="^(csv|json)$", examples=["csv"])
