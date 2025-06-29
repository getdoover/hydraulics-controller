"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from hydraulics_controller.application import HydraulicsControllerApplication
    assert HydraulicsControllerApplication

def test_config():
    from hydraulics_controller.app_config import HydraulicsControllerConfig

    config = HydraulicsControllerConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from hydraulics_controller.app_ui import HydraulicsControllerUI
    assert HydraulicsControllerUI

def test_state():
    from hydraulics_controller.app_state import HydraulicsControllerState
    assert HydraulicsControllerState