import logging
import time
import copy
from pydoover.docker import Application
from pydoover import ui

from .app_config import HydraulicsControllerConfig
from .app_ui import HydraulicsControllerUI, get_remote_key
from .app_state import HydraulicsControllerState

log = logging.getLogger()

def config_to_ui_remote(config_remote, ui):
    remote_key = get_remote_key(config_remote)
    if remote_key not in ui.remotes:
        log.error(f"Remote {remote_key} not found in UI")
        return None
    return ui.remotes[remote_key]

def get_config_remote(config: HydraulicsControllerConfig, remote_key):
    for remote in config.hydraulic_remotes.elements:
        if get_remote_key(remote) == remote_key:
            return remote
    log.error(f"Remote {remote_key} not found in config")
    return None

class HydraulicsControllerApplication(Application):
    config: HydraulicsControllerConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: HydraulicsControllerUI = None
        self.state: HydraulicsControllerState = None

        self._last_pin_write = None

        self.loop_target_period = 0.25  # seconds

    async def setup(self):
        self.ui = HydraulicsControllerUI(config=self.config)
        self.state = HydraulicsControllerState(self)
        self.ui_manager.set_display_name("Hydraulics")
        self.ui_manager.add_children(*self.ui.fetch())
        self.ui.coerce_default_values()

    async def main_loop(self):
        s = await self.state.spin_state()
        log.info(f"State is: {s}")

        await self.update_remote_tags()

        run_motor = None

        if s == "off":
            self.coerce_ui_commands_off()
            await self.write_pins() # Write all pins off

        if s == "error":
            self.coerce_ui_commands_off()
            await self.write_pins() # Write all pins off

        if s == "user_prep":
            run_motor = True
            await self.write_pins() # Write all pins off

        if s == "user_active":
            run_motor = True
            await self.write_pins(self.get_active_pins())
        
        if s == "auto_prep":
            run_motor = True
            self.coerce_ui_commands()
            await self.write_pins() # Write all pins off

        if s == "auto_active":
            run_motor = True
            self.coerce_ui_commands()
            await self.write_pins(self.get_active_pins())

        if s == "test":
            await self.write_pins(self.get_active_pins())


        if run_motor:
            await self.update_motor_control_request("Hydraulics")
        else:
            await self.update_motor_control_request(None)


    async def update_motor_control_request(self, reason=None):
        await self.set_tag_async("run_request_reason", reason, self.config.motor_controller.value)

    async def update_remote_tags(self):
        """Publish tag information about what is happening with the remotes"""

        ## Get all remotes
        remaining_remote_keys = [get_remote_key(remote) for remote in self.config.hydraulic_remotes.elements]
        active_remotes = {}
        if self.state.state in ["auto_active", "test"]:
            ## Merge auto command requests to active remotes
            active_remotes.update(self.get_next_auto_command_requests())
        if self.state.state in ["user_active", "test"]:
            active_remotes.update(self.get_user_commands())

        ## If the state is active, publish the next command requests
        for remote, request_value in active_remotes.items():
            remote_key = get_remote_key(remote)
            await self.set_tag_async(f"{remote_key}", request_value)
            if remote_key in remaining_remote_keys:
                remaining_remote_keys.remove(remote_key)

        ## If there are any remotes left, publish them as "off"
        for remote_key in remaining_remote_keys:
            await self.set_tag_async(f"{remote_key}", "off")

    def coerce_ui_commands_off(self):
        """Coerce all remotes to be off"""
        for remote in self.ui.remotes.values():
            if remote.current_value != "off":
                remote.coerce("off")

    def coerce_ui_commands(self):
        # First coerce all remotes to be off
        self.coerce_ui_commands_off()
        # Cycle through command requests coerce them to be the correct value
        for config_remote, request_value in self.get_next_auto_command_requests().items():
            ui_remote = config_to_ui_remote(config_remote, self.ui)
            ui_remote.coerce(request_value)

    def get_test_command(self):
        motor_control_mode = self.ui_manager.get_command("motor_control_mode")
        if motor_control_mode.current_value == "off":
            return True
        return False
    
    def has_auto_command_requests(self):
        cmds = self.get_auto_command_requests()
        if len(cmds) < 1:
            return False
        ## Otherwise if any of the requests are not "off", return True
        for remote, request_value in cmds.items():
            if request_value != "off":
                return True
        return False
    
    def has_user_command(self):
        if self.ui.motor_control_mode.current_value == "manual":
            return True
        if len(self.get_user_commands()) > 0:
            return True
        return False
    
    def is_user_active_ready(self):
        tag_value = self.get_tag("state", self.config.motor_controller.value)
        if tag_value in ["running_user", "running_auto"]:
            return True
        return False

    def is_auto_active_ready(self):
        ## If the motor controller reports that it is ready, return True
        tag_value = self.get_tag("state", self.config.motor_controller.value)
        if tag_value == "running_auto":
            return True
        return False
    
    def get_user_commands(self):
        commands = {}
        for remote_key, ui_remote in self.ui.remotes.items():
            if ui_remote.current_value != "off":
                config_remote = get_config_remote(self.config, remote_key)
                commands[config_remote] = ui_remote.current_value
        return commands

    def get_auto_command_requests(self):
        commands = {}
        ## cycle through the names of all remotes to find any tags that have a value
        for remote in self.config.hydraulic_remotes.elements:
            remote_key = get_remote_key(remote)
            request_value = self.get_tag(f"request_{remote_key}")
            if self.is_command_request_valid(remote, request_value) and request_value != "off":
                commands[remote] = request_value
        return commands
    
    def is_command_request_valid(self, remote, request_value):
        valid_values = ["forward", "reverse", "off"]
        if remote.forward_label.value:
            valid_values.append(remote.forward_label.value.replace(" ", "_"))
        if remote.reverse_label.value:
            valid_values.append(remote.reverse_label.value.replace(" ", "_"))
        if request_value in valid_values:
            return True
        return False

    def get_next_auto_command_requests(self, max_concurrent_remotes=1):
        ## Get all command requests and sort them by priority
        command_requests = self.get_auto_command_requests()
        sorted_command_request_keys = sorted(command_requests.keys(), key=lambda x: x.priority.value)
        ## If the number of command requests is greater than the max concurrent remotes, return the first max_concurrent_remotes
        if len(sorted_command_request_keys) > max_concurrent_remotes:
            sorted_command_request_keys = sorted_command_request_keys[:max_concurrent_remotes]
        ## Return the full dictionary with only the keys that are in the sorted list
        return {key: command_requests[key] for key in sorted_command_request_keys}
    
    def get_all_remote_pins(self):
        pins = []
        for remote in self.config.hydraulic_remotes.elements:
            pins.append(remote.forward_pin.value)
            if remote.two_way.value:
                pins.append(remote.reverse_pin.value)
        # Remove any Nones and duplicates
        pins = list(set([pin for pin in pins if pin is not None]))
        return pins

    def get_pin_for_remote(self, remote, request_value):
        if request_value in ["forward", remote.forward_label.value]:
            return remote.forward_pin.value
        if remote.two_way.value and request_value in ["reverse", remote.reverse_label.value]:
            return remote.reverse_pin.value
        return None
    
    def get_active_pins(self):
        active_pins = []
        # Cycle through user commands and get the active pins
        for config_remote, request_value in self.get_user_commands().items():
            active_pins.append(self.get_pin_for_remote(config_remote, request_value))
        # Cycle through command requests and get the active pins
        for config_remote, request_value in self.get_next_auto_command_requests().items():
            active_pins.append(self.get_pin_for_remote(config_remote, request_value))

        # Remove any Nones and duplicates
        active_pins = list(set([pin for pin in active_pins if pin is not None]))
        return active_pins
    
    async def write_pins(self, active_pins=[]):
        all_pins = self.get_all_remote_pins()
        outputs = [False] * len(all_pins)

        for pin in active_pins:
            outputs[all_pins.index(pin)] = True

        if self._last_pin_write != outputs:
            self._last_pin_write = outputs
            await self.platform_iface.set_do_async(all_pins, outputs)