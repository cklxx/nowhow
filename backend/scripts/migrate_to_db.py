#!/usr/bin/env python3
"""
数据迁移脚本：将文件存储的数据迁移到 SQLite 数据库
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import init_database
from database.models import SourceModel, ArticleModel, WorkflowModel
from repositories.db_source_repository import DatabaseSourceRepository
from services.db_storage_service import DatabaseStorageService
from utils.source_manager import SourceManager

async def migrate_sources():
    """迁移信源配置"""
    print("🔄 开始迁移信源配置...")
    
    # 初始化旧的文件管理器
    source_manager = SourceManager()
    
    # 初始化新的数据库存储库
    db_repo = DatabaseSourceRepository()
    
    # 获取所有现有信源
    file_sources = source_manager.get_all_sources(include_inactive=True)
    
    migrated_count = 0
    for source in file_sources:
        try:
            # 检查数据库中是否已存在
            existing = await db_repo.get_by_id(source.id)
            if existing:
                print(f"⏭️  信源已存在，跳过: {source.name}")
                continue
            
            # 创建新的信源记录
            source_data = source.model_dump()
            await db_repo.create(source_data)
            
            migrated_count += 1
            print(f"✅ 已迁移信源: {source.name}")
            
        except Exception as e:
            print(f"❌ 迁移信源失败 {source.name}: {e}")
    
    print(f"✅ 信源配置迁移完成，共迁移 {migrated_count} 个信源")

async def migrate_articles():
    """迁移文章数据"""
    print("🔄 开始迁移文章数据...")
    
    # 初始化数据库存储服务
    db_storage = DatabaseStorageService()
    
    # 查找所有文章文件
    data_dir = backend_dir / "data"
    articles_dir = data_dir / "articles"
    
    if not articles_dir.exists():
        print("📁 文章目录不存在，跳过文章迁移")
        return
    
    migrated_count = 0
    for json_file in articles_dir.glob("articles_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取 workflow_id
            filename = json_file.stem
            parts = filename.split('_')
            if len(parts) >= 3:
                # 格式: articles_timestamp_workflow_id
                workflow_id = parts[-1]
            else:
                workflow_id = f"migrated_{filename}"
            
            # 处理文章数据
            articles = []
            if isinstance(data, dict):
                articles = data.get('articles', [])
            elif isinstance(data, list):
                articles = data
            
            if articles:
                await db_storage.save_generated_articles(workflow_id, articles)
                migrated_count += len(articles)
                print(f"✅ 已迁移 {len(articles)} 篇文章 (workflow: {workflow_id})")
            
        except Exception as e:
            print(f"❌ 迁移文章文件失败 {json_file}: {e}")
    
    print(f"✅ 文章数据迁移完成，共迁移 {migrated_count} 篇文章")

async def migrate_workflows():
    """迁移工作流数据"""
    print("🔄 开始迁移工作流数据...")
    
    # 初始化数据库存储服务
    db_storage = DatabaseStorageService()
    
    # 查找所有工作流文件
    data_dir = backend_dir / "data"
    workflows_dir = data_dir / "workflows"
    
    if not workflows_dir.exists():
        print("📁 工作流目录不存在，跳过工作流迁移")
        return
    
    migrated_count = 0
    for json_file in workflows_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            workflow_id = data.get('id', json_file.stem)
            
            # 创建工作流状态
            workflow_state = {
                'id': workflow_id,
                'name': data.get('name', f'Migrated Workflow {workflow_id}'),
                'description': data.get('description', ''),
                'config': data.get('config', {}),
                'status': data.get('status', 'completed'),
                'progress': data.get('progress', 100.0),
                'current_step': data.get('current_step', ''),
                'sources_count': data.get('sources_count', 0),
                'crawled_count': data.get('crawled_count', 0),
                'processed_count': data.get('processed_count', 0),
                'articles_generated': data.get('articles_generated', 0),
                'results': data.get('results', {}),
                'error_log': data.get('error_log', []),
                'execution_time': data.get('execution_time')
            }
            
            await db_storage.save_workflow_state(workflow_id, workflow_state)
            migrated_count += 1
            print(f"✅ 已迁移工作流: {workflow_id}")
            
        except Exception as e:
            print(f"❌ 迁移工作流失败 {json_file}: {e}")
    
    print(f"✅ 工作流数据迁移完成，共迁移 {migrated_count} 个工作流")

def create_default_sources():
    """创建默认的内置信源"""
    print("🔄 创建默认信源配置...")
    
    # 使用文件管理器的内置信源初始化功能
    source_manager = SourceManager()
    source_manager._init_builtin_sources()
    
    print("✅ 默认信源配置创建完成")

async def main():
    """主迁移流程"""
    print("🚀 开始数据库迁移...")
    print(f"📁 后端目录: {backend_dir}")
    
    try:
        # 初始化数据库
        print("🔧 初始化数据库...")
        db_manager = init_database()
        print("✅ 数据库初始化完成")
        
        # 执行迁移
        await migrate_sources()
        await migrate_articles()
        await migrate_workflows()
        
        print("\n🎉 所有数据迁移完成!")
        
        # 显示统计信息
        print("\n📊 迁移统计:")
        
        # 统计信源
        db_repo = DatabaseSourceRepository()
        sources = await db_repo.get_all()
        print(f"   信源总数: {len(sources)}")
        
        # 统计文章
        db_storage = DatabaseStorageService()
        articles = await db_storage.load_generated_articles()
        print(f"   文章总数: {len(articles)}")
        
        # 统计工作流
        session = db_manager.get_sync_session()
        try:
            workflow_count = session.query(WorkflowModel).count()
            print(f"   工作流总数: {workflow_count}")
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())