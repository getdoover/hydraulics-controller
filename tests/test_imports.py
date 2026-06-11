"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

import json

from pydoover.config import Schema
from pydoover.tags import Tags
from pydoover.ui import UI


def test_import_app():
    from hydraulics_controller.application import HydraulicsControllerApplication

    assert HydraulicsControllerApplication.config_cls is not None
    assert HydraulicsControllerApplication.tags_cls is not None
    assert HydraulicsControllerApplication.ui_cls is not None


def test_config_schema():
    from hydraulics_controller.app_config import HydraulicsControllerConfig

    assert issubclass(HydraulicsControllerConfig, Schema)

    schema = HydraulicsControllerConfig.to_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "hydraulic_remotes" in schema["properties"]


def test_tags():
    from hydraulics_controller.app_tags import HydraulicsControllerTags

    assert issubclass(HydraulicsControllerTags, Tags)


def test_ui():
    from hydraulics_controller.app_ui import HydraulicsControllerUI

    assert issubclass(HydraulicsControllerUI, UI)


def test_state():
    from hydraulics_controller.app_state import HydraulicsControllerState

    assert HydraulicsControllerState


def test_config_export(tmp_path):
    from hydraulics_controller.app_config import HydraulicsControllerConfig

    fp = tmp_path / "doover_config.json"
    HydraulicsControllerConfig.export(fp, "hydraulics_controller")

    data = json.loads(fp.read_text())
    assert "config_schema" in data["hydraulics_controller"]
    assert "properties" in data["hydraulics_controller"]["config_schema"]
