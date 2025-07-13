#!/usr/bin/env python3
"""
清理无用的本地文件夹脚本
数据已迁移到 SQLite 数据库，可以安全删除文件存储
"""

import sys
import shutil
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def cleanup_storage_files():
    """清理已迁移的存储文件"""
    print("🧹 开始清理无用的本地文件夹...")
    
    data_dir = backend_dir / "data"
    
    # 需要清理的目录
    cleanup_dirs = [
        "sources",      # 信源配置（已迁移到数据库）
        "articles",     # 生成的文章（已迁移到数据库） 
        "content",      # 处理后的内容（已迁移到数据库）
        "workflows"     # 工作流状态（已迁移到数据库）
    ]
    
    # 需要保留的目录
    keep_dirs = [
        "logs"          # 日志文件保留
    ]
    
    cleaned_count = 0
    
    for dir_name in cleanup_dirs:
        target_dir = data_dir / dir_name
        if target_dir.exists():
            try:
                # 备份重要文件（如果有的话）
                backup_important_files(target_dir)
                
                # 删除目录
                shutil.rmtree(target_dir)
                print(f"✅ 已清理目录: {target_dir}")
                cleaned_count += 1
            except Exception as e:
                print(f"❌ 清理目录失败 {target_dir}: {e}")
        else:
            print(f"⏭️  目录不存在，跳过: {target_dir}")
    
    # 检查是否有其他文件需要清理
    if data_dir.exists():
        remaining_files = list(data_dir.glob("*.json"))
        for json_file in remaining_files:
            if should_cleanup_file(json_file):
                try:
                    json_file.unlink()
                    print(f"✅ 已清理文件: {json_file}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"❌ 清理文件失败 {json_file}: {e}")
    
    print(f"✅ 清理完成，共清理 {cleaned_count} 个项目")
    
    # 显示保留的目录
    print("\\n📁 保留的目录:")
    for dir_name in keep_dirs:
        keep_dir = data_dir / dir_name
        if keep_dir.exists():
            print(f"   {keep_dir}")
    
    # 显示数据库文件
    db_file = data_dir / "app.db"
    if db_file.exists():
        print(f"\\n💾 数据库文件: {db_file}")
        print(f"   大小: {db_file.stat().st_size} 字节")

def backup_important_files(directory: Path):
    """备份重要文件（如有需要）"""
    # 暂时不需要备份，因为数据已经迁移到数据库
    pass

def should_cleanup_file(file_path: Path) -> bool:
    """判断文件是否应该被清理"""
    filename = file_path.name
    
    # 清理模式匹配的文件
    cleanup_patterns = [
        "crawled_content_*.json",
        "processed_content_*.json", 
        "articles_*.json",
        "workflow_*.json",
        "sources.json"
    ]
    
    for pattern in cleanup_patterns:
        if file_path.match(pattern):
            return True
    
    return False

def main():
    """主清理流程"""
    print("🚀 开始清理迁移后的文件...")
    print(f"📁 后端目录: {backend_dir}")
    
    # 确认操作
    print("\\n⚠️  警告: 此操作将删除已迁移到数据库的文件存储")
    print("   确保数据库迁移已成功完成")
    
    response = input("\\n是否继续清理? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ 取消清理操作")
        return
    
    try:
        cleanup_storage_files()
        print("\\n🎉 清理操作完成!")
        print("\\n📊 当前存储状态:")
        print("   ✅ 信源配置: 存储在 SQLite 数据库")
        print("   ✅ 文章数据: 存储在 SQLite 数据库") 
        print("   ✅ 工作流状态: 存储在 SQLite 数据库")
        print("   ✅ 日志文件: 保留在本地文件系统")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()