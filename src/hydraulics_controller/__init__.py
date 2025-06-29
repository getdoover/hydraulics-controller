from pydoover.docker import run_app

from .application import HydraulicsControllerApplication
from .app_config import HydraulicsControllerConfig

def main():
    """
    Run the application.
    """
    run_app(HydraulicsControllerApplication(config=HydraulicsControllerConfig()))
