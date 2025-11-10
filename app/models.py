from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Literal

CubeColor = Literal['R', 'G', 'B', 'O', 'Y', 'W']

class CubeFace(BaseModel):
    TL: CubeColor; TC: CubeColor; TR: CubeColor
    ML: CubeColor; C: CubeColor; MR: CubeColor
    BL: CubeColor; BC: CubeColor; BR: CubeColor

    @field_validator('*')
    @classmethod
    def validate_color(cls, v):
        if v not in {'R', 'G', 'B', 'O', 'Y', 'W'}:
            raise ValueError("Invalid cube color")
        return v

    def model_post_init(self, __context):
        if len([self.TL, self.TC, self.TR, self.ML, self.C, self.MR, self.BL, self.BC, self.BR]) != 9:
            raise ValueError("Cube face must have exactly 9 tiles")

class TauntRequest(BaseModel):
    npc_character: str = Field(..., min_length=1, max_length=50)
    player_character: str = Field(..., min_length=1, max_length=50)
    context: str | None = Field(None, max_length=200)

    @field_validator('npc_character', 'player_character')
    @classmethod
    def validate_character(cls, v):
        v = v.strip()
        if not v: raise ValueError("Character name cannot be empty")
        return v

class TauntResponse(BaseModel):
    taunt: str = Field(..., min_length=10, max_length=200)
    @field_validator('taunt')
    @classmethod
    def validate_taunt(cls, v):
        v = v.strip().strip('"').strip("'")
        if not v: raise ValueError("Taunt cannot be empty")
        return v
