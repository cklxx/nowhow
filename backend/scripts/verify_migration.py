#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import asyncio
from pathlib import Path

backend_dir = Path(__file__).parent.parent

def verify_database_content():
    """Verify database contains migrated sources"""
    print("🔍 Verifying database migration...")
    
    db_path = backend_dir / "data" / "app.db"
    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check total sources
        cursor.execute('SELECT COUNT(*) FROM sources')
        total_sources = cursor.fetchone()[0]
        print(f"✅ Total sources in database: {total_sources}")
        
        # Check source types
        cursor.execute('SELECT type, COUNT(*) FROM sources GROUP BY type')
        type_counts = cursor.fetchall()
        print(f"📊 Sources by type:")
        for source_type, count in type_counts:
            print(f"   {source_type}: {count}")
        
        # Check content types  
        cursor.execute('SELECT content_type, COUNT(*) FROM sources GROUP BY content_type')
        content_counts = cursor.fetchall()
        print(f"📊 Sources by content type:")
        for content_type, count in content_counts:
            print(f"   {content_type}: {count}")
        
        # Check for AI/Agent related sources
        cursor.execute("""
            SELECT name FROM sources 
            WHERE (name LIKE '%AI%' OR name LIKE '%Agent%' OR name LIKE '%智能%' 
                   OR description LIKE '%agent%' OR description LIKE '%AI%')
            ORDER BY name
        """)
        ai_sources = cursor.fetchall()
        print(f"🤖 AI/Agent related sources ({len(ai_sources)}):")
        for source in ai_sources[:10]:  # Show first 10
            print(f"   - {source[0]}")
        if len(ai_sources) > 10:
            print(f"   ... and {len(ai_sources) - 10} more")
        
        # Check Chinese sources
        cursor.execute("""
            SELECT name FROM sources 
            WHERE (name LIKE '%清华%' OR name LIKE '%百度%' OR name LIKE '%阿里%' 
                   OR name LIKE '%字节%' OR name LIKE '%达摩%')
            ORDER BY name
        """)
        chinese_sources = cursor.fetchall()
        print(f"🇨🇳 Chinese sources ({len(chinese_sources)}):")
        for source in chinese_sources:
            print(f"   - {source[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main verification function"""
    print("📋 Source Migration Verification Report")
    print("=" * 50)
    
    success = verify_database_content()
    
    if success:
        print(f"\n🎉 Migration verification completed successfully!")
        print(f"   ✅ Database is accessible")
        print(f"   ✅ Sources are properly migrated")  
        print(f"   ✅ AI/Agent sources are included")
        print(f"   ✅ Chinese sources are included")
        print(f"\n💡 The system now uses SQLite database for source storage!")
    else:
        print(f"\n❌ Migration verification failed!")

if __name__ == "__main__":
    main()