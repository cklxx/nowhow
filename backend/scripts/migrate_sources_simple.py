#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import yaml
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import init_database
from repositories.db_source_repository import DatabaseSourceRepository
from models.source_config import SourceConfig, SourceType, ContentType


async def migrate_yaml_to_db():
    """Migrate YAML sources to database"""
    print("Starting source migration...")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("Database initialized")
    
    # Initialize repository
    db_repo = DatabaseSourceRepository()
    
    # Load YAML file
    yaml_file = backend_dir / "sources_premium.yml"
    if not yaml_file.exists():
        print(f"YAML file not found: {yaml_file}")
        return
    
    print(f"Loading sources from: {yaml_file}")
    
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    sources = []
    migrated_count = 0
    
    # Process RSS feeds
    if 'sources' in data and 'rss_feeds' in data['sources']:
        for source in data['sources']['rss_feeds']:
            try:
                # Map category to content type
                category = source.get('category', 'news')
                content_type_mapping = {
                    'research': 'research',
                    'news': 'news', 
                    'blog': 'blog',
                    'analysis': 'article',
                    'education': 'article',
                    'industry': 'news',
                    'cloud': 'article',
                    'agents': 'research'
                }
                
                # Create source data
                source_data = {
                    'id': source['id'],
                    'name': source['name'],
                    'url': source['url'],
                    'type': 'rss',
                    'content_type': content_type_mapping.get(category, 'article'),
                    'description': source.get('description', ''),
                    'crawl_config': {
                        'timeout': 30,
                        'priority': source.get('priority', 'medium'),
                        'verified': source.get('verified', False),
                        'requires_parsing': source.get('requires_parsing', False)
                    },
                    'auth_config': {},
                    'content_selectors': {},
                    'is_active': True,
                    'is_built_in': True,
                    'created_by': 'system'
                }
                
                # Check if exists
                existing = await db_repo.get_by_id(source_data['id'])
                if existing:
                    print(f"Source already exists, skipping: {source_data['name']}")
                    continue
                
                # Create source
                await db_repo.create(source_data)
                migrated_count += 1
                print(f"Migrated source: {source_data['name']}")
                
            except Exception as e:
                print(f"Failed to migrate source {source.get('name', 'Unknown')}: {e}")
    
    # Process websites
    if 'sources' in data and 'websites' in data['sources']:
        for source in data['sources']['websites']:
            try:
                source_data = {
                    'id': source['id'],
                    'name': source['name'],
                    'url': source['url'],
                    'type': 'website',
                    'content_type': 'research',
                    'description': source.get('description', ''),
                    'crawl_config': {
                        'timeout': 30,
                        'priority': source.get('priority', 'medium'),
                        'verified': source.get('verified', False),
                        'requires_parsing': True
                    },
                    'auth_config': {},
                    'content_selectors': {},
                    'is_active': True,
                    'is_built_in': True,
                    'created_by': 'system'
                }
                
                # Check if exists
                existing = await db_repo.get_by_id(source_data['id'])
                if existing:
                    print(f"Source already exists, skipping: {source_data['name']}")
                    continue
                
                # Create source
                await db_repo.create(source_data)
                migrated_count += 1
                print(f"Migrated website: {source_data['name']}")
                
            except Exception as e:
                print(f"Failed to migrate website {source.get('name', 'Unknown')}: {e}")
    
    print(f"\nMigration completed! Migrated {migrated_count} sources")
    
    # Show statistics
    try:
        stats = await db_repo.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Total sources: {stats['total_sources']}")
        print(f"  Active sources: {stats['active_sources']}")
        print(f"  Built-in sources: {stats['builtin_sources']}")
        
    except Exception as e:
        print(f"Failed to get statistics: {e}")


if __name__ == "__main__":
    asyncio.run(migrate_yaml_to_db())