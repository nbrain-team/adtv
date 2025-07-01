from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional, Dict, Any
import csv
import io
import json
from datetime import datetime
from core.database import get_db
from .data_lake_models import DataLakeRecord
from .data_lake_schemas import (
    DataLakeRecordCreate, 
    DataLakeRecordUpdate, 
    DataLakeRecordResponse,
    DataLakeFilterParams,
    ColumnMapping,
    BulkEditRequest
)

router = APIRouter(tags=["data_lake"])

# Field definitions for validation and dropdown values
FIELD_DEFINITIONS = {
    "invitation_response": ["Booked", "In-Play", "Not Interested"],
    "interest_level": ["1- I'm In", "2- I'm Interested but have Questions", "3- No Thank You"],
    "attendance": ["Attended", "Attended- Left Early", "Canceled", "No-Show"],
    "profession": ["Agent", "Lender", "Title", "Lawyer", "Insurance", "Builder", "Other"],
    "time_zone": ["Eastern", "Central", "Mountain", "Pacific", "Hawaii"],
    "contract_status": ["Agreement In", "Ready for Podio", "Importing", "Owned by CSR", "Objection", "Rejection"],
    "event_type": ["In Person (Craig)", "In Person (Guest)", "Virtual - City Zoom", "Virtual - Dragnet", "Direct 1:1"],
    "client_type": ["Power Player Hybrid (PPH)", "Power Player Client", "FAD Hybrid", "Local FAD Hybrid", "FAD", "Local FAD", "Brand Ambassador", "OPADTV Hybrid", "LION"],
    "sale_type": ["Event", "Direct"],
    "sale_closed_by_market_manager": ["Justin Anderson", "Kim Vigil", "Joan Akita", "Tim Diiorio", "Kim Antenucci", "David Perloff", "Kalena Goin", "Steve Tabacchiera", "Rick Tancreto"],
    "sale_closed_by_bdr": ["Amy", "Bailey", "Evan", "Kaitlyn", "Kalena", "Sigrid", "Justin", "Tim", "Kimmy A"],
    "friday_deadline": ["First Friday", "Second Friday", "Third Friday"],
    "paid_membership_in_advance": ["TRUE", "FALSE"],
    "speaker_source": ["Dave Panozzo", "Shannon Gillette", "Barry Habib", "KWNM"],
    "lender_banker_or_broker": ["Banker", "Broker"]
}

# Load DMA and Partner Market values from CSV files
def load_dropdown_values():
    dma_values = []
    partner_markets = []
    
    try:
        with open('/Users/dannydemichele/Adstv/data lake/dma-values.csv', 'r') as f:
            reader = csv.DictReader(f)
            dma_values = [row['DMA'] for row in reader]
    except:
        pass
    
    try:
        with open('/Users/dannydemichele/Adstv/data lake/partner-market.csv', 'r') as f:
            reader = csv.DictReader(f)
            partner_markets = [row['Partner Show Market'] for row in reader]
    except:
        pass
    
    FIELD_DEFINITIONS['dma'] = dma_values
    FIELD_DEFINITIONS['partner_show_market'] = partner_markets

# Load dropdown values on startup
load_dropdown_values()

@router.get("/field-definitions")
async def get_field_definitions():
    """Get field definitions including dropdown values"""
    return FIELD_DEFINITIONS

@router.get("/records", response_model=Dict[str, Any])
async def get_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    filters: Optional[str] = None,
    columns: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get data lake records with pagination, sorting, filtering, and column selection"""
    query = db.query(DataLakeRecord)
    
    # Apply search across all text fields
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                DataLakeRecord.lead_source.ilike(search_term),
                DataLakeRecord.city.ilike(search_term),
                DataLakeRecord.first_name.ilike(search_term),
                DataLakeRecord.last_name.ilike(search_term),
                DataLakeRecord.company.ilike(search_term),
                DataLakeRecord.email.ilike(search_term),
                DataLakeRecord.phone.ilike(search_term),
                DataLakeRecord.state_initials.ilike(search_term),
                DataLakeRecord.state_spelled_out.ilike(search_term),
                DataLakeRecord.rep.ilike(search_term),
                DataLakeRecord.invitation_response_notes.ilike(search_term),
                DataLakeRecord.tims_notes.ilike(search_term),
                DataLakeRecord.craigs_notes.ilike(search_term),
                DataLakeRecord.hotel_name.ilike(search_term),
                DataLakeRecord.hotel_city.ilike(search_term),
                DataLakeRecord.hotel_state.ilike(search_term),
                DataLakeRecord.account_manager_notes.ilike(search_term),
                DataLakeRecord.referred_by.ilike(search_term),
                DataLakeRecord.data_source.ilike(search_term)
            )
        )
    
    # Apply filters
    if filters:
        filter_dict = json.loads(filters)
        for field, value in filter_dict.items():
            if hasattr(DataLakeRecord, field) and value:
                query = query.filter(getattr(DataLakeRecord, field) == value)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    if sort_by and hasattr(DataLakeRecord, sort_by):
        order_func = getattr(getattr(DataLakeRecord, sort_by), sort_order)()
        query = query.order_by(order_func)
    
    # Apply pagination
    records = query.offset(skip).limit(limit).all()
    
    # Convert to dict and filter columns if specified
    records_data = []
    for record in records:
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        if columns:
            column_list = columns.split(',')
            record_dict = {k: v for k, v in record_dict.items() if k in column_list}
        records_data.append(record_dict)
    
    return {
        "records": records_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/records", response_model=DataLakeRecordResponse)
async def create_record(
    record: DataLakeRecordCreate,
    db: Session = Depends(get_db)
):
    """Create a new data lake record"""
    db_record = DataLakeRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/records/{record_id}", response_model=DataLakeRecordResponse)
async def update_record(
    record_id: int,
    record: DataLakeRecordUpdate,
    db: Session = Depends(get_db)
):
    """Update a data lake record"""
    db_record = db.query(DataLakeRecord).filter(DataLakeRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    for field, value in record.dict(exclude_unset=True).items():
        setattr(db_record, field, value)
    
    db_record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Delete a data lake record"""
    db_record = db.query(DataLakeRecord).filter(DataLakeRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(db_record)
    db.commit()
    return {"message": "Record deleted successfully"}

@router.delete("/records/all")
async def delete_all_records(
    confirm: bool = Query(False, description="Set to true to confirm deletion of all records"),
    db: Session = Depends(get_db)
):
    """Delete all data lake records - requires confirmation"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Please set confirm=true to delete all records"
        )
    
    # Get count before deletion
    count = db.query(DataLakeRecord).count()
    
    # Delete all records
    db.query(DataLakeRecord).delete()
    db.commit()
    
    return {"message": f"Successfully deleted {count} records"}

@router.post("/bulk-edit")
async def bulk_edit_records(
    request: BulkEditRequest,
    db: Session = Depends(get_db)
):
    """Bulk edit multiple records"""
    records = db.query(DataLakeRecord).filter(DataLakeRecord.id.in_(request.record_ids)).all()
    
    for record in records:
        for field, value in request.updates.items():
            if hasattr(record, field):
                setattr(record, field, value)
        record.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": f"Updated {len(records)} records"}

@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    mapping: str = Query(...),
    db: Session = Depends(get_db)
):
    """Import CSV file with column mapping and smart record matching"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Parse mapping
    column_mapping = json.loads(mapping)
    
    # Read CSV file
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    # Get the highest existing unique_id
    max_unique_id = db.query(func.max(DataLakeRecord.unique_id)).scalar() or 0
    next_unique_id = max_unique_id + 1
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # Map CSV columns to database fields
            record_data = {}
            for csv_col, db_field in column_mapping.items():
                if db_field and csv_col in row:
                    value = row[csv_col].strip()
                    
                    # Handle different field types
                    if db_field.endswith('_date'):
                        if value:
                            record_data[db_field] = datetime.strptime(value, '%m/%d/%Y')
                    elif db_field in ['tier', 'years_experience', 'unique_id'] or '_count' in db_field:
                        if value:
                            record_data[db_field] = int(value)
                    elif db_field.endswith('_usd') or db_field in ['initiation_fee', 'monthly_recurring_revenue']:
                        if value:
                            # Remove currency symbols and commas
                            value = value.replace('$', '').replace(',', '')
                            record_data[db_field] = float(value)
                    elif db_field in ['b2b_call_center_vsa', 'rejected_by_presenter', 'lion_flag']:
                        record_data[db_field] = value.lower() in ['true', 'yes', '1', 'checked']
                    else:
                        record_data[db_field] = value if value else None
            
            # Extract key fields for matching
            first_name = record_data.get('first_name', '').strip().lower() if record_data.get('first_name') else ''
            last_name = record_data.get('last_name', '').strip().lower() if record_data.get('last_name') else ''
            phone = record_data.get('phone', '').strip() if record_data.get('phone') else ''
            
            # Try to find existing record by first_name + last_name + phone
            existing_record = None
            if first_name and last_name and phone:
                existing_record = db.query(DataLakeRecord).filter(
                    func.lower(DataLakeRecord.first_name) == first_name,
                    func.lower(DataLakeRecord.last_name) == last_name,
                    DataLakeRecord.phone == phone
                ).first()
            
            if existing_record:
                # Update existing record
                for field, new_value in record_data.items():
                    if field == 'unique_id':
                        continue  # Don't update unique_id
                    
                    current_value = getattr(existing_record, field)
                    
                    # Update logic: overwrite if current has value, append if current is empty
                    if new_value is not None:
                        if current_value:
                            # Overwrite existing data
                            setattr(existing_record, field, new_value)
                        else:
                            # Append to empty field
                            setattr(existing_record, field, new_value)
                
                existing_record.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new record with auto-generated unique_id if not provided
                if 'unique_id' not in record_data or not record_data['unique_id']:
                    record_data['unique_id'] = next_unique_id
                    next_unique_id += 1
                
                db_record = DataLakeRecord(**record_data)
                db.add(db_record)
                imported_count += 1
                
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported": imported_count,
        "updated": updated_count,
        "errors": errors[:10],  # Return first 10 errors
        "total_errors": len(errors)
    }

@router.get("/export-csv")
async def export_csv(
    filters: Optional[str] = None,
    columns: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Export filtered data to CSV"""
    query = db.query(DataLakeRecord)
    
    # Apply filters
    if filters:
        filter_dict = json.loads(filters)
        for field, value in filter_dict.items():
            if hasattr(DataLakeRecord, field) and value:
                query = query.filter(getattr(DataLakeRecord, field) == value)
    
    records = query.all()
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Define columns to export
    if columns:
        column_list = columns.split(',')
    else:
        column_list = [c.name for c in DataLakeRecord.__table__.columns if c.name not in ['id', 'created_at', 'updated_at', 'created_by']]
    
    writer = csv.DictWriter(output, fieldnames=column_list)
    writer.writeheader()
    
    for record in records:
        row_data = {}
        for col in column_list:
            value = getattr(record, col)
            if isinstance(value, datetime):
                row_data[col] = value.strftime('%m/%d/%Y') if 'date' in col else value.strftime('%m/%d/%Y %I:%M %p')
            elif isinstance(value, bool):
                row_data[col] = 'TRUE' if value else 'FALSE'
            else:
                row_data[col] = value
        writer.writerow(row_data)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=data_lake_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.post("/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    """Analyze CSV file and suggest column mappings"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    # Get CSV columns
    csv_columns = reader.fieldnames or []
    
    # Get database columns
    db_columns = [c.name for c in DataLakeRecord.__table__.columns if c.name not in ['id', 'created_at', 'updated_at', 'created_by']]
    
    # Suggest mappings
    suggestions = {}
    for csv_col in csv_columns:
        csv_col_lower = csv_col.lower().replace(' ', '_').replace('-', '_')
        
        # Try exact match
        if csv_col_lower in db_columns:
            suggestions[csv_col] = csv_col_lower
        # Try partial matches
        else:
            for db_col in db_columns:
                if csv_col_lower in db_col or db_col in csv_col_lower:
                    suggestions[csv_col] = db_col
                    break
    
    return {
        "csv_columns": csv_columns,
        "db_columns": db_columns,
        "suggestions": suggestions
    } 