#!/usr/bin/env python3
"""
Create health plans for the uploaded documents - Lockhart and Spooner
"""
import sys
import os
from datetime import datetime, date

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import SessionLocal
from app.models.health_plan import HealthPlan
from app.models.tpa import TPA

def create_health_plans():
    """Create health plans for Lockhart and Spooner documents"""
    print("🏥 Creating Health Plans for Uploaded Documents")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get the Kempton TPA
        kempton_tpa = db.query(TPA).filter(TPA.name.like('%Kempton%')).first()
        if not kempton_tpa:
            print("❌ Kempton TPA not found")
            return
        
        print(f"✅ Found TPA: {kempton_tpa.name}")
        print(f"   TPA ID: {kempton_tpa.id}")
        
        # Create health plans for the documents we have
        health_plans = [
            {
                "name": "Lockhart ISD Group Health Plan",
                "plan_number": "LOCKHART-2024",
                "plan_year": 2024,
                "effective_date": date(2024, 1, 1),
                "plan_type": "Group Health Plan",
                "description": "Lockhart Independent School District Group Health Plan",
                "is_active": True,
                "tpa_id": kempton_tpa.id
            },
            {
                "name": "Spooner Inc Employee Benefits Plan",
                "plan_number": "SPOONER-2024", 
                "plan_year": 2024,
                "effective_date": date(2024, 1, 1),
                "plan_type": "Employee Benefits Plan",
                "description": "Spooner, Inc. Employee Benefits Program",
                "is_active": True,
                "tpa_id": kempton_tpa.id
            }
        ]
        
        created_plans = []
        for plan_data in health_plans:
            # Check if plan already exists
            existing = db.query(HealthPlan).filter(
                HealthPlan.plan_number == plan_data["plan_number"],
                HealthPlan.tpa_id == kempton_tpa.id
            ).first()
            
            if existing:
                print(f"⚠️  Health plan {plan_data['name']} already exists")
                created_plans.append(existing)
                continue
            
            # Create new health plan
            health_plan = HealthPlan(**plan_data)
            db.add(health_plan)
            db.commit()
            db.refresh(health_plan)
            
            created_plans.append(health_plan)
            print(f"✅ Created: {health_plan.name}")
            print(f"   Plan Number: {health_plan.plan_number}")
            print(f"   Plan ID: {health_plan.id}")
            print()
        
        print(f"🎉 Health Plans Ready: {len(created_plans)} plans available")
        print()
        print("📋 Summary:")
        for plan in created_plans:
            print(f"   • {plan.name} ({plan.plan_number})")
        
        print(f"\n✅ Chat interface can now select from these health plans!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_health_plans()