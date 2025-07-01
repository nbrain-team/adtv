from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class DataLakeRecordBase(BaseModel):
    unique_id: Optional[int] = None
    lead_source: Optional[str] = None
    tier: Optional[int] = None
    city: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    dma: Optional[str] = None
    one_yr_total_sales_usd: Optional[float] = None
    state_initials: Optional[str] = None
    state_spelled_out: Optional[str] = None
    website: Optional[str] = None
    business_facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    years_experience: Optional[int] = None
    one_yr_seller_deals_count: Optional[int] = None
    one_yr_seller_deals_usd: Optional[float] = None
    one_yr_buyer_deals_count: Optional[int] = None
    one_yr_buyer_deals_usd: Optional[float] = None
    one_yr_total_transactions_count: Optional[int] = None
    average_home_sale_price_usd: Optional[float] = None
    invitation_response: Optional[str] = None
    invitation_response_notes: Optional[str] = None
    appointment_set_date: Optional[datetime] = None
    rep: Optional[str] = None
    b2b_call_center_vsa: Optional[bool] = False
    interest_level: Optional[str] = None
    attendance: Optional[str] = None
    tims_notes: Optional[str] = None
    craigs_notes: Optional[str] = None
    rejected_by_presenter: Optional[bool] = False
    profession: Optional[str] = None
    event_date: Optional[datetime] = None
    event_time: Optional[str] = None
    time_zone: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_street_address: Optional[str] = None
    hotel_city: Optional[str] = None
    hotel_state: Optional[str] = None
    hotel_zip_code: Optional[str] = None
    hotel_meeting_room_name: Optional[str] = None
    lion_flag: Optional[bool] = False
    sale_date: Optional[datetime] = None
    contract_status: Optional[str] = None
    event_type: Optional[str] = None
    client_type: Optional[str] = None
    partner_show_market: Optional[str] = None
    sale_type: Optional[str] = None
    sale_closed_by_market_manager: Optional[str] = None
    sale_closed_by_bdr: Optional[str] = None
    friday_deadline: Optional[str] = None
    start_date: Optional[datetime] = None
    initiation_fee: Optional[float] = None
    monthly_recurring_revenue: Optional[float] = None
    paid_membership_in_advance: Optional[str] = None
    account_manager_notes: Optional[str] = None
    referred_by: Optional[str] = None
    speaker_source: Optional[str] = None
    data_source: Optional[str] = None
    lender_one_yr_volume_usd: Optional[float] = None
    lender_one_yr_closed_loans_count: Optional[int] = None
    lender_banker_or_broker: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\d{3}-\d{3}-\d{4}$', v):
            raise ValueError('Phone must be in format 000-000-0000')
        return v
    
    @validator('state_initials')
    def validate_state_initials(cls, v):
        if v and len(v) != 2:
            raise ValueError('State initials must be exactly 2 characters')
        return v.upper() if v else v

class DataLakeRecordCreate(DataLakeRecordBase):
    pass

class DataLakeRecordUpdate(DataLakeRecordBase):
    pass

class DataLakeRecordResponse(DataLakeRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        orm_mode = True

class DataLakeFilterParams(BaseModel):
    lead_source: Optional[str] = None
    tier: Optional[int] = None
    city: Optional[str] = None
    state_initials: Optional[str] = None
    invitation_response: Optional[str] = None
    profession: Optional[str] = None
    contract_status: Optional[str] = None
    event_type: Optional[str] = None
    client_type: Optional[str] = None
    sale_type: Optional[str] = None
    
class ColumnMapping(BaseModel):
    csv_column: str
    db_field: Optional[str] = None

class BulkEditRequest(BaseModel):
    record_ids: List[int]
    updates: Dict[str, Any] 