from pydantic import BaseModel, Field

class RerankRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 5