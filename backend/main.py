#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import multiprocessing

# Add project root to Python path
backend_dir = Path(__file__).parent.absolute()
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

def main():
    """Start the API server"""
    import uvicorn
    
    # Only print from the original process to avoid duplicates
    if multiprocessing.current_process().name == 'MainProcess':
        print(f"Starting backend from backend/main.py")
        print(f"Project root: {project_root}")
        print(f"Working directory: {os.getcwd()}")
    
    # Stay in backend directory for proper module resolution
    os.chdir(backend_dir)
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True, log_config=None)

if __name__ == "__main__":
    main()
