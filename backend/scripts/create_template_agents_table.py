#!/usr/bin/env python3
"""
Script to create the template_agents table if it doesn't exist
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, Base, TemplateAgent

def create_template_agents_table():
    """Create the template_agents table"""
    print("Creating template_agents table...")
    
    # Create only the TemplateAgent table
    TemplateAgent.__table__.create(bind=engine, checkfirst=True)
    
    print("Template agents table created successfully!")

if __name__ == "__main__":
    create_template_agents_table() 