import logging

from pydoover.state import StateMachine

log = logging.getLogger(__name__)

class HydraulicsControllerState:
    state: str

    prep_timeout_secs = 60 * 2  # 2 minutes
    error_timeout_secs = 60 * 60 * 24  # 24 hours

    states = [
        {"name": "off", "display_string": None},
        {"name": "error", "display_string": "Error", "timeout": error_timeout_secs, "on_timeout": "clear_error"},
        {"name": "user_prep", "display_string": None, "timeout": prep_timeout_secs, "on_timeout": "error"},
        {"name": "user_active", "display_string": None},
        {"name": "auto_prep", "display_string": None, "timeout": prep_timeout_secs, "on_timeout": "error"},
        {"name": "auto_active", "display_string": None},
        {"name": "test", "display_string": "Test Mode", "timeout": error_timeout_secs, "on_timeout": "stop"},
    ]

    transitions = [
        {"trigger": "error", "source": "*", "dest": "error"},
        {"trigger": "user_start_prep", "source": ["off", "error"], "dest": "user_prep"},
        {"trigger": "user_ready", "source": ["user_prep"], "dest": "user_active"},
        {"trigger": "auto_start_prep", "source": ["off", "error"], "dest": "auto_prep"},
        {"trigger": "auto_ready", "source": ["auto_prep"], "dest": "auto_active"},
        {"trigger": "stop", "source": ["test","user_start_prep", "user_active","auto_start_prep","auto_active"], "dest": "off"},
        {"trigger": "start_test", "source": ["off", "error"], "dest": "test"},
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

        if self.app.get_test_command():
            await self.start_test()

        if s in ["off", "error"]:
            if self.app.has_user_command():
                await self.user_start_prep()
            if self.app.has_auto_command_requests():
                await self.auto_start_prep()

        if s == "user_prep":
            if not self.app.has_user_command():
                await self.stop()
            if self.app.is_user_active_ready():
                await self.user_ready()
        
        if s == "user_active":
            if not self.app.has_user_command():
                await self.stop()
            if not self.app.is_user_active_ready():
                await self.error()
        
        if s == "auto_prep":
            if not self.app.has_auto_command_requests():
                await self.stop()
            if self.app.is_auto_active_ready():
                await self.auto_ready()
        
        if s == "auto_active":
            if not self.app.has_auto_command_requests():
                await self.stop()
            if not self.app.is_auto_active_ready():
                await self.error()

        if s == "test":
            if not self.app.get_test_command():
                await self.stop()