"""
Migration script to add campaign management tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from core.database import engine

def add_campaign_tables():
    """Add all campaign-related tables"""
    
    with engine.connect() as conn:
        # Create clients table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clients (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                industry VARCHAR,
                website VARCHAR,
                description TEXT,
                brand_voice TEXT,
                target_audience JSON,
                keywords JSON,
                competitors JSON,
                social_accounts JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR REFERENCES users(id)
            );
        """))
        
        # Create client_documents table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_documents (
                id VARCHAR PRIMARY KEY,
                client_id VARCHAR REFERENCES clients(id) ON DELETE CASCADE,
                filename VARCHAR NOT NULL,
                file_type VARCHAR,
                file_path VARCHAR,
                content TEXT,
                embedding_id VARCHAR,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by VARCHAR REFERENCES users(id)
            );
        """))
        
        # Create campaigns table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id VARCHAR PRIMARY KEY,
                client_id VARCHAR REFERENCES clients(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                description TEXT,
                topics JSON,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status VARCHAR DEFAULT 'draft',
                submitted_for_approval TIMESTAMP,
                approved_by VARCHAR REFERENCES users(id),
                approved_at TIMESTAMP,
                approval_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR REFERENCES users(id)
            );
        """))
        
        # Create content_items table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS content_items (
                id VARCHAR PRIMARY KEY,
                campaign_id VARCHAR REFERENCES campaigns(id) ON DELETE CASCADE,
                platform VARCHAR NOT NULL,
                content_type VARCHAR,
                title VARCHAR,
                content TEXT NOT NULL,
                media_urls JSON,
                hashtags JSON,
                scheduled_date TIMESTAMP,
                published_date TIMESTAMP,
                status VARCHAR DEFAULT 'draft',
                platform_post_id VARCHAR,
                prompt_used TEXT,
                model_used VARCHAR,
                generation_params JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create content_analytics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS content_analytics (
                id VARCHAR PRIMARY KEY,
                content_item_id VARCHAR REFERENCES content_items(id) ON DELETE CASCADE,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                opens INTEGER DEFAULT 0,
                click_through_rate FLOAT DEFAULT 0.0,
                bounce_rate FLOAT DEFAULT 0.0,
                engagement_rate FLOAT DEFAULT 0.0,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create campaign_analytics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS campaign_analytics (
                id VARCHAR PRIMARY KEY,
                campaign_id VARCHAR REFERENCES campaigns(id) ON DELETE CASCADE,
                total_reach INTEGER DEFAULT 0,
                total_engagement INTEGER DEFAULT 0,
                total_clicks INTEGER DEFAULT 0,
                platform_metrics JSON,
                estimated_value FLOAT DEFAULT 0.0,
                cost FLOAT DEFAULT 0.0,
                roi FLOAT DEFAULT 0.0,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create ai_models table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_models (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                provider VARCHAR,
                model_id VARCHAR,
                default_params JSON,
                cost_per_token FLOAT,
                total_tokens_used INTEGER DEFAULT 0,
                total_cost FLOAT DEFAULT 0.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_created_by ON clients(created_by);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_documents_client ON client_documents(client_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_content_items_campaign ON content_items(campaign_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_content_items_platform ON content_items(platform);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_content_items_status ON content_items(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_content_analytics_content ON content_analytics(content_item_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_campaign_analytics_campaign ON campaign_analytics(campaign_id);"))
        
        conn.commit()
        print("✓ Successfully added campaign tables")

if __name__ == "__main__":
    add_campaign_tables() 