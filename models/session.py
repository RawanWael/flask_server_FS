from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field


class Session(BaseModel):
    sessionId: str = Field(None, alias="_id")
    exerciseName: str
    exerciseId: str
    patientId: str
    therapistId: str
    date: datetime
    performedDuartion: int
    accuracy: float
    path: str
    addressed: bool
    comment: str

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data
