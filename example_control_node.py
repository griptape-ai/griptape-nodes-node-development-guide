"""Example node for the Node Development Guide.

This file is intentionally verbose and heavily commented:
- It demonstrates the core concepts (node class + parameters + traits + process()).
- It shows how to shape the UI (display names, multiline text, slider, etc.).
- It includes a simple validation hook so errors surface *before* a flow runs.

Note: This example uses the low-level `Parameter` API directly so you can see
all the moving parts. In real node libraries, consider the `Parameter*` helper
constructs (e.g. `ParameterString`, `ParameterInt`) for common cases.
"""

from __future__ import annotations

from typing import Any

import random

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, ParameterTypeBuiltin
from griptape_nodes.exe_types.node_types import DataNode
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider

class ExampleNode(DataNode):
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        # Always call the base constructor so the engine can initialize internal state.
        # `name` is what users see in the UI (and what appears in logs/errors).
        super().__init__(name, metadata)

        # --------
        # Inputs / Properties / Outputs
        #
        # A Parameter can expose any combination of three modes:
        # - INPUT: accepts a connection from another node
        # - PROPERTY: editable in the node UI
        # - OUTPUT: can connect to another node
        #
        # In a real node you will often:
        # - make INPUT+PROPERTY for config values that can be wired or typed in
        # - make OUTPUT-only for values computed by `process()`
        # --------

        # Free text entry parameter (input + editable property + output passthrough)
        #
        # `type` is the parameter's primary engine type. Builtins are available via
        # `ParameterTypeBuiltin.<TYPE>.value` (e.g. "str", "int", "float").
        self.add_parameter(
            Parameter(
                name="free_text",
                tooltip="Enter any text",
                type=ParameterTypeBuiltin.STR.value,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY, ParameterMode.OUTPUT},
                ui_options={
                    # `display_name` controls the label shown in the UI.
                    "display_name": "Free Text",
                    # `multiline` turns the input into a multi-line text area.
                    "multiline": True,
                },
                # Provide a non-empty default so the node does something useful immediately.
                default_value="hello from the example node",
            )
        )

        # Dropdown parameter
        #
        # Traits attach behaviors to a parameter. `Options(...)` creates a dropdown
        # UI and persists the choices in ui_options for stability.
        self.add_parameter(
            Parameter(
                name="dropdown",
                tooltip="Select an option",
                type=ParameterTypeBuiltin.STR.value,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY, ParameterMode.OUTPUT},
                traits={Options(choices=["yes", "no", "maybe"])},
                ui_options={
                    "display_name": "Dropdown",
                },
                default_value="yes",
            )
        )

        # Integer slider parameter
        #
        # `Slider(min_val, max_val)` adds a slider UI and provides range validation.
        # For numeric parameters, you can also set a `step` in ui_options.
        self.add_parameter(
            Parameter(
                name="integer_slider",
                tooltip="Select a value",
                type=ParameterTypeBuiltin.INT.value,
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY, ParameterMode.OUTPUT},
                traits={Slider(min_val=1, max_val=10)},
                ui_options={
                    "display_name": "Integer Slider",
                    "step": 1,
                },
                default_value=5,
            )
        )

        # Output text parameter
        #
        # OUTPUT-only parameters are generally written in `process()` and are not user-editable.
        self.add_parameter(
            Parameter(
                name="reversed_text",
                tooltip="Reversed words from free text",
                type=ParameterTypeBuiltin.STR.value,
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "display_name": "Reversed Text",
                    "multiline": True,
                },
            )
        )

        # Random float parameter (OUTPUT-only)
        self.add_parameter(
            Parameter(
                name="random_float",
                tooltip="Random float between 0 and integer slider value",
                type=ParameterTypeBuiltin.FLOAT.value,
                allowed_modes={ParameterMode.OUTPUT},
                ui_options={
                    "display_name": "Random Float",
                },
            )
        )

    def process(self) -> None:
        """Run the node.

        The engine calls `process()` when the node executes in a flow.
        Read parameters with `get_parameter_value(...)` and write outputs to
        `self.parameter_output_values`.
        """

        # Read the current parameter values (from UI or from upstream connections).
        free_text = self.get_parameter_value("free_text") or ""
        dropdown = self.get_parameter_value("dropdown")
        integer_slider = self.get_parameter_value("integer_slider") or 0

        # Reverse the words in free_text
        reversed_words = " ".join(reversed(str(free_text).split()))
        self.parameter_output_values["reversed_text"] = reversed_words

        # Pass through the dropdown selection so it can be consumed downstream.
        self.parameter_output_values["dropdown"] = dropdown

        # Calculate random float
        # NOTE: `random.uniform(a, b)` requires numeric inputs. This is a toy example;
        # real nodes should validate and handle None/missing values robustly.
        random_float = round(random.uniform(0, float(integer_slider)), 3)
        self.parameter_output_values["random_float"] = random_float

        # For demonstration, just print the values
        # (Avoid print() in production nodes; use structured logging or a "logs" output parameter.)
        print(
            "Free Text: "
            f"{free_text}, Dropdown: {dropdown}, Integer Slider: {integer_slider}, "
            f"Reversed Words: {self.parameter_output_values['reversed_text']}, "
            f"Random Float: {self.parameter_output_values['random_float']}"
        )

    def validate_before_workflow_run(self) -> list[Exception] | None:
        """Validate node configuration before the flow runs.

        This hook is called by the workflow engine prior to execution so you can
        surface actionable errors early (e.g. missing required inputs).
        """
        errors = []
        free_text_value = self.get_parameter_value("free_text")

        # Check if 'free_text' is empty
        if not free_text_value:
            errors.append(ValueError(f"The '{self.name}' node's 'free_text' parameter is empty."))

        return errors if errors else None