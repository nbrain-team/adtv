#!/usr/bin/env python3
"""Debug script to check permissions and email templates"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, User, EmailTemplate

def debug_check():
    """Check permissions and templates"""
    db = SessionLocal()
    
    print("=== CHECKING USER PERMISSIONS ===")
    # Check user permissions
    user = db.query(User).filter(User.email == "danny@nbrain.ai").first()
    if user:
        print(f"✅ User found: {user.email}")
        print(f"Role: {user.role}")
        print(f"Permissions: {user.permissions}")
        
        # Check specific permission
        has_ad_traffic = user.permissions.get('ad-traffic', False) if user.permissions else False
        print(f"Has ad-traffic permission: {has_ad_traffic}")
    else:
        print("❌ User danny@nbrain.ai not found!")
    
    print("\n=== CHECKING EMAIL TEMPLATES ===")
    # Check email templates
    templates = db.query(EmailTemplate).all()
    print(f"Total templates in database: {len(templates)}")
    
    if templates:
        print("\nTemplates found:")
        for template in templates:
            print(f"- {template.name} (ID: {template.id}, System: {template.is_system}, Active: {template.is_active})")
    else:
        print("❌ No templates found in database!")
    
    # Check specifically for ADTV templates
    adtv_templates = db.query(EmailTemplate).filter(
        EmailTemplate.category == "ADTV Outreach"
    ).all()
    print(f"\nADTV templates found: {len(adtv_templates)}")
    
    db.close()

if __name__ == "__main__":
    debug_check() 