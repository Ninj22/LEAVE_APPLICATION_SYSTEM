from pydantic import BaseModel
from typing import Optional
from datetime import date

class LeaveApplication(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    contact_info: str
    salary_payment_preference: str
    salary_payment_address: Optional[str]
    permission_note_country: Optional[str]
    person_handling_duties_id: int
