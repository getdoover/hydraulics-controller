from pathlib import Path

from pydoover import ui

from .app_config import HydraulicsControllerConfig
from .utils import get_remote_key


def _option(name: str, label: str) -> ui.Option:
    # Option derives its value from the label; override it so the values
    # published to tags stay "off"/"forward"/"reverse" whatever the labels are.
    option = ui.Option(label)
    option.name = name
    return option


class HydraulicsControllerUI(ui.UI):
    config: HydraulicsControllerConfig

    async def setup(self):
        # config remote element -> Select interaction
        self.remotes = {}
        for remote in self.config.hydraulic_remotes.elements:
            remote_key = get_remote_key(remote)

            options = [
                _option("off", "Off"),
                _option("forward", remote.forward_label.value),
            ]
            if remote.two_way.value:
                options.append(_option("reverse", remote.reverse_label.value))

            self.remotes[remote] = self.add_element(
                ui.Select(
                    remote.name.value,
                    name=remote_key,
                    options=options,
                    default="off",
                )
            )

        if self.config.motor_controller.value is not None:
            self.add_element(
                ui.Select(
                    "Motor Control Mode",
                    name="motor_control_mode",
                    options=[
                        _option("auto", "Auto"),
                        _option("manual", "Manual"),
                        _option("off", "Off"),
                    ],
                    default="auto",
                )
            )

def export():
    HydraulicsControllerUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "hydraulics_controller",
    )
