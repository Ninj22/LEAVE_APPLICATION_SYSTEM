from pydantic import BaseModel
from datetime import date

class LeaveApplication(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    contact_info: str
    salary_payment_preference: str
    salary_payment_address: str
    permission_note_country: str
    person_handling_duties_id: str
