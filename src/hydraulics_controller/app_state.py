import logging

from pydoover.state import StateMachine

log = logging.getLogger(__name__)

class HydraulicsControllerState:
    state: str

    prep_timeout_secs = 60 * 2  # 2 minutes
    error_timeout_secs = 60 * 60 * 24  # 24 hours

    states = [
        {"name": "off"},
        {"name": "error", "timeout": error_timeout_secs, "on_timeout": "stop"},
        {"name": "user_prep", "timeout": prep_timeout_secs, "on_timeout": "error"},
        {"name": "user_active"},
        {"name": "auto_prep", "timeout": prep_timeout_secs, "on_timeout": "error"},
        {"name": "auto_active", "on_exit": "clear_user_commands"},
        {"name": "test", "timeout": error_timeout_secs, "on_timeout": "stop"},
    ]

    transitions = [
        {"trigger": "error", "source": "*", "dest": "error"},
        {"trigger": "user_start_prep", "source": ["off", "error"], "dest": "user_prep"},
        {"trigger": "user_ready", "source": ["user_prep"], "dest": "user_active"},
        {"trigger": "auto_start_prep", "source": ["off", "error"], "dest": "auto_prep"},
        {"trigger": "auto_ready", "source": ["auto_prep"], "dest": "auto_active"},
        {"trigger": "stop", "source": "*", "dest": "off"},
        {"trigger": "auto_stop", "source": ["auto_prep", "auto_active"], "dest": "off", "after": "clear_user_commands"},
        {"trigger": "start_test", "source": "*", "dest": "test"},
    ]

    def __init__(self, app):
        self.app = app

        self.state_machine = StateMachine(
            states=self.states,
            transitions=self.transitions,
            model=self,
            initial="off",
            queued=True,
        )

    def get_state_display_string(self):
        strings = {
            "off": None,
            "error": "Error",
            "user_prep": None,
            "user_active": None,
            "auto_prep": None,
        }
        return strings.get(self.state, None)


    async def spin_state(self): 
        last_state = None
        ## keep spinning until state has stabilised
        while last_state != self.state:
            last_state = self.state
            await self.evaluate_state()
            # log.info(f"State spin complete for {self.name} - {self.state}")
        return self.state

    async def evaluate_state(self):
        s = self.state

        if s != "test" and self.app.get_test_command():
            await self.start_test()

        elif s in ["off", "error"]:
            if self.app.has_auto_command_requests():
                await self.auto_start_prep()
            elif self.app.has_user_command():
                await self.user_start_prep()

        elif s == "user_prep":
            if not self.app.has_user_command():
                await self.stop()
            elif self.app.is_user_active_ready():
                await self.user_ready()
        
        elif s == "user_active":
            if not self.app.has_user_command():
                await self.stop()
            elif not self.app.is_user_active_ready():
                await self.error()
        
        elif s == "auto_prep":
            if not self.app.has_auto_command_requests():
                await self.auto_stop()
            elif self.app.is_auto_active_ready():
                await self.auto_ready()
        
        elif s == "auto_active":
            if not self.app.has_auto_command_requests():
                await self.auto_stop()
            elif not self.app.is_auto_active_ready():
                await self.error()

        elif s == "test":
            if not self.app.get_test_command():
                await self.stop()

    async def clear_user_commands(self):
        self.app.coerce_ui_commands_off()