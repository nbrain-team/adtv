from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, CheckConstraint
from datetime import datetime
from core.database import Base

class DataLakeRecord(Base):
    __tablename__ = 'data_lake_records'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Fields from CSV dictionary
    unique_id = Column(Integer, nullable=True)
    lead_source = Column(String(255), nullable=True)
    tier = Column(Integer, nullable=True)
    city = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)  # Format: 000-000-0000
    email = Column(String(255), nullable=True)
    dma = Column(String(255), nullable=True)  # From dma-values.csv
    one_yr_total_sales_usd = Column(Float, nullable=True)
    state_initials = Column(String(2), nullable=True)
    state_spelled_out = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    business_facebook_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    years_experience = Column(Integer, nullable=True)
    one_yr_seller_deals_count = Column(Integer, nullable=True)
    one_yr_seller_deals_usd = Column(Float, nullable=True)
    one_yr_buyer_deals_count = Column(Integer, nullable=True)
    one_yr_buyer_deals_usd = Column(Float, nullable=True)
    one_yr_total_transactions_count = Column(Integer, nullable=True)
    average_home_sale_price_usd = Column(Float, nullable=True)
    invitation_response = Column(String(50), nullable=True)  # Booked, In-Play, Not Interested
    invitation_response_notes = Column(Text, nullable=True)
    appointment_set_date = Column(DateTime, nullable=True)
    rep = Column(String(255), nullable=True)
    b2b_call_center_vsa = Column(Boolean, default=False)
    interest_level = Column(String(100), nullable=True)  # 1- I'm In, 2- I'm Interested but have Questions, 3- No Thank You
    attendance = Column(String(50), nullable=True)  # Attended, Attended- Left Early, Canceled, No-Show
    tims_notes = Column(Text, nullable=True)
    craigs_notes = Column(Text, nullable=True)
    rejected_by_presenter = Column(Boolean, default=False)
    profession = Column(String(50), nullable=True)  # Agent, Lender, Title, Lawyer, Insurance, Builder, Other
    event_date = Column(DateTime, nullable=True)
    event_time = Column(String(20), nullable=True)  # HH:MM AM/PM
    time_zone = Column(String(20), nullable=True)  # Eastern, Central, Mountain, Pacific, Hawaii
    hotel_name = Column(String(255), nullable=True)
    hotel_street_address = Column(String(500), nullable=True)
    hotel_city = Column(String(255), nullable=True)
    hotel_state = Column(String(50), nullable=True)
    hotel_zip_code = Column(String(10), nullable=True)
    hotel_meeting_room_name = Column(String(255), nullable=True)
    lion_flag = Column(Boolean, default=False)
    sale_date = Column(DateTime, nullable=True)
    contract_status = Column(String(100), nullable=True)  # Agreement In, Ready for Podio, Importing, Owned by CSR, Objection, Rejection
    event_type = Column(String(100), nullable=True)  # In Person (Craig), In Person (Guest), Virtual - City Zoom, Virtual - Dragnet, Direct 1:1
    client_type = Column(String(100), nullable=True)  # Power Player Hybrid (PPH), Power Player Client, FAD Hybrid, Local FAD Hybrid, FAD, Local FAD, Brand Ambassador, OPADTV Hybrid, LION
    partner_show_market = Column(String(255), nullable=True)  # From partner-market.csv
    sale_type = Column(String(50), nullable=True)  # Event, Direct
    sale_closed_by_market_manager = Column(String(255), nullable=True)
    sale_closed_by_bdr = Column(String(255), nullable=True)
    friday_deadline = Column(String(50), nullable=True)  # First Friday, Second Friday, Third Friday
    start_date = Column(DateTime, nullable=True)
    initiation_fee = Column(Float, nullable=True)
    monthly_recurring_revenue = Column(Float, nullable=True)
    paid_membership_in_advance = Column(String(10), nullable=True)  # TRUE, FALSE
    account_manager_notes = Column(Text, nullable=True)
    referred_by = Column(String(255), nullable=True)
    speaker_source = Column(String(255), nullable=True)  # Dave Panozzo, Shannon Gillette, Barry Habib, KWNM
    data_source = Column(String(255), nullable=True)
    lender_one_yr_volume_usd = Column(Float, nullable=True)
    lender_one_yr_closed_loans_count = Column(Integer, nullable=True)
    lender_banker_or_broker = Column(String(20), nullable=True)  # Banker, Broker
    
    # Metadata fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    # Add check constraints for validation
    __table_args__ = (
        CheckConstraint("phone ~ '^[0-9]{3}-[0-9]{3}-[0-9]{4}$' OR phone IS NULL", name='check_phone_format'),
        CheckConstraint("email ~ '^[^@]+@[^@]+\.[^@]+$' OR email IS NULL", name='check_email_format'),
    ) 