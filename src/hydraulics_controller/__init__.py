from pydoover.docker import run_app

from .application import HydraulicsControllerApplication


def main():
    """Run the application."""
    run_app(HydraulicsControllerApplication())
