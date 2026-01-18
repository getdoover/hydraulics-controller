from pathlib import Path

from pydoover import config


class HydraulicsControllerConfig(config.Schema):
    def __init__(self):

        hyd_remote_elem = config.Object("Hydraulic Remote")
        hyd_remote_elem.add_elements(
            config.String("Name", description="Name for this remote"),
            config.Boolean("Two Way", default=True, description="Is this a two way remote?"),
            config.String("Forward Label", default="Forward", description="E.g. Gate 'Up'/'Down', 'Engage', 'In'/'Out' etc."),
            config.String("Reverse Label", default="Reverse", description="Same as forward label. Only applicable for two way remotes."),
            config.Integer("Forward Pin", description="Pin number for forward action"),
            config.Integer("Reverse Pin", description="Pin number for reverse action, only applicable for two way remotes"),
            config.Integer("Priority", default=1,description="Lower number = higher priority. If multiple remotes are active, the one with the lowest priority will be stopped."),
        )
        self.hydraulic_remotes = config.Array(
            "Hydraulic Remotes",
            element=hyd_remote_elem
        )

        self.max_concurrent_remotes = config.Integer(
            "Max Concurrent Remotes",
            description="Maximum number of remotes to run concurrently"
        )

        self.motor_controller = config.Application(
            "Motor Controller",
            description="(Optional) The motor controller powering the hydraulic pump",
            default=None,
        )


def export():
    HydraulicsControllerConfig().export(Path(__file__).parents[2] / "doover_config.json", "hydraulics_controller")

if __name__ == "__main__":
    export()
