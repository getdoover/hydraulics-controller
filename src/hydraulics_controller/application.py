import logging
import time

from pydoover.docker import Application

from .app_config import HydraulicsControllerConfig
from .app_tags import HydraulicsControllerTags
from .app_ui import HydraulicsControllerUI
from .app_state import HydraulicsControllerState
from .utils import get_remote_key

log = logging.getLogger(__name__)


class HydraulicsControllerApplication(Application):
    config_cls = HydraulicsControllerConfig
    tags_cls = HydraulicsControllerTags
    ui_cls = HydraulicsControllerUI

    async def setup(self):
        self.started: float = time.time()
        self.state = HydraulicsControllerState(self)

        self._last_pin_write = None

        self.loop_target_period = 0.25  # seconds

    async def main_loop(self):
        s = await self.state.spin_state()
        log.info(f"State is: {s}")

        await self.update_remote_tags()

        run_motor = False

        if s == "off":
            await self.coerce_ui_commands_off()
            await self.write_pins()  # Write all pins off

        if s == "error":
            await self.coerce_ui_commands_off()
            await self.write_pins()  # Write all pins off

        if s == "user_prep":
            run_motor = True
            await self.write_pins()  # Write all pins off

        if s == "user_active":
            run_motor = True
            await self.write_pins(self.get_active_pins())

        if s == "auto_prep":
            run_motor = True
            await self.coerce_ui_commands()
            await self.write_pins()  # Write all pins off

        if s == "auto_active":
            run_motor = True
            await self.coerce_ui_commands()
            await self.write_pins(self.get_active_pins())

        if s == "test":
            await self.write_pins(self.get_active_pins())

        if run_motor:
            await self.update_motor_control_request("Hydraulics")
        else:
            await self.update_motor_control_request(None)

    @property
    def motor_control_mode(self):
        """The motor control mode Select, or None when no motor controller is configured."""
        try:
            return self.ui.motor_control_mode
        except AttributeError:
            return None

    async def update_motor_control_request(self, reason=None):
        motor_controller = self.config.motor_controller.value
        if motor_controller is None:
            return
        await self.set_tag("run_request_reason", reason, app_key=motor_controller)

    async def update_remote_tags(self):
        """Publish tag information about what is happening with the remotes"""

        ## Get all remotes
        remaining_remotes = list(self.config.hydraulic_remotes.elements)
        if self.state.state == "auto_active":
            ## If the state is active, publish the next command requests
            for remote, request_value in self.get_next_auto_command_requests().items():
                await self.tags.get_tag(get_remote_key(remote)).set(request_value)
                if remote in remaining_remotes:
                    remaining_remotes.remove(remote)

        if self.state.state == "user_active":
            for remote, request_value in self.get_user_commands().items():
                await self.tags.get_tag(get_remote_key(remote)).set(request_value)
                if remote in remaining_remotes:
                    remaining_remotes.remove(remote)

        ## If there are any remotes left, publish them as "off"
        for remote in remaining_remotes:
            await self.tags.get_tag(get_remote_key(remote)).set("off")

    async def coerce_ui_commands_off(self):
        """Coerce all remotes to be off"""
        for remote in self.ui.remotes.values():
            if remote.value != "off":
                await remote.set("off")

    async def coerce_ui_commands(self):
        # Coerce every remote to its requested value, or off if it has no request
        requests = self.get_next_auto_command_requests()
        for config_remote, ui_remote in self.ui.remotes.items():
            target = requests.get(config_remote, "off")
            if ui_remote.value != target:
                await ui_remote.set(target)

    def get_test_command(self):
        motor_control_mode = self.motor_control_mode
        return motor_control_mode is not None and motor_control_mode.value == "off"

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
        motor_control_mode = self.motor_control_mode
        if motor_control_mode is not None and motor_control_mode.value == "manual":
            return True
        if len(self.get_user_commands()) > 0:
            return True
        return False

    def is_user_active_ready(self):
        motor_controller = self.config.motor_controller.value
        if motor_controller is None:
            return True
        tag_value = self.get_tag("state", motor_controller)
        return tag_value in ["running_user", "running_auto"]

    def is_auto_active_ready(self):
        ## If the motor controller reports that it is ready, return True
        motor_controller = self.config.motor_controller.value
        if motor_controller is None:
            return True
        tag_value = self.get_tag("state", motor_controller)
        return tag_value == "running_auto"

    def get_user_commands(self):
        commands = {}
        for config_remote, ui_remote in self.ui.remotes.items():
            if ui_remote.value != "off":
                commands[config_remote] = ui_remote.value
        return commands

    def get_auto_command_requests(self):
        commands = {}
        ## cycle through the names of all remotes to find any tags that have a value
        for remote in self.config.hydraulic_remotes.elements:
            remote_key = get_remote_key(remote)
            request_value = self.tags.get_tag(f"request_{remote_key}").value
            if self.is_command_request_valid(remote, request_value):
                commands[remote] = request_value
        return commands

    def is_command_request_valid(self, remote, request_value):
        valid_values = ["forward", "reverse", "off"]
        if remote.forward_label.value:
            valid_values.append(remote.forward_label.value.replace(" ", "_"))
        if remote.reverse_label.value:
            valid_values.append(remote.reverse_label.value.replace(" ", "_"))
        return request_value in valid_values

    def get_next_auto_command_requests(self):
        ## Get all command requests and sort them by priority
        command_requests = self.get_auto_command_requests()
        sorted_command_request_keys = sorted(command_requests.keys(), key=lambda x: x.priority.value)
        ## If the number of command requests is greater than the max concurrent remotes, return the first max_concurrent_remotes
        max_concurrent_remotes = self.config.max_concurrent_remotes.value or 1
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
        if not all_pins:
            return

        outputs = [False] * len(all_pins)
        for pin in active_pins:
            outputs[all_pins.index(pin)] = True

        if self._last_pin_write != outputs:
            self._last_pin_write = outputs
            await self.platform_iface.set_do(all_pins, outputs)
