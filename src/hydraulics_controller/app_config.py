from pathlib import Path

from pydoover import config


class HydraulicRemote(config.Object):
    name = config.String("Name", description="Name for this remote")
    two_way = config.Boolean("Two Way", default=True, description="Is this a two way remote?")
    forward_label = config.String("Forward Label", default="Forward", description="E.g. Gate 'Up'/'Down', 'Engage', 'In'/'Out' etc.")
    reverse_label = config.String("Reverse Label", default="Reverse", description="Same as forward label. Only applicable for two way remotes.")
    forward_pin = config.Integer("Forward Pin", description="Pin number for forward action")
    reverse_pin = config.Integer("Reverse Pin", default=None, description="Pin number for reverse action, only applicable for two way remotes")
    priority = config.Integer("Priority", default=1, description="Lower number = higher priority. If multiple remotes are active, the one with the lowest priority will be stopped.")


class HydraulicsControllerConfig(config.Schema):
    hydraulic_remotes = config.Array(
        "Hydraulic Remotes",
        element=HydraulicRemote("Hydraulic Remote"),
    )
    max_concurrent_remotes = config.Integer(
        "Max Concurrent Remotes",
        default=1,
        description="Maximum number of remotes to run concurrently",
    )
    motor_controller = config.Application(
        "Motor Controller",
        description="(Optional) The motor controller powering the hydraulic pump",
        default=None,
    )


def export():
    HydraulicsControllerConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "hydraulics_controller",
    )


if __name__ == "__main__":
    export()
