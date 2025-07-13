#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信源迁移脚本：将 YAML 配置的信源迁移到 SQLite 数据库
"""

import sys
import os
import yaml
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import init_database
from repositories.db_source_repository import DatabaseSourceRepository
from models.source_config import SourceConfig, SourceType, ContentType


class SourceMigrator:
    """信源迁移器"""
    
    def __init__(self):
        self.db_repo = DatabaseSourceRepository()
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def load_yaml_sources(self, yaml_file: Path) -> List[Dict[str, Any]]:
        """加载 YAML 配置文件中的信源"""
        print(f"📁 读取配置文件: {yaml_file}")
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            sources = []
            
            # 处理 RSS 信源
            if 'sources' in data and 'rss_feeds' in data['sources']:
                for source in data['sources']['rss_feeds']:
                    source_data = self._convert_yaml_source(source, 'rss')
                    if source_data:
                        sources.append(source_data)
            
            # 处理网站信源
            if 'sources' in data and 'websites' in data['sources']:
                for source in data['sources']['websites']:
                    source_data = self._convert_yaml_source(source, 'website')
                    if source_data:
                        sources.append(source_data)
            
            # 处理备用信源
            if 'backup_sources' in data and 'rss_feeds' in data['backup_sources']:
                for source in data['backup_sources']['rss_feeds']:
                    source_data = self._convert_yaml_source(source, 'rss', priority='low')
                    if source_data:
                        sources.append(source_data)
            
            print(f"✅ 成功解析 {len(sources)} 个信源")
            return sources
            
        except Exception as e:
            print(f"❌ 读取 YAML 文件失败: {e}")
            return []
    
    def _convert_yaml_source(self, yaml_source: Dict[str, Any], source_type: str, priority: str = None) -> Optional[Dict[str, Any]]:
        """将 YAML 信源配置转换为数据库格式"""
        try:
            # 映射信源类型
            type_mapping = {
                'rss': SourceType.RSS,
                'website': SourceType.WEBSITE,
                'api': SourceType.API
            }
            
            # 映射内容类型
            category = yaml_source.get('category', 'news')
            content_type_mapping = {
                'research': ContentType.RESEARCH,
                'news': ContentType.NEWS,
                'blog': ContentType.BLOG,
                'analysis': ContentType.ARTICLE,
                'education': ContentType.ARTICLE,
                'industry': ContentType.NEWS,
                'cloud': ContentType.ARTICLE,
                'agents': ContentType.RESEARCH,
                'documentation': ContentType.ARTICLE
            }
            
            # 设置优先级
            if not priority:
                priority = yaml_source.get('priority', 'medium')
            
            # 抓取配置
            crawl_config = {
                'timeout': 30,
                'max_retries': 3,
                'priority': priority,
                'requires_parsing': yaml_source.get('requires_parsing', False),
                'verified': yaml_source.get('verified', False),
                'last_checked': yaml_source.get('last_checked', datetime.now().strftime('%Y-%m-%d'))
            }
            
            # 语言配置
            language = yaml_source.get('language', 'en')
            if language == 'zh':
                crawl_config['language'] = 'chinese'
            
            return {
                'id': yaml_source['id'],
                'name': yaml_source['name'],
                'url': yaml_source['url'],
                'type': type_mapping.get(source_type, SourceType.WEBSITE),
                'content_type': content_type_mapping.get(category, ContentType.ARTICLE),
                'description': yaml_source.get('description', ''),
                'crawl_config': crawl_config,
                'auth_config': {},
                'content_selectors': {},
                'is_active': True,
                'is_built_in': True,  # 来自配置文件的都标记为内置
                'created_by': 'system',
                'quality_score': self._get_quality_score(priority),
                'relevance_score': self._get_relevance_score(category)
            }
            
        except Exception as e:
            print(f"❌ 转换信源配置失败 {yaml_source.get('name', 'Unknown')}: {e}")
            return None
    
    def _get_quality_score(self, priority: str) -> float:
        """根据优先级获取质量分数"""
        score_mapping = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
        return score_mapping.get(priority, 0.7)
    
    def _get_relevance_score(self, category: str) -> float:
        """根据分类获取相关性分数"""
        score_mapping = {
            'research': 0.95,
            'agents': 0.95,
            'news': 0.8,
            'analysis': 0.85,
            'education': 0.8,
            'industry': 0.75,
            'cloud': 0.7
        }
        return score_mapping.get(category, 0.75)
    
    async def migrate_source(self, source_data: Dict[str, Any]) -> bool:
        """迁移单个信源"""
        try:
            # 检查是否已存在
            existing = await self.db_repo.get_by_id(source_data['id'])
            if existing:
                print(f"⏭️  信源已存在，跳过: {source_data['name']}")
                self.skipped_count += 1
                return True
            
            # 创建新信源
            await self.db_repo.create(source_data)
            print(f"✅ 已迁移信源: {source_data['name']}")
            self.migrated_count += 1
            return True
            
        except Exception as e:
            print(f"❌ 迁移信源失败 {source_data['name']}: {e}")
            self.error_count += 1
            return False
    
    async def migrate_all_sources(self) -> None:
        """迁移所有信源"""
        print("🚀 开始信源迁移...")
        
        # 查找所有 YAML 配置文件
        yaml_files = [
            backend_dir / "sources_premium.yml",
            backend_dir / "sources.yml",
            backend_dir / "data" / "sources.yml"
        ]
        
        all_sources = []
        for yaml_file in yaml_files:
            if yaml_file.exists():
                sources = self.load_yaml_sources(yaml_file)
                all_sources.extend(sources)
        
        if not all_sources:
            print("❌ 没有找到可迁移的信源配置")
            return
        
        print(f"📊 找到 {len(all_sources)} 个信源配置，开始迁移...")
        
        # 逐个迁移信源
        for source_data in all_sources:
            await self.migrate_source(source_data)
        
        # 显示迁移结果
        print(f"\n🎉 信源迁移完成!")
        print(f"   ✅ 成功迁移: {self.migrated_count}")
        print(f"   ⏭️  跳过重复: {self.skipped_count}")
        print(f"   ❌ 迁移失败: {self.error_count}")
        print(f"   📊 总计处理: {len(all_sources)}")
    
    async def display_statistics(self) -> None:
        """显示数据库统计信息"""
        print("\n📊 数据库统计信息:")
        
        try:
            stats = await self.db_repo.get_statistics()
            print(f"   总信源数: {stats['total_sources']}")
            print(f"   活跃信源: {stats['active_sources']}")
            print(f"   内置信源: {stats['builtin_sources']}")
            print(f"   用户信源: {stats['user_sources']}")
            
            print(f"\n   按类型分布:")
            for source_type, count in stats['by_type'].items():
                print(f"     {source_type}: {count}")
            
            print(f"\n   按内容类型分布:")
            for content_type, count in stats['by_content_type'].items():
                print(f"     {content_type}: {count}")
                
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")


async def main():
    """主函数"""
    print("🗃️  信源数据库迁移工具")
    print("=" * 50)
    
    try:
        # 初始化数据库
        print("🔧 初始化数据库...")
        init_database()
        print("✅ 数据库初始化完成")
        
        # 创建迁移器
        migrator = SourceMigrator()
        
        # 执行迁移
        await migrator.migrate_all_sources()
        
        # 显示统计信息
        await migrator.display_statistics()
        
        print("\n🎊 迁移任务全部完成!")
        
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())