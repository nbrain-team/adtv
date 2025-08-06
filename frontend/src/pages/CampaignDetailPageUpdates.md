# CampaignDetailPage.tsx Updates

## 1. Add Import
After line 22, add:
```typescript
import { EmailCampaignTab } from '../components/EmailCampaignTab';
```

## 2. Add State for Email Selection
After line 249 (selectedContacts state), add:
```typescript
const [selectedForEmail, setSelectedForEmail] = useState<Contact[]>([]);
```

## 3. Update Tab Triggers (lines 936-940)
Replace:
```typescript
<Tabs.Trigger value="email-templates">Email Templates</Tabs.Trigger>
<Tabs.Trigger value="emails">Generate Emails</Tabs.Trigger>
```
With:
```typescript
<Tabs.Trigger value="email-campaign">
    Email Campaign {selectedForEmail.length > 0 && `(${selectedForEmail.length})`}
</Tabs.Trigger>
```

## 4. Add "Send Email" Action to Contacts Tab
In the Actions dropdown (around line 1400), add:
```typescript
<DropdownMenu.Item 
    onClick={() => {
        const selected = contacts.filter(c => selectedContacts.has(c.id));
        setSelectedForEmail(selected);
        setActiveTab('email-campaign');
    }}
    disabled={selectedContacts.size === 0}
>
    <EnvelopeClosedIcon />
    Send Email to Selected
</DropdownMenu.Item>
```

## 5. Add "Send Email" Action to RSVP Tab
In the RSVP Actions dropdown (around line 1650), add similar code:
```typescript
<DropdownMenu.Item 
    onClick={() => {
        const selected = contacts.filter(c => selectedContacts.has(c.id) && c.is_rsvp);
        setSelectedForEmail(selected);
        setActiveTab('email-campaign');
    }}
    disabled={selectedContacts.size === 0}
>
    <EnvelopeClosedIcon />
    Send Email to Selected RSVPs
</DropdownMenu.Item>
```

## 6. Replace Email Templates and Generate Emails Tab Content
Replace the entire content of both tabs (lines 1759-1923) with:
```typescript
{/* Email Campaign Tab */}
<Tabs.Content value="email-campaign">
    <EmailCampaignTab
        campaignId={campaignId}
        campaign={campaign}
        selectedContacts={selectedForEmail}
        onClearSelection={() => {
            setSelectedForEmail([]);
            setSelectedContacts(new Set());
        }}
    />
</Tabs.Content>
```

## 7. Update handleMoveToRSVP Function (around line 620)
Add alert message after successful move:
```typescript
const handleMoveToRSVP = async () => {
    try {
        const contactIds = Array.from(selectedContacts);
        const response = await api.post(`/api/campaigns/${campaignId}/contacts/rsvp`, {
            contact_ids: contactIds,
            is_rsvp: true
        });
        await fetchContacts();
        setSelectedContacts(new Set());
        alert(`Successfully moved ${contactIds.length} contact(s) to RSVP. They remain visible in both Contacts and RSVP tabs.`);
    } catch (err) {
        console.error('Failed to move contacts to RSVP:', err);
        alert('Failed to move contacts to RSVP. Please try again.');
    }
};
``` 