#!/usr/bin/env python3
"""
Database migration script for audio-video-fix merge.
Recreates database schema with new Character model and scene fields.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database import Base, engine
from models import SessionModel, SceneModel, Character


def migrate():
    """
    Recreate database schema with new models.
    WARNING: This will drop all existing tables and data!
    """
    print("🔄 Starting database migration...")
    print("⚠️  WARNING: This will drop all existing data!")
    
    confirm = input("Type 'yes' to continue: ").strip()
    if confirm.lower() != "yes":
        print("Migration cancelled.")
        return False
    
    try:
        # Drop all existing tables
        print("🗑️  Dropping existing tables...")
        Base.metadata.drop_all(engine)
        
        # Create new schema
        print("✨ Creating new tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Database migration completed successfully!")
        print("\nNew schema includes:")
        print("  ✓ Character model (for AI characters)")
        print("  ✓ SessionModel.character_id (FK to Character)")
        print("  ✓ SceneModel.act (hook/main/cta)")
        print("  ✓ SceneModel.action (for image generation)")
        print("  ✓ SceneModel.dialogue (for TTS)")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
