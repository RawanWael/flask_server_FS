from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(None, alias="_id")
    password: str
    token: str
    user_type: str

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data


class UserLoginRequest(BaseModel):
    id: str = Field(None, alias="_id")
    password: str

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data["_id"] is None:
            data.pop("_id")
        return data
