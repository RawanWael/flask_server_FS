from datetime import datetime, timedelta
from xmlrpc.client import DateTime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import List


class Appointment(BaseModel):
    therapistId: str
    patientId: str
    timeFrom: datetime
    timeTo: datetime
    status: str

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        return data