#!/usr/bin/env python3
"""
Main entry point for the refactored Crawler AI application
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 