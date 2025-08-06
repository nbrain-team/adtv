# Campaign Form Frontend Updates

## Required Changes to Campaign Creation Form

### 1. Form Field Order and Logic

**Step 1: Basic Information**
- Campaign Name
- Associate Producer Name (changed from "Campaign Owner Name")
- Associate Producer Email
- Associate Producer Phone
- Video Link
- Event Info Link
- City (new separate field)
- State (new separate field)
- Launch Date

**Step 2: Event Type Selection (MUST BE FIRST)**
- Event Type: Virtual or In-Person (Radio buttons or Select)

**Step 3: Event-Type Specific Fields**

#### If "In-Person" is selected, show:
- **Date/Time Slot 1** (Required)
  - Date 1 (date picker)
  - Time 1 (time picker)
- **Date/Time Slot 2** (Optional)
  - Date 2 (date picker)
  - Time 2 (time picker)
- **Hotel Name** (text input)
- **Hotel Address** (text input)
- **Calendly Link** (URL input - single link for in-person)

#### If "Virtual" is selected, show:
- **Date/Time/Calendly Slot 1** (Required)
  - Date 1 (date picker)
  - Time 1 (time picker)
  - Calendly Link 1 (URL input)
- **Date/Time/Calendly Slot 2** (Optional)
  - Date 2 (date picker)
  - Time 2 (time picker)
  - Calendly Link 2 (URL input)
- **Date/Time/Calendly Slot 3** (Optional)
  - Date 3 (date picker)
  - Time 3 (time picker)
  - Calendly Link 3 (URL input)

**Step 4: Locations to Scrape**
- Label: "Locations to Scrape" (changed from "Target Cities")
- Keep as multi-line text area

### 2. Data Structure to Send

```typescript
interface EventSlot {
  date: string;  // Format: "YYYY-MM-DD" or formatted date string
  time: string;  // Format: "HH:MM AM/PM"
  calendly_link?: string;  // Optional, mainly for virtual events
}

interface CampaignFormData {
  name: string;
  owner_name: string;  // Associate Producer Name
  owner_email: string;
  owner_phone?: string;
  video_link?: string;
  event_link?: string;
  city?: string;  // New field
  state?: string;  // New field
  launch_date: string;
  event_type: 'virtual' | 'in_person';
  
  // New structure for event slots
  event_slots: EventSlot[];
  
  // Keep these for backward compatibility (can be derived from event_slots)
  event_date: string;  // Use first slot's date
  event_times: string[];  // Extract times from slots
  
  target_cities?: string;  // Locations to Scrape
  hotel_name?: string;  // Only for in-person
  hotel_address?: string;  // Only for in-person
  calendly_link?: string;  // Main link for in-person events
}
```

### 3. Form Validation Rules

- **Event Type** must be selected before showing date/time fields
- **In-Person Events:**
  - At least 1 date/time slot required
  - Maximum 2 date/time slots
  - Hotel Name and Address required
  - Single Calendly Link optional
- **Virtual Events:**
  - At least 1 date/time/calendly slot required  
  - Maximum 3 date/time/calendly slots
  - Each slot must have its own Calendly link

### 4. Example Implementation

```typescript
const [eventType, setEventType] = useState<'virtual' | 'in_person' | ''>('');
const [eventSlots, setEventSlots] = useState<EventSlot[]>([
  { date: '', time: '', calendly_link: '' }
]);

// Add slot
const addEventSlot = () => {
  const maxSlots = eventType === 'in_person' ? 2 : 3;
  if (eventSlots.length < maxSlots) {
    setEventSlots([...eventSlots, { date: '', time: '', calendly_link: '' }]);
  }
};

// Remove slot
const removeEventSlot = (index: number) => {
  if (eventSlots.length > 1) {
    setEventSlots(eventSlots.filter((_, i) => i !== index));
  }
};

// On submit, populate backward compatibility fields
const handleSubmit = () => {
  const formData = {
    ...otherFields,
    event_slots: eventSlots,
    // For backward compatibility
    event_date: eventSlots[0]?.date || new Date().toISOString(),
    event_times: eventSlots.map(slot => slot.time).filter(Boolean),
  };
  
  // Send to API
  api.post('/api/campaigns', formData);
};
```

### 5. Mail Merge Fields Generated

The backend will automatically generate these mail merge fields:
- `[[City]]` - From city field
- `[[State]]` - From state field
- `[[Date1]]`, `[[Time1]]` - From first event slot
- `[[Date2]]`, `[[Time2]]` - From second event slot  
- `[[Date3]]`, `[[Time3]]` - From third event slot (virtual only)
- `[[Calendly Link 1]]`, `[[Calendly Link 2]]`, `[[Calendly Link 3]]` - For virtual events
- `[[Hotel Name]]`, `[[Hotel Address]]` - For in-person events
- `[[Associate Name]]`, `[[Associate email]]`, `[[Associate Phone]]` - From owner fields

### 6. UI/UX Recommendations

1. Use conditional rendering to show/hide fields based on event type
2. Add "Add Another Date/Time" button (with limits)
3. Show clear labels like "Date/Time Option 1", "Date/Time Option 2"
4. For virtual events, group each slot's fields together
5. Add helper text explaining the purpose of each field
6. Consider using a stepper/wizard format for better flow 