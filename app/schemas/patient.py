from pydantic import BaseModel
from datetime import date


class PatientData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
