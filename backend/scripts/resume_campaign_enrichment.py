import os
import sys
import argparse
from datetime import datetime

# Ensure backend package imports work when run on Render shell
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from core.database import SessionLocal, Campaign, CampaignContact
from core.campaign_routes import enrich_campaign_contacts


def resume_enrichment(campaign_id: str, reset_processing: bool = True) -> None:
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"Error: Campaign {campaign_id} not found")
            return

        print(f"Resuming enrichment for campaign: {campaign.id} — {campaign.name}")

        # Reset any contacts stuck in 'processing' to 'pending'
        reset_count = 0
        if reset_processing:
            reset_count = db.query(CampaignContact).filter(
                CampaignContact.campaign_id == campaign_id,
                CampaignContact.enrichment_status == 'processing'
            ).update({CampaignContact.enrichment_status: 'pending'}, synchronize_session=False)
            db.commit()
            print(f"Reset {reset_count} contacts from 'processing' to 'pending'")

        # Ensure status reflects enrichment in progress
        campaign.status = 'enriching'
        db.commit()
        print("Campaign status set to 'enriching'")

    finally:
        db.close()

    # Run enrichment synchronously (same as background task logic)
    # Use campaign owner id if available; the function does not use it directly
    owner_id = campaign.user_id if campaign else "system"
    print(f"Starting enrichment job at {datetime.utcnow().isoformat()}Z ...")
    enrich_campaign_contacts(campaign_id, owner_id)
    print("Enrichment job finished.")


def main():
    parser = argparse.ArgumentParser(description="Resume campaign enrichment after interruption")
    parser.add_argument("--campaign-id", required=True, help="Campaign ID to resume")
    parser.add_argument("--no-reset", action="store_true", help="Do not reset 'processing' contacts to 'pending'")
    args = parser.parse_args()

    resume_enrichment(args.campaign_id, reset_processing=not args.no_reset)


if __name__ == "__main__":
    main()


