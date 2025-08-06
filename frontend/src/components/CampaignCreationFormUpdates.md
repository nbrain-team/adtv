# Campaign Creation Form Updates

## Fields to Add/Update:

### 1. Change "Owner" Label to "Associate"
- Change "Campaign Owner Name" to "Associate Name"
- Change "Campaign Owner Email" to "Associate Email"
- Add "Associate Phone" field

### 2. Add New Mail Merge Fields
- **Video Link** - URL field for the personal video
- **Event Link** - URL field for event information page

### 3. Update Event Times
- Support up to 3 date/time slots
- Each slot should have separate Date and Time fields
- Labels: "Date/Time Option 1", "Date/Time Option 2", "Date/Time Option 3"

## Example Form Structure:

```typescript
interface CampaignFormData {
  name: string;
  owner_name: string;  // Label: "Associate Name"
  owner_email: string; // Label: "Associate Email"
  owner_phone: string; // Label: "Associate Phone"
  video_link: string;  // Label: "Video Link"
  event_link: string;  // Label: "Event Info Link"
  launch_date: string;
  event_type: 'virtual' | 'in_person';
  event_date: string;
  event_times: string[]; // Array of up to 3 time strings
  target_cities: string; // Format: "City, State"
  hotel_name: string;
  hotel_address: string;
  calendly_link: string;
}
```

## Mail Merge Field Reference:

### Campaign Fields (double square brackets):
- `[[VIDEO-LINK]]` - From video_link field
- `[[City]]` - Extracted from target_cities (before comma)
- `[[State]]` - Extracted from target_cities (after comma)
- `[[Event-Link]]` - From event_link field
- `[[Date1]]`, `[[Time1]]` - From event_date + event_times[0]
- `[[Date2]]`, `[[Time2]]` - From event_date + event_times[1]
- `[[Date3]]`, `[[Time3]]` - From event_date + event_times[2]
- `[[Hotel Name]]` - From hotel_name field
- `[[Hotel Address]]` - From hotel_address field
- `[[Associate Name]]` - From owner_name field
- `[[Associate email]]` - From owner_email field
- `[[Associate Phone]]` - From owner_phone field
- `[[Calendly Link]]` - From calendly_link field

### Contact Fields (double curly braces):
- `{{FirstName}}` - Contact's first name
- `{{LastName}}` - Contact's last name
- `{{Neighborhood_1}}` - Contact's neighborhood
- `{{Email}}` - Contact's email
- `{{Company}}` - Contact's company
- `{{Title}}` - Contact's title
- `{{Phone}}` - Contact's phone 