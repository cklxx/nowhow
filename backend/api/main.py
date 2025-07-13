"""
Clean Architecture API with high cohesion and low coupling.
Implements Uncle Bob's Clean Architecture principles.
"""

# Import clean architecture API
from .clean_api import create_clean_app

# Create the app instance
app = create_clean_app()

# For backwards compatibility, also export the app creation function
def create_app():
    """Create the clean architecture app"""
    return create_clean_app()

# Export app for uvicorn
__all__ = ["app", "create_app"]