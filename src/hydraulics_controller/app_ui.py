from pydoover import ui
from .app_config import HydraulicsControllerConfig

def get_remote_key(remote):
    return remote.name.value.lower().replace(" ", "_") 

class HydraulicsControllerUI:
    def __init__(self, config: HydraulicsControllerConfig):

        self.remotes = {}
        for remote in config.hydraulic_remotes.elements:
            remote_key = get_remote_key(remote)

            if remote.two_way.value:
                options = [
                    ui.Option("off", "Off"),
                    ui.Option("forward", remote.forward_label.value),
                    ui.Option("reverse", remote.reverse_label.value),
                ]
            else:
                options = [
                    ui.Option("off", "Off"),
                    ui.Option("forward", remote.forward_label.value),
                ]

            self.remotes[remote] = ui.StateCommand(
                remote_key,
                remote.name.value,
                user_options=options,
                default="off",
            )

        self.motor_control_mode = None
        if config.motor_controller.value is not None:
            self.motor_control_mode = ui.StateCommand(
                "motor_control_mode",
                "Motor Control Mode", 
                user_options=[
                    ui.Option("auto", "Auto"),
                    ui.Option("manual", "Manual"),
                    ui.Option("off", "Off"),
                ]
            )

    def fetch(self):
        return list(self.remotes.values()) + [self.motor_control_mode]

    def update(self):
        pass