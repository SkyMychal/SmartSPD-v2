#!/usr/bin/env python3
"""
Kempton Group Trial Account Setup Script
Creates TPA, admin user, and customer service agents for trial testing
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.tpa import TPA
from app.models.user import User, UserRole
from app.models.health_plan import HealthPlan
from app.core.security import get_password_hash
from app.crud.tpa import tpa_crud
from app.crud.user import user_crud
import uuid

def create_kempton_trial_setup():
    """Create Kempton Group trial setup with TPA and users"""
    
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("🚀 Setting up Kempton Group trial account...")
        
        # 1. Check if Kempton Group TPA already exists
        existing_tpa = db.query(TPA).filter(TPA.slug == "kempton-group").first()
        if existing_tpa:
            print("✅ Kempton Group TPA already exists, preserving health plans and documents...")
            # Keep existing health plans and documents, only refresh users if needed
            existing_users = db.query(User).filter(User.tpa_id == existing_tpa.id).all()
            
            # Check if admin user already exists with correct password
            admin_user = db.query(User).filter(
                User.email == "sstillwagon@kemptongroup.com",
                User.tpa_id == existing_tpa.id
            ).first()
            
            if admin_user:
                print("✅ Admin user already exists, skipping user setup")
                print("🏥 Setup complete - preserving all existing data")
                return {
                    "tpa_id": existing_tpa.id,
                    "admin_user_id": admin_user.id,
                    "agent1_user_id": None,
                    "agent2_user_id": None
                }
            else:
                print("⚠️  Refreshing user setup only...")
                for user in existing_users:
                    db.delete(user)
            
            # Use existing TPA
            kempton_tpa = existing_tpa
            print("🏥 Using existing TPA and preserving all health plans/documents")
        else:
            # 2. Create Kempton Group TPA
            kempton_tpa_data = {
                "id": str(uuid.uuid4()),
                "name": "Kempton Group",
                "slug": "kempton-group",
                "email": "admin@kemptongroup.com",
                "phone": "+1-555-KEMPTON",
                "address_line1": "123 Trial Street",
                "city": "Demo City",
                "state": "TX",
                "zip_code": "75001",
                "country": "USA",
                "subscription_tier": "trial",
                "max_users": 10,
                "max_health_plans": 5,
                "max_documents": 50,
                "settings": {
                    "trial_account": True,
                    "trial_start_date": datetime.utcnow().isoformat(),
                    "trial_end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "features_enabled": [
                        "document_upload",
                        "rag_queries", 
                        "analytics",
                        "user_management",
                        "health_plan_management"
                    ]
                },
                "branding": {
                    "company_name": "Kempton Group",
                    "primary_color": "#007bff",
                    "logo_url": ""
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            kempton_tpa = TPA(**kempton_tpa_data)
            db.add(kempton_tpa)
            db.commit()
            db.refresh(kempton_tpa)
            
            print(f"✅ Created Kempton Group TPA (ID: {kempton_tpa.id})")
        
        # 3. Create Admin User
        admin_user_data = {
            "id": str(uuid.uuid4()),
            "tpa_id": kempton_tpa.id,
            "email": "sstillwagon@kemptongroup.com",
            "hashed_password": get_password_hash("temp123"),
            "first_name": "Kempton",
            "last_name": "Administrator",
            "phone": "+1-555-ADMIN",
            "department": "Administration",
            "title": "TPA Administrator",
            "role": UserRole.TPA_ADMIN,
            "permissions": [
                "admin",
                "user_management",
                "health_plan_management",
                "document_management",
                "analytics",
                "system_settings"
            ],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        admin_user = User(**admin_user_data)
        db.add(admin_user)
        
        # 4. Create Customer Service Agent 1
        agent1_user_data = {
            "id": str(uuid.uuid4()),
            "tpa_id": kempton_tpa.id,
            "email": "agent1@kemptongroup.com",
            "hashed_password": get_password_hash("KemptonAgent1!"),
            "first_name": "Sarah",
            "last_name": "Johnson",
            "phone": "+1-555-AGENT1",
            "department": "Customer Service",
            "title": "Customer Service Agent",
            "role": UserRole.CS_AGENT,
            "permissions": [
                "analytics",
                "query_system",
                "member_assistance"
            ],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        agent1_user = User(**agent1_user_data)
        db.add(agent1_user)
        
        # 5. Create Customer Service Agent 2
        agent2_user_data = {
            "id": str(uuid.uuid4()),
            "tpa_id": kempton_tpa.id,
            "email": "agent2@kemptongroup.com",
            "hashed_password": get_password_hash("KemptonAgent2!"),
            "first_name": "Michael",
            "last_name": "Chen",
            "phone": "+1-555-AGENT2",
            "department": "Customer Service",
            "title": "Senior Customer Service Agent",
            "role": UserRole.CS_AGENT,
            "permissions": [
                "analytics",
                "query_system",
                "member_assistance"
            ],
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        agent2_user = User(**agent2_user_data)
        db.add(agent2_user)
        
        db.commit()
        
        print("✅ Created trial users:")
        print(f"   📧 Admin: sstillwagon@kemptongroup.com / temp123")
        print(f"   📧 Agent 1: agent1@kemptongroup.com / KemptonAgent1!")
        print(f"   📧 Agent 2: agent2@kemptongroup.com / KemptonAgent2!")
        
        # 6. Display setup summary
        print("\n🎉 Kempton Group Trial Setup Complete!")
        print("=" * 50)
        print(f"TPA Name: {kempton_tpa.name}")
        print(f"TPA ID: {kempton_tpa.id}")
        print(f"Trial Period: 30 days from {datetime.utcnow().strftime('%Y-%m-%d')}")
        print(f"Max Users: {kempton_tpa.max_users}")
        print(f"Max Health Plans: {kempton_tpa.max_health_plans}")
        print(f"Max Documents: {kempton_tpa.max_documents}")
        print("\nLogin Credentials:")
        print("─" * 30)
        print("Admin Account:")
        print("  Email: sstillwagon@kemptongroup.com")
        print("  Password: temp123")
        print("  Role: TPA Administrator")
        print("  Permissions: Full admin access")
        print("\nAgent Accounts:")
        print("  Email: agent1@kemptongroup.com")
        print("  Password: KemptonAgent1!")
        print("  Name: Sarah Johnson")
        print("  Role: Customer Service Agent")
        print("")
        print("  Email: agent2@kemptongroup.com")
        print("  Password: KemptonAgent2!")
        print("  Name: Michael Chen")
        print("  Role: Senior Customer Service Agent")
        print("\n🚀 Ready for testing!")
        print("Next steps:")
        print("1. Login as admin to upload health plan documents")
        print("2. Login as agents to test query functionality")
        print("3. Test document upload and processing")
        print("4. Test RAG query system with feedback")
        
        return {
            "tpa_id": kempton_tpa.id,
            "admin_user_id": admin_user.id,
            "agent1_user_id": agent1_user.id,
            "agent2_user_id": agent2_user.id
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error setting up Kempton Group trial: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    try:
        setup_result = create_kempton_trial_setup()
        print(f"\n✅ Setup completed successfully!")
        print(f"TPA ID: {setup_result['tpa_id']}")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)