from __future__ import annotations

from ..browser.actions import Action, Navigate, Type
from ..browser.observation import PageObservation
from .task_spec import SimpleSearchTaskSpec, TaskState


class SimpleRuleBasedPolicy:
    """
    Minimal rule-based "agent policy".
    Decides next Action based on current observation and task.
    """

    def decide(
        self,
        obs: PageObservation,
        task: SimpleSearchTaskSpec,
        state: TaskState,
    ) -> Action:
        # If not at the search page yet, navigate there
        if not obs.url.startswith(task.initial_url()):
            return Navigate(task.initial_url())

        # If any input already contains the query, just press Enter on it
        for inp in obs.inputs:
            if inp.value and task.query.lower() in inp.value.lower():
                return Type(selector=inp.selector, text=inp.value, press_enter=True)

        # Otherwise, type into the first available input and press Enter
        if obs.inputs:
            selector = obs.inputs[0].selector
            return Type(selector=selector, text=task.query, press_enter=True)

        # Fallback: refresh the initial URL
        return Navigate(task.initial_url())
