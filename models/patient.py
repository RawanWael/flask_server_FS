from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import List


class Patient(BaseModel):
    id: str = Field(None, alias="_id")
    password: str
    clinicId: str
    fullName: str
    age: int
    gender: str
    phoneNumber: int
    therapyType: List[str]
    therapistId: List[str]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data
