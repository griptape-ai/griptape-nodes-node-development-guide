# Griptape Node Development Guide v3

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Setting Up](#setting-up)
4. [Creating a Node](#creating-a-node)
5. [Parameters](#parameters)
6. [Advanced Parameter Patterns](#advanced-parameter-patterns)
7. [Lifecycle Callbacks](#lifecycle-callbacks)
8. [Best Practices](#best-practices)
9. [Advanced Topics](#advanced-topics)
10. [Modern UI/UX Patterns](#modern-uiux-patterns)
11. [Production Error Handling](#production-error-handling)
12. [Logging Best Practices](#logging-best-practices)
13. [Flexible Artifact Processing](#flexible-artifact-processing)
14. [Creating Node Libraries](#creating-node-libraries)
15. [Custom Widget Components](#custom-widget-components)
16. [Library Structure with uv Dependency Management](#library-structure-with-uv-dependency-management)
17. [Two-Mode UI Pattern (Simple + Custom)](#two-mode-ui-pattern-simple--custom)
18. [Music/Audio Generation API Patterns](#musicaudio-generation-api-patterns)
19. [Documentation Patterns for Node Libraries](#documentation-patterns-for-node-libraries)
20. [Contributing to the Standard Library](#contributing-to-the-standard-library)
21. [Appendix](#appendix)

## Introduction

Griptape Nodes are modular workflow components that enable users to build complex AI workflows through visual programming. This guide covers both fundamental concepts and advanced patterns for creating robust, user-friendly nodes.

Nodes inherit from BaseNode subclasses:

- **DataNode**: For data processing tasks
- **ControlNode**: For flow control with exec_in/out
- **StartNode**: For workflow initialization
- **EndNode**: For workflow termination

## Core Concepts

### Base Classes

- **DataNode**: Processes data without execution flow control
- **ControlNode**: Manages execution flow with exec_in/exec_out connections
- **StartNode**: Entry points for workflows
- **EndNode**: Terminal points for workflows

### Parameters

Define inputs, outputs, and properties via the Parameter class. Parameters support:

- Type validation
- UI customization
- Connection constraints
- Default values
- Traits (Options, Slider, Button, ColorPicker)

### Process Method

The `process()` method contains core logic. Set outputs in `self.parameter_output_values`.

### Node States

- **UNRESOLVED**: Initial state
- **RESOLVING**: Currently processing
- **RESOLVED**: Processing complete

### Connections

Managed via lifecycle callbacks for validation and handling.

### Events

Use `on_griptape_event` for reacting to workflow events.

## Setting Up

1. Install griptape-nodes
2. Use virtual environments for isolation
3. Structure projects with simple folder hierarchies
4. Import from `griptape_nodes.exe_types.*` and `griptape_nodes_library.utils.*`

## Creating a Node

### Basic Node Structure

```python
from typing import Any
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import DataNode

class MyNode(DataNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.category = "Category"
        self.description = "Description"

        self.add_parameter(Parameter(
            name="input",
            input_types=["str"],
            type="str",
            tooltip="Input parameter"
        ))

        self.add_parameter(Parameter(
            name="output",
            output_type="str",
            tooltip="Output parameter"
        ))

    def process(self) -> None:
        val = self.get_parameter_value("input").upper()
        self.parameter_output_values["output"] = val
```

## Parameters

### Parameter Attributes

All Parameter attributes:

- **name**: str, unique identifier, no whitespace
- **tooltip**: str or list[dict] for UI help text
- **default_value**: Any default value
- **type**: str (e.g., "str", "list[str]", ParameterTypeBuiltin.STR.value)
- **input_types**: list[str] for incoming connection types
- **output_type**: str for outgoing connection type
- **allowed_modes**: set[ParameterMode] {INPUT, OUTPUT, PROPERTY}
- **ui_options**: dict for UI customization
- **converters**: list[Callable[[Any], Any]] for value transformation
- **validators**: list[Callable[[Parameter, Any], None]] for validation
- **hide/hide_label/hide_property**: common UI flags (also available via `ui_options`; `ui_options` wins on conflict)
- **allow_input/allow_property/allow_output**: convenience flags for configuring modes (ignored if `allowed_modes` is explicitly set)
- **settable**: bool (default True) - False for computed/output parameters
- **serializable**: bool (default True) - set False for non-serializable values (drivers, file handles, etc.)
- **user_defined**: bool (default False)
- **private**: bool (default False) - hide from general user editing (library/internal use)
- **parent_container_name**: str|None for grouping

### Traits

Add functionality via `add_trait()`:

- **Options**: `Options(choices=list[str] | list[tuple[str, Any]], show_search: bool = True, search_filter: str = "")`
- **Slider**: `Slider(min_val: float, max_val: float)`
- **Button**: `Button(label: str = "", variant=..., size=..., button_link=... | on_click=..., get_button_state=...)`
- **ColorPicker**: `ColorPicker(format="hex")`
- **FileSystemPicker**: `FileSystemPicker(...)` (file/directory selection UI)

### Parameter helper constructs (`ParameterString`, `ParameterInt`, ...)

Griptape Nodes includes a set of convenience Parameter subclasses under `griptape_nodes.exe_types.param_types.*`.
They exist to make common parameter patterns **simple, consistent, and runtime-mutable** (many expose UI options as Python properties).

#### Quick reference table

| Helper            | Enforced `type` / `output_type`               | Default `input_types` behavior                          | Key UI convenience args                                                            | Notes                                                                 |
| ----------------- | --------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `ParameterString` | `"str"` / `"str"`                             | `accept_any=True` → `["any"]` with converter to `str`   | `markdown`, `multiline`, `placeholder_text`, `is_full_width`                       | `type`, `output_type`, and `input_types` constructor args are ignored |
| `ParameterBool`   | `"bool"` / `"bool"`                           | `accept_any=True` → `["any"]` with converter to `bool`  | `on_label`, `off_label`                                                            | Converts common strings like `"true"/"false"`, `"yes"/"no"`           |
| `ParameterInt`    | `"int"` / `"int"`                             | `accept_any=True` → `["any"]` with converter to `int`   | `step`, `slider`, `min_val`, `max_val`, `validate_min_max`                         | Adds constraint traits (Clamp/MinMax/Slider) based on args            |
| `ParameterFloat`  | `"float"` / `"float"`                         | `accept_any=True` → `["any"]` with converter to `float` | `step`, `slider`, `min_val`, `max_val`, `validate_min_max`                         | Adds constraint traits (Clamp/MinMax/Slider) based on args            |
| `ParameterDict`   | `"dict"` / `"dict"`                           | `accept_any=True` → `["any"]` with converter to `dict`  | (none)                                                                             | Uses `griptape_nodes.utils.dict_utils.to_dict()` for conversion       |
| `ParameterJson`   | `"json"` / `"json"`                           | `accept_any=True` → `["any"]` with converter to JSON    | `button`, `button_label`, `button_icon`                                            | Uses `json_repair.repair_json()` for robust string → JSON             |
| `ParameterRange`  | `"list"` / `"list"`                           | `accept_any=True` → `["any"]` with converter to `list`  | `range_slider` + `min_val/max_val/step`, labels                                    | Range slider is only meaningful when the value is a 2-number list     |
| `ParameterImage`  | `"ImageUrlArtifact"` / `"ImageUrlArtifact"`   | `accept_any=True` → `["any"]` (no conversion)           | `clickable_file_browser`, `webcam_capture_image`, `edit_mask`, `pulse_on_run`      | Mostly UI convenience; add converters if you need type coercion       |
| `ParameterAudio`  | `"AudioUrlArtifact"` / `"AudioUrlArtifact"`   | `accept_any=True` → `["any"]` (no conversion)           | `clickable_file_browser`, `microphone_capture_audio`, `edit_audio`, `pulse_on_run` | Mostly UI convenience; add converters if you need type coercion       |
| `ParameterVideo`  | `"VideoUrlArtifact"` / `"VideoUrlArtifact"`   | `accept_any=True` → `["any"]` (no conversion)           | `clickable_file_browser`, `webcam_capture_video`, `edit_video`, `pulse_on_run`     | Mostly UI convenience; add converters if you need type coercion       |
| `Parameter3D`     | `"ThreeDUrlArtifact"` / `"ThreeDUrlArtifact"` | `accept_any=True` → `["any"]` (no conversion)           | `clickable_file_browser`, `expander`, `pulse_on_run`                               | Mostly UI convenience; add converters if you need type coercion       |
| `ParameterButton` | `"button"` / `"str"`                          | `["str", "any"]`                                        | `label`, `variant`, `size`, `icon`, `state`, `href` / `on_click`                   | **Label is display text; `default_value` is stored value**            |

#### Shared behavior across helpers

- All helpers forward the standard `Parameter` constructor knobs (`allowed_modes` or `allow_input/allow_property/allow_output`, `hide/hide_label/hide_property`, `settable`, `serializable`, etc.).
- Many helpers default `accept_any=True`. When enabled, the helper typically sets `input_types=["any"]` and prepends a converter (e.g. `ParameterString` converts any input to `str`). Turn this off if you want strict typing.
- If you provide both an explicit convenience parameter (e.g. `hide=True`) and the same key in `ui_options` (e.g. `ui_options={"hide": False}`), **`ui_options` wins** and Griptape Nodes will warn about the conflict.

#### Detailed helper notes

##### `ParameterString`

- Enforces `type="str"` and `output_type="str"`.
- `accept_any=True` converts `None` → `""` and otherwise uses `str(value)`.
- UI convenience: `markdown`, `multiline`, `placeholder_text`, `is_full_width` (all are runtime-settable properties).

##### `ParameterBool`

- Enforces `type="bool"` and `output_type="bool"`.
- `accept_any=True` converts common string representations (e.g. `"true"`, `"yes"`, `"on"`, `"1"`) to `True` and (`"false"`, `"no"`, `"off"`, `"0"`) to `False`.
- UI convenience: `on_label`, `off_label` (runtime-settable properties).

##### `ParameterInt` / `ParameterFloat` (via `ParameterNumber`)

- Enforces numeric `type` / `output_type` and can prepend a converter when `accept_any=True`.
- `step`: stored in `ui_options["step"]` and validated (value must be a multiple of the current step).
- `slider`, `min_val`, `max_val`, `validate_min_max`: adds one of these constraint traits based on priority:
  - `Slider(min_val, max_val)` if `slider=True`
  - `MinMax(min_val, max_val)` if `validate_min_max=True`
  - `Clamp(min_val, max_val)` if `min_val` and `max_val` are provided

##### `ParameterJson`

- Enforces `type="json"` and `output_type="json"`.
- `accept_any=True` attempts to repair/parse JSON strings using `json_repair.repair_json()` (and will also attempt to stringify non-string inputs).
- UI convenience: optional editor button (`button`, `button_label`, `button_icon`).

##### `ParameterDict`

- Enforces `type="dict"` and `output_type="dict"`.
- `accept_any=True` uses `to_dict(...)` to coerce common inputs into a dict.

##### `ParameterRange`

- Enforces `type="list"` and `output_type="list"`.
- `accept_any=True` coerces `None` → `[]`, list → list, and any other value → `[value]`.
- UI convenience: `range_slider` (a nested `ui_options["range_slider"]` object) with `min_val/max_val/step` and label visibility options.
- The range slider UI is only applicable when the value is a list of exactly two numeric values.

##### `ParameterImage` (Recommended for Image Parameters)

**Always use `ParameterImage` instead of generic `Parameter` for image inputs/outputs.** It provides:

- Automatic `type="ImageUrlArtifact"` and `output_type="ImageUrlArtifact"`
- Built-in UI options for file browser, webcam capture, and mask editing
- Consistent behavior across all image-handling nodes

**Basic Usage:**

```python
from griptape_nodes.exe_types.param_types.parameter_image import ParameterImage

# Input image parameter
self.add_parameter(
    ParameterImage(
        name="input_image",
        tooltip="Input image for processing",
        allow_output=False,  # Input only
    )
)

# Output image parameter
self.add_parameter(
    ParameterImage(
        name="output_image",
        tooltip="Generated image result",
        allow_input=False,   # Output only
        allow_property=False,
    )
)
```

**Available UI Options:**

- `clickable_file_browser`: Enable file browser for image selection
- `webcam_capture_image`: Enable webcam capture
- `edit_mask`: Enable mask editing overlay
- `pulse_on_run`: Visual feedback when image updates

**Dynamic Visibility Pattern:**

For parameters that should only appear for certain model types:

```python
def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)

    # Add image parameter (hidden by default)
    self.add_parameter(
        ParameterImage(
            name="input_image",
            tooltip="Input image for image-to-image generation",
            allow_output=False,
        )
    )

    # Initialize visibility based on default model
    self._initialize_parameter_visibility()

def _initialize_parameter_visibility(self) -> None:
    """Initialize parameter visibility based on default model."""
    model = self.get_parameter_value("model") or "default"
    if model in ["model-with-image-support", "another-model"]:
        self.show_parameter_by_name("input_image")
    else:
        self.hide_parameter_by_name("input_image")

def after_value_set(self, parameter: Parameter, value: Any) -> None:
    """Update visibility when model changes."""
    if parameter.name == "model":
        if value in ["model-with-image-support", "another-model"]:
            self.show_parameter_by_name("input_image")
        else:
            self.hide_parameter_by_name("input_image")
            self.set_parameter_value("input_image", None)  # Clear when hiding

    return super().after_value_set(parameter, value)
```

**Why Use `ParameterImage` Over Generic `Parameter`:**

| Aspect      | Generic `Parameter`               | `ParameterImage`                            |
| ----------- | --------------------------------- | ------------------------------------------- |
| Type safety | Manual `type`/`input_types` setup | Automatic artifact types                    |
| UI features | Manual `ui_options` configuration | Built-in file browser, webcam, mask editing |
| Consistency | Varies by implementation          | Standardized across nodes                   |
| Maintenance | More boilerplate code             | Less code, cleaner                          |

**Legacy Pattern (Avoid):**

```python
# ❌ Don't do this - use ParameterImage instead
self.add_parameter(
    Parameter(
        name="input_image",
        input_types=["ImageArtifact", "ImageUrlArtifact", "str"],
        type="ImageArtifact",
        default_value=None,
        tooltip="Input image",
        allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
        ui_options={"display_name": "Input Image"},
    )
)
```

**Recommended Pattern:**

```python
# ✅ Use ParameterImage for cleaner, more maintainable code
self.add_parameter(
    ParameterImage(
        name="input_image",
        tooltip="Input image",
        allow_output=False,
    )
)
```

##### `ParameterAudio` / `ParameterVideo` / `Parameter3D`

- Enforce their corresponding `*UrlArtifact` `type` / `output_type` (e.g., `AudioUrlArtifact`, `VideoUrlArtifact`, `ThreeDUrlArtifact`).
- These helpers primarily provide UI options (file browser / capture / editing / expanders). If you need coercion from e.g. `str` → artifact, supply `converters` and/or handle it in your node's `before_value_set()` / `process()` logic.
- Follow the same patterns as `ParameterImage` for these media types.

##### `ParameterButton`

Buttons provide interactive UI elements that trigger actions when clicked, such as updating parameters, performing calculations, or navigating between states.

**Basic Properties:**

- Enforces `type="button"` and `output_type="str"`
- By default, it's a **property-only** UI element (`allow_property=True`, `allow_input=False`, `allow_output=False`)
- Accepts either `href="..."` (simple link) or `on_click=...` (custom callback) parameters
- `label` is the display text shown on the button
- `icon` adds a visual icon (optional)
- `icon_position` controls icon placement ("left" or "right", defaults to "left")

**Important:** The `on_click` handler and `href` are passed **directly to `ParameterButton`** as parameters, not via the `Button` trait.

**Implementation Pattern:**

Buttons must be wrapped in a `ParameterButtonGroup` container:

```python
from griptape_nodes.exe_types.core_types import ParameterButtonGroup
from griptape_nodes.exe_types.param_types.parameter_button import ParameterButton
from griptape_nodes.traits.button import Button, ButtonDetailsMessagePayload

class MyNode(DataNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Create button group with context manager
        with ParameterButtonGroup(name="my_button_group") as button_group:
            ParameterButton(
                name="update_button",
                label="Update Date/Time",
                icon="calendar",
                on_click=self._handle_button_click,  # Pass on_click directly
            )
        self.add_node_element(button_group)

        # Add parameter that will be updated by button
        self.add_parameter(
            Parameter(
                name="display_value",
                tooltip="Value updated by button",
                type=ParameterTypeBuiltin.STR.value,
                allowed_modes={ParameterMode.PROPERTY},
                ui_options={
                    "display_name": "Display Value",
                    "readonly": True,  # Prevent manual editing
                },
                default_value="Click button to update",
            )
        )

    def _handle_button_click(
        self,
        button: Button,
        button_payload: ButtonDetailsMessagePayload,
    ) -> None:
        """Button click handler.

        Args:
            button: The Button trait instance
            button_payload: Contains click event details
        """
        # Update parameter value
        new_value = "Updated at " + datetime.now().strftime("%H:%M:%S")
        self.set_parameter_value("display_value", new_value)
```

**Multiple Buttons in a Group:**

```python
with ParameterButtonGroup(name="navigation_buttons") as nav_buttons:
    ParameterButton(
        name="previous",
        label="Previous",
        icon="arrow-left",
        on_click=self._previous_item,  # Pass on_click directly
    )
    ParameterButton(
        name="next",
        label="Next",
        icon="arrow-right",
        icon_position="right",
        on_click=self._next_item,  # Pass on_click directly
    )
self.add_node_element(nav_buttons)
```

**Common Use Cases:**

1. **Update Display Values**

   ```python
   def _update_datetime(self, button: Button, button_payload: ButtonDetailsMessagePayload) -> None:
       """Update datetime display when button is clicked."""
       current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       self.set_parameter_value("datetime_display", current_time)
   ```

2. **Navigate Through Items**

   ```python
   def _next_image(self, button: Button, button_payload: ButtonDetailsMessagePayload) -> None:
       """Increment index and update display."""
       current_index = self.get_parameter_value("image_index")
       self.set_parameter_value("image_index", current_index + 1)
       self._update_display()
   ```

3. **Trigger Calculations**

   ```python
   def _calculate(self, button: Button, button_payload: ButtonDetailsMessagePayload) -> None:
       """Perform calculation and update result parameter."""
       input_value = self.get_parameter_value("input")
       result = self._perform_complex_calculation(input_value)
       self.set_parameter_value("result", result)
   ```

4. **Reset to Defaults**
   ```python
   def _reset(self, button: Button, button_payload: ButtonDetailsMessagePayload) -> None:
       """Reset parameters to default values."""
       self.set_parameter_value("counter", 0)
       self.set_parameter_value("display", "")
   ```

**Link Buttons (Alternative to `on_click`):**

For simple navigation to external URLs:

```python
ParameterButton(
    name="docs_link",
    label="View Documentation",
    icon="external-link",
    href="https://docs.griptape.ai",  # Pass href directly
)
```

**Best Practices:**

- Use descriptive button labels that clearly indicate the action
- Choose appropriate icons that match the action (e.g., "calendar" for date/time, "arrow-left"/"arrow-right" for navigation)
- Keep button handlers simple and focused on a single action
- Use read-only parameters for values that should only be updated by buttons
- Avoid triggering expensive operations directly in button handlers (consider using flags that `process()` checks instead)
- Group related buttons together in a single `ParameterButtonGroup`

**Common Patterns:**

| Pattern        | Button Action                      | Updated Parameter Type      | Use Case                         |
| -------------- | ---------------------------------- | --------------------------- | -------------------------------- |
| Update Display | Updates a read-only text parameter | `PROPERTY` (readonly)       | Show current time, status, count |
| Navigation     | Increments/decrements an index     | Hidden `PROPERTY` parameter | Image carousel, list browsing    |
| Toggle State   | Switches between states            | `PROPERTY` parameter        | Enable/disable features          |
| Trigger Action | Sets a flag checked by `process()` | Hidden `PROPERTY` parameter | Refresh data, recalculate        |

**Complete Example:**

See `example_control_node.py` and `image_carousel.py` for working implementations that demonstrate:

- Button creation with icons
- Button group usage
- Updating read-only parameters
- Handler method signatures
- Navigation patterns
- Locale-appropriate datetime formatting

### Containers

- **ParameterList**: A container parameter that owns multiple child `Parameter` items (use `get_parameter_list_value()` to flatten values)
- **ParameterDictionary**: A container parameter that owns ordered key/value pairs (distinct from `ParameterDict`, which is a `dict`-typed value parameter helper)
- **ParameterGroup**: For UI grouping

**Container semantics (important):**

- Container parameters are represented as `ParameterContainer` objects in the engine. They are **always truthy**, even when empty (they override `__bool__()` to avoid bugs with stale cached values).
- `ParameterList` supports several UI convenience options (e.g. `collapsed`, grid display, and column count) that are merged into `ui_options` at runtime.
- `ParameterDictionary` is an ordered collection of key/value pair children (internally represented as a list to preserve order).

### ParameterList Pattern

For parameters accepting multiple inputs of the same type:

```python
self.add_parameter(
    ParameterList(
        name="tools",
        input_types=["Tool", "list[Tool]"],
        default_value=[],
        tooltip="Connect individual tools or a list of tools",
        allowed_modes={ParameterMode.INPUT},
    )
)

# Retrieve in process method
tools = self.get_parameter_list_value("tools")  # Always returns a list
for tool in tools:
    # Process each tool
```

**Benefits:**

- Multiple connection points in UI
- Automatic aggregation of inputs
- Flexible workflow design
- Follows Griptape design patterns

**Important behavior note:** `get_parameter_list_value()` flattens nested iterables and **drops falsey items**
(e.g. `0`, `False`, `""`, empty dicts/lists). If you need to preserve falsey values, use `get_parameter_value()` and handle flattening yourself.

### Common Parameter Patterns

#### Search Input with Placeholder

```python
Parameter(
    name="search_query",
    input_types=["str"],
    type="str",
    tooltip="Search term to find models",
    allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
    ui_options={"placeholder_text": "e.g., llama, bert, stable-diffusion"}
)
```

#### Full-Width List Output

```python
Parameter(
    name="results",
    output_type="list[dict]",
    type="list[dict]",
    tooltip="Search results with full information",
    allowed_modes={ParameterMode.OUTPUT},
    ui_options={"is_full_width": True}
)
```

#### Multiline Text Input

```python
Parameter(
    name="prompt",
    input_types=["str"],
    type="str",
    tooltip="Description of desired output",
    allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
    ui_options={"multiline": True, "placeholder_text": "Describe what you want..."}
)
```

#### File Upload with Browser

```python
Parameter(
    name="image",
    input_types=["ImageArtifact", "ImageUrlArtifact", "str"],
    type="ImageArtifact",
    tooltip="Input image file",
    allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
    ui_options={"clickable_file_browser": True}
)
```

## Advanced Parameter Patterns

### Dynamic Parameter Visibility

Use `after_value_set()` callback to create context-aware UIs:

```python
def after_value_set(self, parameter: Parameter, value: Any) -> None:
    """Update parameter visibility based on model selection."""
    if parameter.name == "model":
        if value == "text-to-image":
            self.hide_parameter_by_name("input_image")
            self.show_parameter_by_name("prompt")
        elif value == "image-to-image":
            self.show_parameter_by_name("input_image")
            self.show_parameter_by_name("prompt")

    return super().after_value_set(parameter, value)
```

### Dynamic Options Updates

Update parameter choices at runtime:

```python
from griptape_nodes.traits.options import Options

def _update_option_choices(self, param_name: str, choices: list, default_value: str):
    """Update Options trait choices dynamically."""
    param = self.get_parameter_by_name(param_name)
    if not param:
        return

    # Traits are stored as child elements on the Parameter
    # (most commonly, you'll be updating an Options trait)
    for trait in param.find_elements_by_type(Options):
        trait.choices = choices
        break
    self.set_parameter_value(param_name, default_value)
```

### Advanced ParameterList Usage

Include both individual and list types for maximum flexibility:

```python
self.add_parameter(
    ParameterList(
        name="images",
        input_types=[
            "ImageArtifact",
            "ImageUrlArtifact",
            "str",
            "list",
            "list[ImageArtifact]",
            "list[ImageUrlArtifact]",
        ],
        default_value=[],
        tooltip="Input images (up to 10 images total)",
        allowed_modes={ParameterMode.INPUT},
        ui_options={"expander": True, "display_name": "Input Images"},
    )
)
```

### Controlling Parameter Order in the UI

Parameters appear in the UI in the order they are added via `add_parameter()`. This matters for user experience - related parameters should be grouped logically.

**Problem**: Base classes like `BaseImageProcessor` automatically add parameters (e.g., `input_image`) in their `__init__`, which may not be the order you want.

**Solution**: Extend `SuccessFailureNode` directly instead of `BaseImageProcessor` to gain full control over parameter ordering:

```python
from griptape_nodes.exe_types.node_types import SuccessFailureNode
from griptape_nodes.exe_types.param_types.parameter_image import ParameterImage

class ColorMatch(SuccessFailureNode):
    """Transfer colors from a reference image to a target image."""

    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)

        # Reference image FIRST - the source of the color palette
        self.add_parameter(
            ParameterImage(
                name="reference_image",
                tooltip="Reference image - the source of the color palette to transfer",
                ui_options={"clickable_file_browser": True, "expander": True},
            )
        )

        # Target image SECOND - the image to modify
        self.add_parameter(
            ParameterImage(
                name="target_image",
                tooltip="Target image - the image to apply the color transfer to",
                ui_options={"clickable_file_browser": True, "expander": True},
            )
        )

        # Additional parameters in desired order...
```

**When to Use This Pattern**:

- Two-image nodes where the semantic order matters (reference → target)
- Nodes requiring specific parameter groupings not provided by base classes
- When base class parameter order conflicts with your UX goals

**Trade-off**: You lose helper methods from specialized base classes, but gain complete control over the node's UI structure.

### Two-Image Processing Node Pattern

For nodes that process two images together (blending, color matching, compositing), use this pattern:

```python
from typing import Any, ClassVar
from PIL import Image

from griptape.artifacts import ImageUrlArtifact
from griptape_nodes.exe_types.core_types import Parameter
from griptape_nodes.exe_types.node_types import SuccessFailureNode
from griptape_nodes.exe_types.param_types.parameter_image import ParameterImage
from griptape_nodes_library.utils.image_utils import (
    dict_to_image_url_artifact,
    load_pil_from_url,
    save_pil_image_with_named_filename,
)
from griptape_nodes_library.utils.file_utils import generate_filename


class TwoImageProcessor(SuccessFailureNode):
    """Base pattern for nodes processing two images."""

    CATEGORY: ClassVar[str] = "image"

    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)

        # First image input
        self.add_parameter(
            ParameterImage(
                name="image_a",
                tooltip="First input image",
                ui_options={"clickable_file_browser": True, "expander": True},
            )
        )

        # Second image input
        self.add_parameter(
            ParameterImage(
                name="image_b",
                tooltip="Second input image",
                ui_options={"clickable_file_browser": True, "expander": True},
            )
        )

        # Output image
        self.add_parameter(
            ParameterImage(
                name="output_image",
                tooltip="Processed result",
                allowed_modes={ParameterMode.OUTPUT},
            )
        )

    def _get_image_artifact(self, param_name: str) -> ImageUrlArtifact | None:
        """Convert parameter value to ImageUrlArtifact."""
        value = self.get_parameter_value(param_name)
        if value is None:
            return None
        if isinstance(value, dict):
            return dict_to_image_url_artifact(value)
        return value

    def _process_images(self) -> None:
        """Process both images and set output."""
        image_a_artifact = self._get_image_artifact("image_a")
        image_b_artifact = self._get_image_artifact("image_b")

        if not image_a_artifact or not image_b_artifact:
            return

        # Load as PIL images
        pil_a = load_pil_from_url(image_a_artifact.value)
        pil_b = load_pil_from_url(image_b_artifact.value)

        # Process images (override in subclass)
        result_pil = self._do_processing(pil_a, pil_b)

        # Save result
        filename = generate_filename(self.name, suffix="processed")
        output_artifact = save_pil_image_with_named_filename(result_pil, filename)
        self.parameter_output_values["output_image"] = output_artifact

    def _do_processing(self, image_a: Image.Image, image_b: Image.Image) -> Image.Image:
        """Override this method with actual processing logic."""
        raise NotImplementedError

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Trigger live preview when both images are available."""
        if parameter.name in ("image_a", "image_b"):
            image_a = self.get_parameter_value("image_a")
            image_b = self.get_parameter_value("image_b")
            if image_a and image_b:
                self._process_images()

        return super().after_value_set(parameter, value)

    def process(self) -> None:
        """Main processing entry point."""
        self._process_images()
```

**Key Utilities Used**:

- `dict_to_image_url_artifact()`: Converts dict representation to artifact
- `load_pil_from_url()`: Loads PIL Image from URL (including localhost)
- `save_pil_image_with_named_filename()`: Saves PIL Image and returns artifact
- `generate_filename()`: Creates consistent filenames with node name

## Lifecycle Callbacks

All callbacks are overridable:

- **allow_incoming_connection**, **allow_outgoing_connection**: Return bool for connection validation
- **after_incoming_connection**, **after_outgoing_connection**: Handle post-connection logic
- **after_incoming_connection_removed**, **after_outgoing_connection_removed**: Handle disconnection
- **before_value_set**: Return modified value before setting
- **after_value_set**: React to parameter value changes
- **validate_before_workflow_run**, **validate_before_node_run**: Return list[Exception]|None
- **on_griptape_event**: Handle workflow events
- **initialize_spotlight**: Setup spotlight functionality
- **get_next_control_output**: Return Parameter|None for control flow

### Helper Methods

- `hide_parameter_by_name()`, `show_parameter_by_name()`
- `append_value_to_parameter()`
- `publish_update_to_parameter()`

## Best Practices

### Core Principles

- **Descriptive names and tooltips**
- **Robust error handling with validators**
- **Single responsibility per node**
- **Use `SecretsManager` for API keys and secrets**
- **Import all dependencies at module level**
- **Idempotent process methods**

### Secrets Management

Use `GriptapeNodes.SecretsManager()` to access API keys and secrets:

```python
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

class MyNode(DataNode):
    SERVICE_NAME = "MyService"
    API_KEY_NAME = "MY_SERVICE_API_KEY"

    def _validate_api_key(self) -> str:
        api_key = GriptapeNodes.SecretsManager().get_secret(self.API_KEY_NAME)
        if not api_key:
            raise ValueError(f"Missing {self.API_KEY_NAME}")
        return api_key
```

**Key Points:**

- Import `GriptapeNodes` at module level, not inside functions
- Use `SecretsManager().get_secret()` to retrieve secrets
- Define `API_KEY_NAME` as a class constant for consistency
- Always validate that the secret exists before using it

### Import Best Practices

**Always import dependencies at module level, not inside functions:**

❌ **Bad** - Conditional/lazy imports:

```python
def _get_image_data(self, image_artifact):
    try:
        from PIL import Image  # Don't do this
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
```

✅ **Good** - Module-level imports:

```python
# At top of file
from PIL import Image
from io import BytesIO

def _get_image_data(self, image_artifact):
    img = Image.open(BytesIO(image_bytes))
```

**Why?**

- Makes dependencies clear and visible
- Avoids redundant imports throughout the file
- Follows Python best practices (PEP 8)
- Easier to catch missing dependencies early
- Better IDE support and code completion

**Exception**: Only use conditional imports for truly optional dependencies that may not be installed:

```python
def process(self) -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        error_msg = "huggingface_hub library not installed"
        self.parameter_output_values["output"] = None
        raise ImportError(error_msg)
```

### Import Organization

Organize imports in standard order with blank lines between groups:

```python
# Standard library imports
import base64
import logging
from typing import Any

# Third-party imports
import requests
from PIL import Image

# Local/Griptape imports
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import DataNode
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
```

### Type Checking for Third-Party Libraries

When importing third-party libraries, you may encounter type checking errors. Use the appropriate `type: ignore` comment based on the situation:

#### Scenario 1: Library Installed but Missing Type Stubs

For libraries that are installed but lack type annotations (like `sklearn`, `ultralytics`, `supervision`):

```python
# ✅ Library exists but has no type stubs
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from ultralytics import YOLO  # type: ignore[import-untyped]
from supervision import Detections  # type: ignore[import-untyped]
```

#### Scenario 2: Library Not Installed in CI Type Checking Environment

For libraries that are runtime dependencies but not installed in the CI type checking environment (like `color-matcher`, specialized processing libraries):

```python
# ✅ Library not installed in type checking environment
from color_matcher import ColorMatcher  # type: ignore[reportMissingImports]
from color_matcher.normalizations import norm_img_to_uint8  # type: ignore[reportMissingImports]
```

#### When to Use Which

| Error Type             | Comment                                | Use When                         |
| ---------------------- | -------------------------------------- | -------------------------------- |
| `import-untyped`       | `# type: ignore[import-untyped]`       | Library installed, no type stubs |
| `reportMissingImports` | `# type: ignore[reportMissingImports]` | Library not in CI environment    |

**General guidance:**

- `import-untyped` is preferred when both work - it's more precise
- `reportMissingImports` is necessary when the library isn't available during type checking
- Check CI logs to determine which error you're actually getting

### Function Parameter Management

Keep function argument counts low (under 6) by using dataclasses:

❌ **Bad** - Too many parameters:

```python
def process_bbox(self, x: int, y: int, width: int, height: int,
                 dilation_percent: float, img_width: int, img_height: int):
    # Process bounding box
```

✅ **Good** - Use dataclass:

```python
from dataclasses import dataclass

@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    dilation_percent: float
    img_width: int
    img_height: int

def process_bbox(self, bbox: BoundingBox):
    # Process bounding box using bbox.x, bbox.y, etc.
```

**Benefits:**

- Improved readability
- Type safety
- Easier to maintain
- Self-documenting code

### Code Quality

**Additional linting best practices:**

- Remove trailing whitespace from all lines (including blank lines)
- Use consistent indentation (spaces only, no tabs)
- Keep lines under 120 characters when possible
- Use descriptive variable names
- Avoid adding unnecessary Python packaging scaffolding. Create `__init__.py` files only when you actually want a package (or need them for your chosen packaging approach).

#### Pre-commit checks (required)

Before committing in `griptape-nodes`, run formatting and checks and fix any errors:

```bash
make format
make check/lint
make check/types
```

#### Node docs + navigation

When adding a new node to the core library, also add node reference documentation:

- Create a docs page at: `docs/nodes/<category>/<node>.md`
- Add it to `mkdocs.yml` under: `nav -> Nodes Reference -> <Category>`

#### Common gotchas

- Repo-wide lint/type checks can surface issues in **untracked** files too. Avoid leaving untracked folders/files in the repo (for example, copied scratch folders) when running checks or preparing a PR.
- If ruff flags function complexity (e.g., `C901`, `PLR0912`), prefer refactoring into smaller helpers over suppressing.

## Advanced Topics

### REST API vs SDK Integration

**Problem**: Python SDKs often lag behind REST APIs in supporting new features. Parameters available in REST API documentation may not be exposed in SDK libraries.

**When to Use REST API Directly**:

- SDK missing documented API features (e.g., `image_config` for Gemini)
- Need immediate access to new API parameters
- SDK has bugs or limitations
- Want lighter dependencies

**REST API Implementation Pattern**:

```python
import base64
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Authentication
credentials = service_account.Credentials.from_service_account_file(
    service_account_file,
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

def _get_access_token(self, credentials) -> str:
    """Get access token from credentials."""
    if not credentials.valid:
        credentials.refresh(Request())
    return credentials.token

# Build JSON payload matching REST API spec
payload = {
    "contents": {
        "role": "USER",
        "parts": [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode('utf-8')
                }
            }
        ]
    },
    "generation_config": {
        "temperature": 1.0,
        "topP": 0.95,
        "candidateCount": 1,
        "response_modalities": ["TEXT", "IMAGE"],
        "image_config": {  # Feature not in SDK!
            "aspect_ratio": "16:9"
        }
    }
}

# Make authenticated request
access_token = self._get_access_token(credentials)
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

api_endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:generateContent"

response = requests.post(api_endpoint, headers=headers, json=payload, timeout=120)
response.raise_for_status()
response_data = response.json()

# Parse JSON response (handle both camelCase and snake_case)
candidates = response_data.get("candidates", [])
for cand in candidates:
    parts_list = cand.get("content", {}).get("parts", [])
    for part in parts_list:
        if "inlineData" in part or "inline_data" in part:
            inline_data = part.get("inlineData") or part.get("inline_data", {})
            mime = inline_data.get("mimeType") or inline_data.get("mime_type")
            data_b64 = inline_data.get("data", "")
            data_bytes = base64.b64decode(data_b64)
```

**Key Considerations**:

1. **Dependencies**: Use `google-auth` instead of full SDK (`google-cloud-aiplatform`, `google-genai`)
2. **Regional Availability**: Some models only work in specific regions (e.g., `us-central1`), not `global`
3. **Model Names**: Check for `-preview` suffix differences between preview and stable models
4. **Authentication Scopes**: Use `https://www.googleapis.com/auth/cloud-platform` for Vertex AI
5. **Response Format**: Handle both camelCase (API) and snake_case (some SDKs) field names
6. **Base64 Encoding**: REST API expects base64-encoded strings for binary data
7. **Error Handling**: Parse JSON error responses for detailed error messages

**Trade-offs**:

- ✅ Immediate access to all API features
- ✅ Lighter dependencies
- ✅ Full control over requests
- ❌ More implementation work
- ❌ Must handle auth/tokens manually
- ❌ Need to track API changes yourself

### Complex Type Management Systems

For nodes that need sophisticated type negotiation between multiple parameters:

```python
class IfElse(BaseNode):
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)

        # Sophisticated connection tracking for type management
        self._possibility_space: list[str] = []  # Types acceptable to output target
        self._locked_type: str | None = None     # Specific type locked by input
        self._connected_inputs: set[str] = set() # Track input connections
        self._output_connected: bool = False     # Track output connections

    def _update_parameter_types(self) -> None:
        """Update all parameter types based on current state."""
        if self._locked_type:
            # Locked to specific type - everything uses that type
            self.output_if_true.input_types = [self._locked_type]
            self.output_if_false.input_types = [self._locked_type]
            self.output.output_type = self._locked_type
        elif self._possibility_space:
            # Flexible within possibility space
            self.output_if_true.input_types = self._possibility_space.copy()
            self.output_if_false.input_types = self._possibility_space.copy()
            self.output.output_type = ParameterTypeBuiltin.ALL.value
        else:
            # Default state - accept any type
            self.output_if_true.input_types = ["any"]
            self.output_if_false.input_types = ["any"]
            self.output.output_type = ParameterTypeBuiltin.ALL.value
```

**Best Practice**: Use sophisticated type management for nodes that route data between multiple inputs and outputs.

### Agentic Nodes

Inherit from ControlNode for agent management:

```python
from griptape.structures import Agent
from griptape_nodes.exe_types.node_types import ControlNode

class MyAgentNode(ControlNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_parameter(Parameter(
            name="agent_in",
            input_types=["Agent"],
            type="Agent"
        ))
        self.add_parameter(Parameter(
            name="agent_out",
            output_type="Agent"
        ))

    def process(self) -> None:
        agent_state = self.get_parameter_value("agent_in")
        agent = Agent.from_dict(agent_state) if agent_state else Agent()
        # Process with agent
        self.parameter_output_values["agent_out"] = agent.to_dict()
```

### Abstract Base Classes for Node Families

Create abstract base classes for related nodes to share common functionality:

```python
from abc import abstractmethod
from typing import Any

from griptape_nodes.exe_types.base_iterative_nodes import BaseIterativeStartNode

class BaseCustomIterativeStartNode(BaseIterativeStartNode):
    """Base class for a family of custom iterative start nodes."""

    @abstractmethod
    def _get_compatible_end_classes(self) -> set[type]:
        """Return the set of End node classes that this Start node can connect to."""

    @abstractmethod
    def _get_parameter_group_name(self) -> str:
        """Return the name for the parameter group containing iteration data."""

    @abstractmethod
    def _get_exec_out_display_name(self) -> str:
        """Return the display name for the exec_out parameter."""

    @abstractmethod
    def _get_exec_out_tooltip(self) -> str:
        """Return the tooltip for the exec_out parameter."""

    @abstractmethod
    def _get_iteration_items(self) -> list[Any]:
        """Get the list of items to iterate over."""

    @abstractmethod
    def is_loop_finished(self) -> bool:
        """Return True if the loop has completed all iterations."""
```

**Best Practice**: Use abstract base classes to share common logic across node families while enforcing implementation of specific methods.

### Caching

Use ClassVar for shared resources:

```python
from typing import ClassVar, Any

class CachedModelNode(DataNode):
    _cache: ClassVar[dict[str, Any]] = {}

    def get_model(self, model_id: str) -> Any:
        if model_id not in self._cache:
            self._cache[model_id] = load_model(model_id)
        return self._cache[model_id]
```

### Hub Integration (e.g., HuggingFace)

```python
# Gated model detection
is_gated = getattr(model, 'gated', False)
model_dict['gated'] = is_gated

# Status updates for gated models
if getattr(model_info, 'gated', False):
    self.publish_update_to_parameter(
        "status",
        "🔒 GATED MODEL - May require approval"
    )
```

### ParameterMessage for External Links and Status Updates

```python
from griptape_nodes.exe_types.core_types import ParameterMessage

# External link example
ParameterMessage(
    name="model_card_link",
    title="Model Card",
    variant="info",
    value="View model documentation",
    button_link=f"https://huggingface.co/{model_id}",
    button_text="View on HuggingFace"
)

# Dynamic status message example
class MyIterativeNode(BaseIterativeStartNode):
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)

        # Status message parameter for real-time updates
        self.status_message = ParameterMessage(
            name="status_message",
            variant="info",
            value="",
        )
        self.add_node_element(self.status_message)

    def _update_status_message(self, status_type: str = "normal") -> None:
        """Update status message based on current state."""
        if self._total_iterations == 0:
            status = "Completed 0 (of 0)"
        elif status_type == "break":
            status = f"Stopped at {self._current_iteration_count} (of {self._total_iterations}) - Break"
        elif self.is_loop_finished():
            status = f"Completed {self._total_iterations} (of {self._total_iterations})"
        else:
            status = f"Processing {self._current_iteration_count} (of {self._total_iterations})"

        self.status_message.value = status
```

**Best Practice**: Use ParameterMessage for both static external links and dynamic status updates.

## Modern UI/UX Patterns

### Advanced UI Options

```python
ui_options={
    "hide_property": True,      # Hide from property panel
    "pulse_on_run": True,       # Visual feedback during execution
    "expander": True,           # Collapsible parameter groups
    "is_full_width": True,      # Full-width display
    "multiline": True,          # Multi-line text input
    "placeholder_text": "...",  # Input placeholder
    "display_name": "...",      # Custom display name
    "markdown": True,           # Markdown rendering
    "compare": True,            # Comparison mode
    "clickable_file_browser": True,  # File browser integration
    "hide": True,               # ⭐ CORRECT: Completely hide parameter
    "collapsed": True,          # Start parameter groups collapsed
    "edit_mask": True,          # Enable mask editing for images
}
```

#### Hidden Parameters Best Practice

Use `"hide": True` to hide parameters from the UI (for advanced/expert settings):

```python
# ✅ CORRECT: Hidden parameter with slider
num_images_param = Parameter(
    name="num_images",
    input_types=["int"],
    type="int",
    default_value=1,
    tooltip="Number of images to generate (1-9)",
    allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
    ui_options={
        "display_name": "Number of Images",
        "hide": True  # ⭐ CORRECT pattern
    },
)
num_images_param.add_trait(Slider(min_val=1, max_val=9))
self.add_parameter(num_images_param)

# ⚠️ LEGACY: "hidden": True exists but is rare (3 instances vs 47)
ui_options={"hidden": True}  # Less common, prefer "hide": True
```

**Common Use Cases for Hidden Parameters:**

- Advanced/expert configuration options
- Internal control signals
- Debug parameters
- Optional advanced features
- Parameters that should only be set programmatically

### Success/Failure Node Pattern

For nodes that can succeed or fail, inherit from SuccessFailureNode:

```python
from griptape_nodes.exe_types.node_types import SuccessFailureNode

class LoadImage(SuccessFailureNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Add status parameters using the helper method
        self._create_status_parameters(
            result_details_tooltip="Details about the image loading operation result",
            result_details_placeholder="Details on the load attempt will be presented here.",
        )

    def process(self) -> None:
        # Reset execution state at start
        self._clear_execution_status()

        # Clear output values to prevent stale data on errors
        self.parameter_output_values["image"] = None

        try:
            # Processing logic here
            result = load_image()
            self.parameter_output_values["image"] = result

            # Success case
            success_details = f"Image loaded successfully from {source}"
            self._set_status_results(was_successful=True, result_details=f"SUCCESS: {success_details}")

        except Exception as e:
            error_details = f"Failed to load image: {e}"
            self._set_status_results(was_successful=False, result_details=f"FAILURE: {error_details}")
            self._handle_failure_exception(e)
```

**Best Practice**: Use SuccessFailureNode for operations that can fail and need to report status to users.

### Parameter Initialization

Initialize parameter visibility on node creation:

```python
def _initialize_parameter_visibility(self) -> None:
    """Initialize parameter visibility based on default values."""
    default_model = self.get_parameter_value("model") or "default"
    if default_model == "text-only":
        self.hide_parameter_by_name("image_input")
    else:
        self.show_parameter_by_name("image_input")
```

### Artifact Path Tethering Pattern

For nodes that work with files, use the artifact tethering pattern to keep path and artifact parameters synchronized:

```python
from griptape_nodes_library.utils.artifact_path_tethering import (
    ArtifactPathTethering,
    ArtifactTetheringConfig,
)

class LoadImage(SuccessFailureNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Configuration for artifact tethering
        self._tethering_config = ArtifactTetheringConfig(
            dict_to_artifact_func=dict_to_image_url_artifact,
            extract_url_func=self._extract_url_from_image_value,
            supported_extensions=self.SUPPORTED_EXTENSIONS,
            default_extension="png",
            url_content_type_prefix="image/",
        )

        # Create artifact parameter
        self.image_parameter = Parameter(
            name="image",
            input_types=["ImageUrlArtifact", "ImageArtifact", "str"],
            type="ImageUrlArtifact",
            output_type="ImageUrlArtifact",
            ui_options={"clickable_file_browser": True},
        )

        # Create path parameter using tethering utility
        self.path_parameter = ArtifactPathTethering.create_path_parameter(
            name="path",
            config=self._tethering_config,
            display_name="File Path or URL",
        )

        # Tethering helper keeps parameters in sync
        self._tethering = ArtifactPathTethering(
            node=self,
            artifact_parameter=self.image_parameter,
            path_parameter=self.path_parameter,
            config=self._tethering_config,
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        # Delegate tethering logic to helper
        self._tethering.on_after_value_set(parameter, value)
        return super().after_value_set(parameter, value)
```

**Best Practice**: Use artifact tethering for seamless file/URL parameter synchronization.

## Production Error Handling

### Comprehensive Validation

Use `validate_before_node_run()` for complex validation:

```python
def validate_before_node_run(self) -> list[Exception] | None:
    """Validate parameters before running the node."""
    exceptions = []

    model = self.get_parameter_value("model")
    if model == "advanced":
        images = self.get_parameter_list_value("images") or []
        if len(images) > MAX_IMAGES:
            exceptions.append(ValueError(
                f"{self.name}: Maximum {MAX_IMAGES} images allowed, got {len(images)}"
            ))

    return exceptions if exceptions else None
```

### Connection Validation Patterns

For complex nodes with multiple connection requirements:

```python
def _validate_iterative_connections(self) -> list[Exception]:
    """Validate that all required connections are properly established."""
    errors = []
    node_type = self._get_base_node_type_name()

    # Check if exec_out has outgoing connections
    if not _outgoing_connection_exists(self.name, self.exec_out.name):
        errors.append(
            Exception(
                f"{self.name}: Missing required connection from 'On Each Item'. "
                f"REQUIRED ACTION: Connect {node_type} Start to interior loop nodes. "
                "The start node must connect to other nodes to execute the loop body."
            )
        )

    # Check if loop has outgoing connection to End
    if self.end_node is None:
        errors.append(
            Exception(
                f"{self.name}: Missing required tethering connection. "
                f"REQUIRED ACTION: Connect {node_type} Start 'Loop End Node' to {node_type} End 'Loop Start Node'. "
                "This establishes the explicit relationship between start and end nodes."
            )
        )

    return errors
```

**Best Practice**: Provide detailed, actionable error messages that tell users exactly what connections are missing and how to fix them.

### Safe Defaults Pattern

Always set safe defaults before raising exceptions:

```python
def _set_safe_defaults(self) -> None:
    """Set safe default values for all outputs."""
    self.parameter_output_values["result"] = None
    self.parameter_output_values["status"] = "error"
    self.parameter_output_values["count"] = 0

def process(self) -> None:
    try:
        # Processing logic
        result = process_data()
        self.parameter_output_values["result"] = result
    except Exception as e:
        self._set_safe_defaults()
        raise RuntimeError(f"Processing failed: {str(e)}") from e
```

### URL Construction

Use `urllib.parse.urljoin()` for safe URL building:

```python
from urllib.parse import urljoin
import os

def __init__(self, **kwargs):
    super().__init__(**kwargs)

    # Safe URL construction
    base = os.getenv("API_BASE_URL", "https://api.example.com")
    base_slash = base if base.endswith("/") else base + "/"
    api_base = urljoin(base_slash, "api/")
    self._endpoint = urljoin(api_base, "v1/process/")
```

## Logging Best Practices

### Safe Logging Pattern

Prevent logging failures from breaking execution:

```python
from contextlib import suppress
import logging

logger = logging.getLogger(__name__)

def _log(self, message: str) -> None:
    """Safe logging with exception suppression."""
    with suppress(Exception):
        logger.info(message)
```

### Request Sanitization

Sanitize sensitive data in logs:

```python
from copy import deepcopy
import json

PROMPT_TRUNCATE_LENGTH = 100

def _log_request(self, payload: dict[str, Any]) -> None:
    """Log request with sanitized sensitive data."""
    with suppress(Exception):
        sanitized_payload = deepcopy(payload)

        # Truncate long prompts
        prompt = sanitized_payload.get("prompt", "")
        if len(prompt) > PROMPT_TRUNCATE_LENGTH:
            sanitized_payload["prompt"] = prompt[:PROMPT_TRUNCATE_LENGTH] + "..."

        # Redact base64 image data
        if "image" in sanitized_payload:
            image_data = sanitized_payload["image"]
            if isinstance(image_data, str) and image_data.startswith("data:image/"):
                parts = image_data.split(",", 1)
                header = parts[0] if parts else "data:image/"
                b64_len = len(parts[1]) if len(parts) > 1 else 0
                sanitized_payload["image"] = f"{header},<base64 data length={b64_len}>"

        self._log(f"Request: {json.dumps(sanitized_payload, indent=2)}")
```

## Flexible Artifact Processing

### Duck Typing for Artifacts

Handle multiple artifact formats gracefully:

```python
def _extract_image_value(self, image_input: Any) -> str | None:
    """Extract string value from various image input types."""
    if isinstance(image_input, str):
        return image_input

    try:
        # ImageUrlArtifact: .value holds URL string
        if hasattr(image_input, "value"):
            value = getattr(image_input, "value", None)
            if isinstance(value, str):
                return value

        # ImageArtifact: .base64 holds raw or data-URI
        if hasattr(image_input, "base64"):
            b64 = getattr(image_input, "base64", None)
            if isinstance(b64, str) and b64:
                return b64
    except Exception as e:
        self._log(f"Failed to extract image value: {e}")

    return None
```

### Image Format Conversion for External APIs

**Problem**: External APIs often have strict format requirements (e.g., JPEG, PNG, WebP only), but cameras may save images in unsupported formats like MPO (Multi Picture Object) for 3D/burst photos.

**Solution**: Automatically detect and convert unsupported formats:

```python
# Import at top of file
from PIL import Image
from io import BytesIO

def _get_image_data(self, image_artifact: ImageArtifact | ImageUrlArtifact) -> str:
    """Convert image to API-compatible format."""
    # ... extract image_bytes ...

    try:
        img = Image.open(BytesIO(image_bytes))

        # Convert unsupported formats (MPO, TIFF, BMP, etc.) to JPEG
        if img.format not in ['JPEG', 'PNG', 'WEBP']:
            self._log(f"Converting {img.format} to JPEG for API compatibility")
            # Convert to RGB if needed (for formats like MPO)
            if img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            # Save as JPEG to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=95)
            image_bytes = output.getvalue()
            mime_type = "image/jpeg"
        else:
            format_to_mime = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp'
            }
            mime_type = format_to_mime.get(img.format, 'image/jpeg')
    except Exception as e:
        self._log(f"Could not detect image format: {e}")
        mime_type = "image/jpeg"

    # Encode as base64 data URI
    base64_data = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"
```

**Key Points**:

- Apply conversion at all image input points (ImageArtifact, ImageUrlArtifact, localhost URLs)
- Use high quality (95%) to preserve image fidelity
- Handle color mode conversion (MPO often uses non-RGB modes)
- Log conversions for debugging
- Gracefully fall back to JPEG if detection fails

### Utility Function Patterns

Create reusable utility functions for common operations:

```python
# Connection checking utilities
def _outgoing_connection_exists(source_node: str, source_param: str) -> bool:
    """Check if a source node/parameter has any outgoing connections."""
    from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

    connections = GriptapeNodes.FlowManager().get_connections()
    source_connections = connections.outgoing_index.get(source_node)
    if source_connections is None:
        return False

    param_connections = source_connections.get(source_param)
    return bool(param_connections) if param_connections else False

def _incoming_connection_exists(target_node: str, target_param: str) -> bool:
    """Check if a target node/parameter has any incoming connections."""
    from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

    connections = GriptapeNodes.FlowManager().get_connections()
    target_connections = connections.incoming_index.get(target_node)
    if target_connections is None:
        return False

    param_connections = target_connections.get(target_param)
    return bool(param_connections) if param_connections else False
```

**Best Practice**: Create utility functions for common operations like connection checking, validation, and data processing.

### Flexible Image Processing

```python
def _image_to_bytes(self, image_artifact) -> bytes:
    """Convert various image artifact types to bytes."""
    if not image_artifact:
        raise ValueError("No input image provided")

    try:
        # Handle dictionary format (serialized artifacts)
        if isinstance(image_artifact, dict):
            image_url_artifact = self._dict_to_image_url_artifact(image_artifact)
            image_bytes = image_url_artifact.to_bytes()
        # Handle artifact objects directly
        elif isinstance(image_artifact, (ImageArtifact, ImageUrlArtifact)):
            image_bytes = image_artifact.to_bytes()
        else:
            # Try generic to_bytes method
            image_bytes = image_artifact.to_bytes()

        # Verify we have valid image data
        if not image_bytes or len(image_bytes) < 100:
            raise ValueError("Image data is empty or too small")

        return image_bytes

    except Exception as e:
        raise ValueError(f"Failed to extract image data: {str(e)}")
```

## Creating Node Libraries

Bundle nodes into libraries for sharing. Create `griptape_nodes_library.json`:

```json
{
  "name": "Library Name",
  "library_schema_version": "0.1.0",
  "settings": [
    {
      "description": "API keys required by nodes in this library",
      "category": "app_events.on_app_initialization_complete",
      "contents": {
        "secrets_to_register": ["MY_SERVICE_API_KEY", "MY_OTHER_API_KEY"]
      }
    }
  ],
  "metadata": {
    "author": "Author Name",
    "description": "Library description",
    "library_version": "1.0.0",
    "engine_version": "0.55.0",
    "tags": ["AI", "Image Processing"],
    "dependencies": {
      "pip_dependencies": ["pillow", "requests"],
      "pip_install_flags": ["--upgrade"]
    }
  },
  "widgets": [
    {
      "name": "MyWidget",
      "path": "widgets/MyWidget.js",
      "description": "Custom UI component for the node"
    }
  ],
  "categories": [
    {
      "image": {
        "title": "Image Processing",
        "description": "Image manipulation nodes",
        "color": "border-purple-500",
        "icon": "Image"
      }
    }
  ],
  "nodes": [
    {
      "class_name": "MyImageNode",
      "file_path": "image/my_image_node.py",
      "metadata": {
        "category": "image",
        "description": "Process images with AI",
        "display_name": "AI Image Processor",
        "icon": "image",
        "group": "processing"
      }
    }
  ],
  "workflows": ["workflows/example_workflow.py"],
  "is_default_library": false
}
```

### Library Structure

- **settings**: Register secrets/API keys used by library nodes
  - Use `secrets_to_register` array to declare required secrets
  - Category should be `app_events.on_app_initialization_complete`
  - Secrets are accessed via `GriptapeNodes.SecretsManager().get_secret()`
- **metadata.dependencies**: PIP packages installed on library load
- **widgets**: Register custom JS widget components (see [Custom Widget Components](#custom-widget-components))
- **categories**: Group nodes in UI with colors and icons
- **nodes**: List node classes, file paths, and metadata
- **workflows**: Template workflow files

**Important:** The `secrets_to_register` array tells the system which secrets your library needs. Users will be prompted to configure these secrets through the UI or environment variables.

Use flat directory structures. The engine automatically registers and loads libraries.

## Custom Widget Components

Nodes can use custom JavaScript widget components to provide rich, interactive UI beyond the standard parameter controls. Widgets are standalone `.js` files that render into a container element and communicate value changes back to the framework via a callback.

### Widget Architecture

A custom widget involves three pieces:

1. **Widget JS file** (`widgets/MyWidget.js`) — the UI component
2. **Node Python file** — references the widget via the `Widget` trait on a parameter
3. **Library JSON** (`griptape_nodes_library.json`) — registers the widget so the framework can find it

```
library_name/
├── griptape_nodes_library.json
├── my_node.py
└── widgets/
    └── MyWidget.js
```

### Registering a Widget

Add a `"widgets"` array to `griptape_nodes_library.json`:

```json
{
  "name": "My Library",
  "widgets": [
    {
      "name": "MyWidget",
      "path": "widgets/MyWidget.js",
      "description": "Description of the widget"
    }
  ],
  "nodes": [ ... ]
}
```

The `name` must match the name used in the `Widget` trait on the Python side, and the `library` argument must match the `"name"` field at the top level of the JSON.

### Attaching a Widget to a Parameter

Use the `Widget` trait to bind a parameter to your custom widget. The parameter's value is passed to the widget as `props.value`, and changes flow back through `props.onChange`:

```python
from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.traits.widget import Widget

self.add_parameter(
    Parameter(
        name="my_data",
        input_types=["list"],
        type="list",
        output_type="list",
        default_value=[],
        tooltip="Data managed by custom widget",
        allowed_modes={ParameterMode.PROPERTY, ParameterMode.OUTPUT},
        traits={Widget(name="MyWidget", library="My Library")},
    )
)
```

### Widget JS Function Signature

Widgets are ES module default exports. The function receives a container DOM element and a props object, and must return a cleanup function:

```javascript
export default function MyWidget(container, props) {
  const { value, onChange, disabled, height } = props;

  // Build your UI inside `container`
  // Call `onChange(newValue)` when the user changes data
  // Respect `disabled` to prevent interaction when appropriate

  // Return a cleanup function
  return () => {
    // Remove event listeners, dispose resources
  };
}
```

**Props:**

| Prop       | Type       | Description                                      |
| ---------- | ---------- | ------------------------------------------------ |
| `value`    | `any`      | Current parameter value (matches Python default)  |
| `onChange`  | `function` | Callback to send updated value to the framework  |
| `disabled` | `boolean`  | Whether the widget should be read-only            |
| `height`   | `number`   | Suggested height in pixels (may be 0 or absent)   |

### Critical Patterns and Pitfalls

#### Emit Changes Sparingly — Not on Every Keystroke

Calling `onChange` triggers framework state updates that steal focus from the active element. For text inputs, this means the textarea loses focus after every keystroke, making typing impossible. This is not specific to custom widgets — the built-in `TextComponent` in the Griptape Nodes editor uses the same pattern:

- **Local state** (your internal data array, counters, border colors) updates immediately on every `input` event.
- **`onChange`** is called only on `blur` — when the user clicks away or tabs out of the field.
- **Discrete controls** (buttons, steppers, drag-end) call `onChange` immediately since they don't hold focus.

```javascript
// Local state updates on every keystroke — UI stays responsive
textarea.addEventListener("input", (e) => {
  localData[index].text = e.target.value;
  // Update character counters, border colors, etc. here
});

// Emit to framework only when the user leaves the field
textarea.addEventListener("blur", () => {
  localData[index].text = textarea.value;
  onChange(structuredClone(localData));
});

// Discrete controls (buttons, steppers) can emit immediately
button.addEventListener("pointerdown", (e) => {
  e.stopPropagation();
  localData[index].value++;
  onChange(structuredClone(localData));
  render();
});
```

> **Why not `requestAnimationFrame` to restore focus?** Attempting to call `onChange` on every keystroke and then restore focus via `requestAnimationFrame` does not reliably work — the framework's React rendering cycle can complete asynchronously, and the focus restoration races with it.

#### Prevent Node Drag Interference

Node canvases handle drag events for panning and node movement. Interactive elements inside your widget must stop event propagation and use the `nodrag` / `nowheel` CSS classes:

```javascript
// On the outermost wrapper
const wrapper = document.createElement("div");
wrapper.className = "my-widget nodrag nowheel";

// On interactive child elements (textareas, sliders, etc.)
textarea.addEventListener("pointerdown", (e) => e.stopPropagation());
textarea.addEventListener("mousedown", (e) => e.stopPropagation());
```

#### Prevent Keyboard Shortcut Interference

The node editor binds keyboard shortcuts at the canvas level — for example, pressing `Delete` deletes the selected node. When a text input inside your widget has focus, these shortcuts still fire because keyboard events bubble up. Stop propagation on `keydown` to isolate your text inputs:

```javascript
textarea.addEventListener("keydown", (e) => e.stopPropagation());
```

This prevents the Delete key from deleting the node while the user is editing text, and stops other canvas-level shortcuts (copy, paste, undo at the node level) from interfering with normal text editing.

#### Override `user-select: none` for Text Inputs

Widget wrappers typically set `user-select: none` to prevent accidental text selection during drag operations. This cascades into child elements and blocks textarea editing. Override it explicitly:

```css
textarea {
  user-select: text;
  -webkit-user-select: text;
}
```

#### Clone Values Before Emitting

Always pass a fresh copy to `onChange` — not a reference to your internal state. Otherwise the framework and your widget share the same object, leading to subtle bugs:

```javascript
onChange(localData.map((item) => ({ ...item })));
```

#### Clean Up Document-Level Listeners

If you attach listeners to `document` (e.g., for drag-and-drop or click-outside-to-close), remove them in the cleanup function:

```javascript
document.addEventListener("pointerdown", onDocumentClick, true);

return () => {
  document.removeEventListener("pointerdown", onDocumentClick, true);
};
```

#### Assign Stable IDs to List Items

When building widgets that manage reorderable lists (e.g., drag-and-drop shot editors), give each item a unique ID that is decoupled from array index. Without stable IDs, item attributes such as text field contents can be lost during drag-and-drop reordering because the widget re-renders from scratch and identity was tied to position.

```javascript
let nextItemId = 1;

function assignId(item) {
  if (!item.id) {
    item.id = `item-${nextItemId++}`;
  } else {
    const num = parseInt(item.id.replace("item-", ""), 10);
    if (!isNaN(num) && num >= nextItemId) {
      nextItemId = num + 1;
    }
  }
  return item;
}

// On initialization — preserve existing IDs from saved data
let items = value.map((v) => assignId({ ...v }));

// When adding new items
items.push(assignId({ name: "New Item", text: "" }));
```

The ID persists through reorders, re-renders, and round-trips via `onChange`. The display name (e.g., "Shot1", "Shot2") can be renumbered based on visual position while the `id` remains stable.

#### Handle the `disabled` Attribute Correctly in DOM Helpers

If you write a DOM helper function that creates elements from an attributes object, be careful with the `disabled` attribute. Using `setAttribute("disabled", false)` does **not** remove the disabled state — the presence of the attribute in any form disables the element. Use the property instead:

```javascript
if (key === "disabled") {
  element.disabled = !!val;
}
```

#### Show Drop Indicators at End of List

When implementing drag-and-drop reordering, the drop target indicator (e.g., a blue border) must also appear when dragging past the last item in the list. A common approach: when the drag position is below all items, show a `border-bottom` on the last item instead of a `border-top` on a nonexistent next item:

```javascript
if (dragOverIndex === items.length && item.index === lastIndex) {
  item.el.style.borderBottom = "2px solid #4a9eff";
} else if (item.index === dragOverIndex) {
  item.el.style.borderTop = "2px solid #4a9eff";
}
```

### Example: List-Based Editor Widget

A common pattern is a widget that manages a list of structured items with add, delete, reorder, and inline editing. Key implementation details:

- **Stable IDs:** Assign a unique `id` to each item that survives reordering and round-trips through `onChange`.
- **Drag-and-drop reordering:** Attach `pointerdown` on drag handles, create a floating clone for visual feedback, track the insertion point via `pointermove`, and finalize the reorder on `pointerup`. Call `onChange` only after the drop. Show drop indicators at both middle and end-of-list positions.
- **Stepper controls:** For constrained numeric values (e.g., duration 1–15s), use ▲/▼ stepper buttons instead of dropdown menus. Disable buttons when they would violate constraints (min/max per item, max total across all items).
- **Validation constraints:** Enforce limits (max items, max total values, max text length) by disabling the add button and stepper arrows rather than silently ignoring input.
- **Status feedback:** Show a small status bar with current counts vs. limits (e.g., `"3 / 6 shots"`, `"8 / 15 s"`) so users understand why controls may be disabled.
- **Text input isolation:** Stop propagation on `pointerdown`, `mousedown`, and `keydown` to prevent node drag and keyboard shortcut interference. Emit `onChange` only on `blur`.

```python
# Python side — list parameter with widget
self.add_parameter(
    Parameter(
        name="items",
        input_types=["list"],
        type="list",
        output_type="list",
        default_value=[{"name": "Item1", "duration": 2, "description": ""}],
        allowed_modes={ParameterMode.PROPERTY, ParameterMode.OUTPUT},
        traits={Widget(name="MyListEditor", library="My Library")},
    )
)
```

```javascript
// JS side — skeleton for a list editor widget
export default function MyListEditor(container, props) {
  const { value, onChange, disabled } = props;

  // Stable ID assignment
  let nextId = 1;
  function assignId(item) {
    if (!item.id) item.id = `item-${nextId++}`;
    return item;
  }

  let items = Array.isArray(value)
    ? value.map((v) => assignId({ ...v }))
    : [assignId({ name: "Item1", duration: 2, description: "" })];

  function emitChange() {
    if (!disabled && onChange) {
      onChange(items.map((item) => ({ ...item })));
    }
  }

  function render() {
    container.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "nodrag nowheel";

    items.forEach((item, index) => {
      // ... build item row with drag handle, stepper, textarea, trash ...

      // Text input — local update on input, emit on blur
      textarea.addEventListener("input", (e) => {
        items[index].description = e.target.value;
      });
      textarea.addEventListener("blur", () => {
        items[index].description = textarea.value;
        emitChange();
      });

      // Isolate text input from node-level events
      textarea.addEventListener("pointerdown", (e) => e.stopPropagation());
      textarea.addEventListener("mousedown", (e) => e.stopPropagation());
      textarea.addEventListener("keydown", (e) => e.stopPropagation());
    });

    container.appendChild(wrapper);
  }

  render();

  return () => { /* cleanup document-level listeners */ };
}
```

## Contributing to the Standard Library

When adding nodes to the core `griptape_nodes_library` (as opposed to creating a standalone library), follow this process:

### 1. Create a Feature Branch

```bash
cd griptape-nodes
git checkout -b feature/add-color-match-node
```

### 2. Add the Node File

Place your node in the appropriate category subdirectory:

```
libraries/griptape_nodes_library/griptape_nodes_library/
├── image/
│   ├── color_match.py      # New node file
│   ├── load_image.py
│   └── save_image.py
├── text/
├── audio/
└── ...
```

### 3. Update griptape_nodes_library.json

Make three updates to `libraries/griptape_nodes_library/griptape_nodes_library.json`:

#### a. Increment the library version

```json
{
  "metadata": {
    "library_version": "0.59.0" // Was 0.58.0
  }
}
```

#### b. Add any new pip dependencies

```json
{
  "metadata": {
    "dependencies": {
      "pip_dependencies": [
        "existing-dep",
        "color-matcher" // New dependency
      ]
    }
  }
}
```

#### c. Add the node entry

```json
{
  "nodes": [
    {
      "class_name": "ColorMatch",
      "file_path": "griptape_nodes_library/image/color_match.py",
      "metadata": {
        "category": "image",
        "description": "Transfer color characteristics from a reference image to a target image",
        "display_name": "Color Match",
        "icon": "palette",
        "group": "edit"
      }
    }
  ]
}
```

### 4. Add Documentation

Create a documentation page at `docs/nodes/<category>/<node_name>.md`:

```markdown
# Color Match

Transfer color characteristics from a reference image to a target image.

## What It Does

Applies the color palette from a reference image to a target image...

## Parameters

### Inputs

| Parameter       | Type             | Description                 |
| --------------- | ---------------- | --------------------------- |
| reference_image | ImageUrlArtifact | Source of the color palette |
| target_image    | ImageUrlArtifact | Image to apply colors to    |

### Outputs

| Parameter    | Type             | Description          |
| ------------ | ---------------- | -------------------- |
| output_image | ImageUrlArtifact | Color-matched result |

## Example Usage

1. Connect a reference image with desired colors
2. Connect the target image to transform
3. Run the node

## Technical Details

Uses the color-matcher library with histogram matching...
```

### 5. Update mkdocs.yml Navigation

Add your doc page to the navigation in `mkdocs.yml`:

```yaml
nav:
  - Nodes Reference:
      - Image:
          - Load Image: nodes/image/load_image.md
          - Save Image: nodes/image/save_image.md
          - Color Match: nodes/image/color_match.md # New entry
```

### 6. Run Quality Checks

Before committing, run formatting and checks:

```bash
make format        # Auto-format code
make check/lint    # Check for linting issues
make check/types   # Check for type errors
```

Fix any issues that arise before proceeding.

### 7. Commit and Create PR

```bash
git add .
git commit -m "feat(image): add ColorMatch node for color transfer"
git push -u origin HEAD
gh pr create --title "Add ColorMatch node" --body "## Summary
- Adds ColorMatch node for transferring colors between images
- Uses color-matcher library
- Includes documentation

## Test plan
- [ ] Load two images
- [ ] Run color match
- [ ] Verify output has reference colors"
```

### Standard Library vs External Library

| Aspect       | Standard Library                            | External Library                  |
| ------------ | ------------------------------------------- | --------------------------------- |
| Location     | `griptape-nodes` repo                       | Separate repo                     |
| Installation | Included by default                         | User installs                     |
| Review       | Requires PR approval                        | Self-published                    |
| Dependencies | Added to core `griptape_nodes_library.json` | Own `griptape_nodes_library.json` |
| Versioning   | Follows core library version                | Independent versioning            |
| Docs         | Added to main docs site                     | README in library                 |

**When to contribute to standard library:**

- Node has broad utility for many users
- No proprietary/paid API dependencies
- Stable, well-tested implementation
- Follows all code quality standards

**When to create external library:**

- Niche use case
- Requires paid API keys
- Experimental/rapidly changing
- Want independent release cycle

## Appendix

### Imports

```python
# Core imports
from griptape_nodes.exe_types.core_types import (
    Parameter, ParameterList, ParameterMode, ParameterTypeBuiltin,
    ParameterGroup, ParameterMessage, ControlParameterInput, ControlParameterOutput
)
from griptape_nodes.exe_types.node_types import (
    DataNode, ControlNode, BaseNode, SuccessFailureNode,
    StartNode, EndNode
)
from griptape_nodes.exe_types.base_iterative_nodes import BaseIterativeStartNode, BaseIterativeEndNode
from griptape_nodes.traits.options import Options
from griptape_nodes.traits.slider import Slider
from griptape_nodes.traits.color_picker import ColorPicker
from griptape_nodes.traits.file_system_picker import FileSystemPicker

# Artifacts
from griptape.artifacts import ImageArtifact, ImageUrlArtifact, TextArtifact

# Utilities
from griptape_nodes_library.utils.artifact_path_tethering import (
    ArtifactPathTethering, ArtifactTetheringConfig
)
from griptape_nodes_library.utils.image_utils import (
    dict_to_image_url_artifact,
    load_pil_from_url,
    save_pil_image_with_named_filename,
)
from griptape_nodes_library.utils.file_utils import generate_filename
```

### Utility Function Reference

#### Image Utilities (`griptape_nodes_library.utils.image_utils`)

| Function                                            | Purpose                                         | Returns            |
| --------------------------------------------------- | ----------------------------------------------- | ------------------ |
| `dict_to_image_url_artifact(d)`                     | Convert dict representation to ImageUrlArtifact | `ImageUrlArtifact` |
| `load_pil_from_url(url)`                            | Load PIL Image from URL (handles localhost)     | `PIL.Image.Image`  |
| `save_pil_image_with_named_filename(img, filename)` | Save PIL Image to static storage                | `ImageUrlArtifact` |

**Example usage:**

```python
from griptape_nodes_library.utils.image_utils import (
    dict_to_image_url_artifact,
    load_pil_from_url,
    save_pil_image_with_named_filename,
)

# Convert parameter value to artifact
value = self.get_parameter_value("image")
if isinstance(value, dict):
    artifact = dict_to_image_url_artifact(value)
else:
    artifact = value

# Load as PIL for processing
pil_image = load_pil_from_url(artifact.value)

# Process image...
processed = pil_image.filter(...)

# Save and get output artifact
output_artifact = save_pil_image_with_named_filename(processed, "result.png")
self.parameter_output_values["output"] = output_artifact
```

#### File Utilities (`griptape_nodes_library.utils.file_utils`)

| Function                                    | Purpose                    | Returns |
| ------------------------------------------- | -------------------------- | ------- |
| `generate_filename(node_name, suffix, ext)` | Create consistent filename | `str`   |

**Example usage:**

```python
from griptape_nodes_library.utils.file_utils import generate_filename

# Generate filename like "ColorMatch_processed_abc123.png"
filename = generate_filename(self.name, suffix="processed", ext="png")
```

### Advanced Parameter Types

- **ControlParameterInput/Output**: For execution flow control
- **ParameterGroup**: For organizing related parameters with collapsible UI
- **ParameterMessage**: For status updates and external links
- **ParameterList**: For accepting multiple inputs of the same type

### Enumerations

- **NodeResolutionState**: UNRESOLVED, RESOLVING, RESOLVED
- **ParameterMode**: INPUT, OUTPUT, PROPERTY
- **ParameterTypeBuiltin**: STR("str"), BOOL("bool"), INT("int"), FLOAT("float"), ANY("any"), NONE("none"), CONTROL_TYPE("parametercontroltype"), ALL("all")

### Advanced Node Types

- **BaseNode**: Most basic node type for custom implementations
- **DataNode**: For data processing without execution flow
- **ControlNode**: For nodes that manage execution flow
- **SuccessFailureNode**: For operations that can succeed or fail
- **BaseIterativeStartNode/BaseIterativeEndNode**: For iterative operations
- **AsyncResult**: For asynchronous processing operations

### Custom Artifacts

Inherit from BaseArtifact and override methods as needed:

```python
from griptape.artifacts import BaseArtifact

class CustomArtifact(BaseArtifact):
    def __init__(self, value: Any, **kwargs):
        super().__init__(value, **kwargs)

    def to_text(self) -> str:
        return str(self.value)
```

### Advanced Lifecycle Methods

#### Spotlight Control

For conditional dependency resolution:

```python
def initialize_spotlight(self) -> None:
    """Custom spotlight initialization - only include evaluate parameter initially."""
    evaluate_param = self.get_parameter_by_name("evaluate")
    if evaluate_param and ParameterMode.INPUT in evaluate_param.get_mode():
        self.current_spotlight_parameter = evaluate_param

def advance_parameter(self) -> bool:
    """Custom parameter advancement with conditional dependency resolution."""
    if self.current_spotlight_parameter is None:
        return False

    # Special handling for conditional parameters
    if self.current_spotlight_parameter is self.evaluate:
        try:
            evaluation_result = self.check_evaluation()
            next_param = self.output_if_true if evaluation_result else self.output_if_false

            if ParameterMode.INPUT in next_param.get_mode():
                self.current_spotlight_parameter.next = next_param
                next_param.prev = self.current_spotlight_parameter
                self.current_spotlight_parameter = next_param
                return True
        except Exception:
            self.current_spotlight_parameter = None
            return False

    return super().advance_parameter()
```

#### Control Flow Management

```python
def get_next_control_output(self) -> Parameter | None:
    """Return the appropriate control output based on evaluation."""
    if "evaluate" not in self.parameter_output_values:
        self.stop_flow = True
        return None

    if self.parameter_output_values["evaluate"]:
        return self.get_parameter_by_name("Then")
    return self.get_parameter_by_name("Else")
```

## Asynchronous API Integration

### Process Method with Yield Syntax

For nodes that perform long-running asynchronous operations, use the `yield` syntax to properly handle async processing:

```python
from griptape_nodes.exe_types.node_types import DataNode, AsyncResult

class MyAsyncNode(DataNode):
    def process(self) -> AsyncResult | None:
        """Process the request asynchronously."""
        yield lambda: self._process()

    def _process(self) -> None:
        """Main processing method."""
        try:
            # Set safe defaults
            self._set_safe_defaults()

            # Validate API key
            api_key = self._validate_api_key()

            # Submit task
            task_id = self._submit_task(api_key)

            # Poll for completion
            result = self._poll_for_completion(task_id, api_key)

            # Process result
            self.parameter_output_values["output"] = result

        except Exception as e:
            self._set_safe_defaults()
            self._log(f"Processing failed: {e}")
            raise RuntimeError(f"{self.name}: {str(e)}") from e
```

**Key Points:**

- `process()` returns `AsyncResult | None` and yields a lambda
- Actual work is done in `_process()` method
- Pattern matches Minimax and other async nodes
- Enables proper async handling in the workflow engine

### Polling Pattern for Long-Running Tasks

When integrating with APIs that use asynchronous task processing (video generation, model training, etc.), implement a three-step pattern:

#### Step 1: Task Submission

```python
def _submit_task(self, params: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    """Submit task and return response with task_id."""
    payload = self._build_payload(params)

    response = requests.post(
        self.API_BASE_URL,
        json=payload,
        headers=headers,
        timeout=DEFAULT_TIMEOUT
    )
    response.raise_for_status()

    response_data = response.json()
    task_id = response_data.get("task_id")
    return response_data
```

#### Step 2: Status Polling

```python
POLLING_INTERVAL = 10  # seconds (use API-recommended value)
MAX_POLLING_ATTEMPTS = 60  # 10 minutes max

def _poll_for_completion(self, task_id: str, headers: dict[str, str]) -> str | None:
    """Poll API for task completion and return result identifier."""
    query_url = "https://api.example.com/v1/query/task"

    for attempt in range(MAX_POLLING_ATTEMPTS):
        time.sleep(POLLING_INTERVAL)  # Wait before each poll

        response = requests.get(
            query_url,
            headers=headers,
            params={"task_id": task_id},  # Use query params, not path
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()

        status_data = response.json()
        status = status_data.get("status")

        self._log(f"Polling attempt {attempt + 1}: Status = {status}")

        if status == "Success":
            file_id = status_data.get("file_id")
            return file_id
        elif status == "Fail":
            error_msg = status_data.get("error_message", "Unknown error")
            raise RuntimeError(f"Task failed: {error_msg}")
        # Continue polling for "Processing", "Pending", etc.

    raise RuntimeError(f"Task did not complete within {MAX_POLLING_ATTEMPTS * POLLING_INTERVAL} seconds")
```

#### Step 3: Result Retrieval

```python
def _retrieve_result(self, file_id: str, headers: dict[str, str]) -> str:
    """Retrieve download URL from result identifier."""
    retrieve_url = "https://api.example.com/v1/files/retrieve"

    response = requests.get(
        retrieve_url,
        headers=headers,
        params={"file_id": file_id},
        timeout=DEFAULT_TIMEOUT
    )
    response.raise_for_status()

    response_data = response.json()
    download_url = response_data.get("file", {}).get("download_url")

    return download_url
```

**Key Considerations:**

- Always use API-recommended polling intervals (typically 5-10 seconds)
- Set reasonable maximum attempts to prevent infinite loops
- Use query parameters, not path parameters, for task_id (verify with API docs)
- Handle all status states: Success, Fail, Processing, Pending
- Log polling attempts for debugging
- Set safe defaults on failure

### Image Artifact Conversion to Base64

**CRITICAL: Localhost URL Handling**

When sending images to external APIs, ImageUrlArtifact URLs from static storage are localhost and inaccessible to external services. Always detect and convert localhost URLs to base64:

```python
import base64

def _get_image_data(self, image_artifact: ImageArtifact | ImageUrlArtifact) -> str:
    """Convert image artifact to URL or base64 data URI."""

    # ImageUrlArtifact - check if localhost or public URL
    if isinstance(image_artifact, ImageUrlArtifact):
        url = image_artifact.value

        # Localhost URLs must be converted to base64 for external APIs
        if url.startswith(('http://localhost', 'http://127.0.0.1',
                          'https://localhost', 'https://127.0.0.1')):
            self._log(f"Converting localhost URL to base64: {url[:100]}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            image_bytes = response.content

            # Detect MIME type from headers
            mime_type = response.headers.get('content-type', 'image/jpeg')
            if not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'

            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:{mime_type};base64,{base64_data}"

        # Public URLs can be passed through
        self._log(f"Using public URL: {url[:100]}...")
        return url

    # ImageArtifact - use .base64 property (preferred method)
    if isinstance(image_artifact, ImageArtifact):
        # PREFERRED: Use built-in properties
        if hasattr(image_artifact, 'base64') and hasattr(image_artifact, 'mime_type'):
            base64_data = image_artifact.base64  # Raw base64 (no prefix)
            mime_type = image_artifact.mime_type  # e.g., 'image/jpeg'

            # Check if already has data URI prefix
            if base64_data.startswith('data:'):
                self._log("Using ImageArtifact.base64 (already has data URI)")
                return base64_data

            # Add data URI prefix
            self._log(f"Using ImageArtifact.base64 with mime_type: {mime_type}")
            return f"data:{mime_type};base64,{base64_data}"

        # FALLBACK: Manual byte extraction
        self._log("Falling back to manual base64 encoding")
        if hasattr(image_artifact, 'value') and hasattr(image_artifact.value, 'read'):
            image_artifact.value.seek(0)
            image_bytes = image_artifact.value.read()
        elif hasattr(image_artifact, 'data'):
            if isinstance(image_artifact.data, bytes):
                image_bytes = image_artifact.data
            elif hasattr(image_artifact.data, 'read'):
                image_artifact.data.seek(0)
                image_bytes = image_artifact.data.read()
            else:
                raise ValueError("Unsupported ImageArtifact format")
        else:
            raise ValueError("Unsupported ImageArtifact format")

        # Detect MIME type with PIL
        mime_type = "image/jpeg"
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            format_to_mime = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp'
            }
            mime_type = format_to_mime.get(img.format, 'image/jpeg')
        except Exception:
            pass

        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"

    raise ValueError("Unsupported artifact type")
```

**Key Points:**

1. **Always detect localhost URLs** - External APIs cannot access them
2. **Use ImageArtifact.base64 property** - The proper Griptape way (returns raw base64)
3. **Use ImageArtifact.mime_type property** - Automatic MIME type detection
4. **Log which path is used** - Essential for debugging
5. **Download localhost files** - Convert to base64 before sending to API

**Parameter Definition:**

```python
Parameter(
    name="image_input",
    input_types=["ImageArtifact", "ImageUrlArtifact"],  # Accept both
    type="ImageArtifact",
    tooltip="Image input (file or URL)",
    ui_options={"clickable_file_browser": True},  # Enable file browser
)
```

### Multi-Image Input Validation

When nodes accept multiple image parameters, use a reusable validation method with clear parameter identification:

```python
def _validate_image(self, image_artifact: ImageArtifact | ImageUrlArtifact,
                    param_name: str) -> list[Exception]:
    """Validate image with parameter name in error messages."""
    exceptions = []

    if isinstance(image_artifact, ImageArtifact):
        # Get image bytes
        if hasattr(image_artifact, 'value') and hasattr(image_artifact.value, 'read'):
            image_artifact.value.seek(0)
            image_bytes = image_artifact.value.read()
            image_artifact.value.seek(0)
        else:
            return exceptions

        # Validate size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb >= 20:
            exceptions.append(ValueError(
                f"{self.name}: {param_name} size must be < 20MB (current: {size_mb:.1f}MB)"
            ))

        # Validate format and dimensions
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))

            if img.format not in ['JPEG', 'PNG', 'WEBP']:
                exceptions.append(ValueError(
                    f"{self.name}: {param_name} format must be JPG, PNG, or WebP (current: {img.format})"
                ))

            width, height = img.size
            short_edge = min(width, height)
            if short_edge <= 300:
                exceptions.append(ValueError(
                    f"{self.name}: {param_name} short edge must be > 300px (current: {short_edge}px)"
                ))
        except ImportError:
            self._log("PIL not available for validation")
        except Exception as e:
            self._log(f"Error validating {param_name}: {e}")

    return exceptions

def validate_before_node_run(self) -> list[Exception] | None:
    """Validate all image parameters."""
    exceptions = []

    # Validate each image parameter independently
    first_frame = self.get_parameter_value("first_frame_image")
    if first_frame:
        exceptions.extend(self._validate_image(first_frame, "first_frame_image"))

    last_frame = self.get_parameter_value("last_frame_image")
    if last_frame:
        exceptions.extend(self._validate_image(last_frame, "last_frame_image"))

    return exceptions if exceptions else None
```

**Benefits:**

- Clear error messages identifying which image parameter has issues
- Reusable validation logic across multiple image inputs
- Independent validation for each parameter
- Actionable feedback for users

### Model-Dependent Parameter Management

When different models support different parameter combinations:

```python
def after_value_set(self, parameter: Parameter, value: Any) -> None:
    """Handle model-dependent parameter visibility and options."""
    if parameter.name == "model":
        if value == "AdvancedModel":
            # Show model-specific parameters
            self.show_parameter_by_name("advanced_option")

            # Update dropdown choices dynamically
            resolution_param = self.get_parameter_by_name("resolution")
            if resolution_param:
                for child in resolution_param.children:
                    if hasattr(child, 'choices'):
                        child.choices = ADVANCED_MODEL_RESOLUTIONS
                        break
        else:
            # Hide and reset for other models
            self.hide_parameter_by_name("advanced_option")

            # Update to standard choices
            resolution_param = self.get_parameter_by_name("resolution")
            if resolution_param:
                for child in resolution_param.children:
                    if hasattr(child, 'choices'):
                        child.choices = STANDARD_RESOLUTIONS
                        break
                self.set_parameter_value("resolution", "720P")

    return super().after_value_set(parameter, value)
```

**Model-Specific Validation:**

```python
def validate_before_node_run(self) -> list[Exception] | None:
    """Validate model-specific parameter combinations."""
    exceptions = []

    model = self.get_parameter_value("model")
    duration = self.get_parameter_value("duration")
    resolution = self.get_parameter_value("resolution")

    # Example: 10s only for specific model/resolution
    if duration == 10:
        if model != "AdvancedModel":
            exceptions.append(ValueError(f"{self.name}: 10s duration only supported by AdvancedModel"))
        elif resolution == "4K":
            exceptions.append(ValueError(f"{self.name}: 10s duration not supported with 4K resolution"))

    # Model-specific parameter requirements
    if model in ["ModelB", "ModelC"]:
        required_param = self.get_parameter_value("required_for_model_b_c")
        if not required_param:
            exceptions.append(ValueError(f"{self.name}: Parameter required for {model}"))

    return exceptions if exceptions else None
```

### Enhanced Debug Logging for API Integration

For nodes that integrate with external APIs, implement comprehensive debug logging to quickly diagnose issues:

```python
# Task Submission - Log full response
def _submit_task(self, params: dict, headers: dict) -> dict:
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()

    response_data = response.json()
    self._log(f"Task submission response: {json.dumps(response_data, indent=2)}")
    return response_data

# Payload Sizes - Log data sizes before sending
def _log_request(self, payload: dict) -> None:
    if "first_frame_image" in payload:
        img_len = len(payload.get("first_frame_image", ""))
        self._log(f"first_frame_image data length: {img_len} chars (~{img_len/1024:.1f}KB)")

    if "last_frame_image" in payload:
        img_len = len(payload.get("last_frame_image", ""))
        self._log(f"last_frame_image data length: {img_len} chars (~{img_len/1024:.1f}KB)")

# Error Responses - Log full API error details
def _poll_for_completion(self, task_id: str, headers: dict) -> str:
    status_data = response.json()
    status = status_data.get("status")

    if status == "Fail":
        # Log complete error response for debugging
        self._log(f"Full API error response: {json.dumps(status_data, indent=2)}")
        error_msg = status_data.get("error_message", "Unknown error")
        raise RuntimeError(f"Task failed: {error_msg}")

# Processing Paths - Log which code path is executed
def _get_image_data(self, image_artifact) -> str:
    if isinstance(image_artifact, ImageUrlArtifact):
        if url.startswith('http://localhost'):
            self._log(f"Converting localhost URL to base64: {url[:100]}...")
        else:
            self._log(f"Using public URL: {url[:100]}...")
    elif isinstance(image_artifact, ImageArtifact):
        if hasattr(image_artifact, 'base64'):
            self._log(f"Using ImageArtifact.base64 with mime_type: {mime_type}")
        else:
            self._log("Falling back to manual base64 encoding")
```

**What to Log:**

- **Full API responses** (submission, polling, retrieval)
- **Payload sizes** (especially for base64 data)
- **Processing paths** (which code branches execute)
- **Model/parameter combinations** being used
- **Error details** (full error response from API)

**Benefits:**

- Quickly identify where failures occur
- Understand what data is being sent
- Track which code paths execute
- Get exact API error messages and codes
- Debug without reproducing issues

### API Documentation Verification

**Critical Best Practice:** Always verify API specifications directly from documentation.

**Common Pitfalls to Avoid:**

1. **Model Names**: Check exact capitalization (`MiniMax-Hailuo-02` not `video-01`)
2. **Endpoints**: Verify exact URLs (`/v1/query/video_generation` not `/v1/video_generation/{id}`)
3. **Parameters**: Check query params vs path params
4. **Response Structure**: Verify exact field names (`file_id` vs `file_list`)
5. **Polling Intervals**: Use API-recommended values

**Example: Correct vs Incorrect Polling:**

```python
# ✅ CORRECT: Query parameter
response = requests.get(
    "https://api.example.com/v1/query/task",
    params={"task_id": task_id}
)

# ❌ INCORRECT: Path parameter (unless API specifies this)
response = requests.get(
    f"https://api.example.com/v1/query/task/{task_id}"
)
```

**When Documentation is Inaccessible:**

- Explicitly state inability to access web pages (e.g., JavaScript-heavy docs)
- Request user to provide relevant documentation sections
- Never assume or infer API patterns without verification
- Update implementation when code samples are provided

### Library Structure with uv Dependency Management

**Modern Approach**: Use `uv` for fast, reproducible dependency management following the Minimax library pattern.

#### Directory Structure

```
library-name/
├── pyproject.toml              # uv configuration
├── uv.lock                     # Lock file (generated)
├── LICENSE                     # License file
├── README.md                   # Documentation
├── CHANGELOG.md                # Version history
├── .gitignore                  # Ignore rules
└── library_name/
    ├── griptape_nodes_library.json  # Library metadata
    └── node_file.py
```

#### pyproject.toml Configuration

```toml
[project]
name = "library-name"
version = "1.0.0"
description = "Description of your library"
authors = [
    {name = "Your Name", email = "email@example.com"}
]
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "griptape-nodes",
    "requests",
    # Add other dependencies
]

[tool.uv.sources]
griptape-nodes = { git = "https://github.com/griptape-ai/griptape-nodes", rev="latest"}

[tool.hatch.build.targets.wheel]
packages = ["library_name"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Library Configuration (inside subdirectory)

Place `griptape_nodes_library.json` inside the library subdirectory:

```json
{
  "name": "Library Name",
  "library_schema_version": "0.1.0",
  "settings": [
    {
      "description": "API keys required by nodes",
      "category": "app_events.on_app_initialization_complete",
      "contents": {
        "secrets_to_register": ["API_KEY_NAME"]
      }
    }
  ],
  "nodes": [
    {
      "class_name": "NodeClassName",
      "file_path": "node_file.py", // Relative to library subdirectory
      "metadata": {
        "category": "category_name",
        "description": "Node description",
        "display_name": "Node Display Name"
      }
    }
  ]
}
```

#### Installation Instructions in README

Provide both uv (recommended) and pip (fallback) installation methods:

````markdown
## Installation

### Option 1: Using uv (Recommended)

1. Clone or download this library
2. Install dependencies:
   ```bash
   cd library-name
   uv sync
   ```
````

3. Place in Griptape Nodes libraries directory

### Option 2: Automatic Installation

1. Place folder in libraries directory
2. Dependencies install automatically via pip

````

#### Generate Lock File

```bash
cd library-name
uv sync
````

**Benefits:**

- Fast installation (Rust-based)
- Reproducible builds via lock file
- Direct GitHub integration for griptape-nodes
- Backward compatible with pip installation

### Two-Mode UI Pattern (Simple + Custom)

**Use Case**: Create beginner-friendly nodes while offering advanced control for power users.

**Example**: Music/video generation APIs often have "simple description" mode and "detailed control" mode.

#### Implementation Pattern

```python
class GenerativeNode(DataNode):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Mode selector
        mode_param = Parameter(
            name="custom_mode",
            input_types=["bool"],
            type="bool",
            default_value=False,
            tooltip="Custom Mode: Full control. Simple Mode: Auto-generate from prompt.",
            allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
            ui_options={"display_name": "Custom Mode"},
        )
        self.add_parameter(mode_param)

        # Prompt (meaning changes by mode)
        prompt_param = Parameter(
            name="prompt",
            input_types=["str"],
            type="str",
            default_value="",
            tooltip=[
                {"type": "text", "text": "Custom Mode: Exact lyrics/script"},
                {"type": "text", "text": "Simple Mode: General description"},
            ],
            allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
            ui_options={"multiline": True, "display_name": "Prompt"},
        )
        self.add_parameter(prompt_param)

        # Advanced parameters (custom mode only)
        style_param = Parameter(
            name="style",
            input_types=["str"],
            type="str",
            default_value="",
            tooltip="Style/genre (Custom Mode only)",
            allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
            ui_options={"hide": True},  # Hidden by default
        )
        self.add_parameter(style_param)

        title_param = Parameter(
            name="title",
            input_types=["str"],
            type="str",
            default_value="",
            tooltip="Title (Custom Mode only)",
            allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
            ui_options={"hide": True},  # Hidden by default
        )
        self.add_parameter(title_param)

        # Initialize visibility
        self._initialize_parameter_visibility()

    def _initialize_parameter_visibility(self) -> None:
        """Initialize parameter visibility based on default mode."""
        custom_mode = self.get_parameter_value("custom_mode") or False
        if custom_mode:
            self.show_parameter_by_name("style")
            self.show_parameter_by_name("title")
        else:
            self.hide_parameter_by_name("style")
            self.hide_parameter_by_name("title")

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        """Update UI based on mode selection."""
        if parameter.name == "custom_mode":
            if value:
                self.show_parameter_by_name("style")
                self.show_parameter_by_name("title")
            else:
                self.hide_parameter_by_name("style")
                self.hide_parameter_by_name("title")

        return super().after_value_set(parameter, value)

    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate based on selected mode."""
        exceptions = []
        custom_mode = self.get_parameter_value("custom_mode")

        if custom_mode:
            # Custom mode requires style and title
            style = self.get_parameter_value("style") or ""
            title = self.get_parameter_value("title") or ""

            if not style.strip():
                exceptions.append(ValueError(f"{self.name}: Style required in Custom Mode"))
            if not title.strip():
                exceptions.append(ValueError(f"{self.name}: Title required in Custom Mode"))
        else:
            # Simple mode just needs prompt
            prompt = self.get_parameter_value("prompt") or ""
            if not prompt.strip():
                exceptions.append(ValueError(f"{self.name}: Prompt required in Simple Mode"))

        return exceptions if exceptions else None
```

**Best Practice for First-Time Users**: Default to Simple Mode with recommendation in documentation:

```markdown
### Getting Started

#### Simple Mode (Recommended for First-Time Users)

1. Leave "Custom Mode" unchecked
2. Enter a description: "A calm piano melody"
3. Run!

#### Custom Mode (Advanced)

1. Check "Custom Mode"
2. Fill in style, title, and detailed prompt
3. Fine-tune advanced parameters
```

### Music/Audio Generation API Patterns

#### Character Limits by Model

Many generation APIs have model-specific character limits. Store limits as class constants:

```python
class MusicGenerationNode(DataNode):
    # Prompt length limits by model
    PROMPT_LIMITS_CUSTOM = {
        "V3_5": 3000,
        "V4": 3000,
        "V4_5": 5000,
        "V5": 5000,
    }
    PROMPT_LIMIT_SIMPLE = 500

    # Style length limits by model
    STYLE_LIMITS = {
        "V3_5": 200,
        "V4": 200,
        "V4_5": 1000,
        "V5": 1000,
    }

    TITLE_LIMIT = 80

    def validate_before_node_run(self) -> list[Exception] | None:
        """Validate with model-specific limits."""
        exceptions = []
        model = self.get_parameter_value("model")
        custom_mode = self.get_parameter_value("custom_mode")

        if custom_mode:
            prompt = self.get_parameter_value("prompt") or ""
            prompt_limit = self.PROMPT_LIMITS_CUSTOM.get(model, 3000)
            if len(prompt) > prompt_limit:
                exceptions.append(ValueError(
                    f"{self.name}: Prompt exceeds {prompt_limit} character limit for {model} "
                    f"(current: {len(prompt)} characters)"
                ))

            style = self.get_parameter_value("style") or ""
            style_limit = self.STYLE_LIMITS.get(model, 200)
            if len(style) > style_limit:
                exceptions.append(ValueError(
                    f"{self.name}: Style exceeds {style_limit} character limit for {model} "
                    f"(current: {len(style)} characters)"
                ))

        return exceptions if exceptions else None
```

#### Model Selection with Detailed Tooltips

Use list of dict tooltip format for model comparison:

```python
model_param = Parameter(
    name="model",
    input_types=["str"],
    type="str",
    default_value="V5",
    tooltip=[
        {"type": "text", "text": "Model version for generation:"},
        {"type": "text", "text": "• V5: Superior quality, fastest (4 min max)"},
        {"type": "text", "text": "• V4_5PLUS: Richest sound, up to 8 min"},
        {"type": "text", "text": "• V4_5: Superior blending, up to 8 min"},
        {"type": "text", "text": "• V4: Best quality, refined structure (4 min)"},
        {"type": "text", "text": "• V3_5: Creative diversity (4 min)"},
    ],
    allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
)
model_param.add_trait(Options(choices=["V5", "V4_5PLUS", "V4_5", "V4", "V3_5"]))
```

#### Dual Track Output Pattern

APIs that generate multiple variations:

```python
# Output parameter for multiple tracks
music_urls_param = Parameter(
    name="music_urls",
    output_type="list[str]",
    type="list[str]",
    tooltip="Download URLs for generated tracks (2 variations)",
    allowed_modes={ParameterMode.OUTPUT},
    settable=False,
    ui_options={"is_full_width": True, "display_name": "Music URLs"},
)
self.add_parameter(music_urls_param)

def process(self) -> None:
    # ... generation logic ...
    urls = self._extract_music_urls(response_data)
    self.parameter_output_values["music_urls"] = urls

    # Build detailed result
    result_lines = [
        f"✓ Generated {len(urls)} track variation(s)",
        "",
        "Music URLs:",
    ]
    for i, url in enumerate(urls, 1):
        result_lines.append(f"{i}. {url}")

    self.parameter_output_values["result_details"] = "\n".join(result_lines)
```

#### Status Updates During Long Operations

Update status parameter in real-time during polling:

```python
def _poll_for_completion(self, task_id: str, api_key: str) -> dict[str, Any]:
    """Poll API with real-time status updates."""
    for attempt in range(self.MAX_POLLING_ATTEMPTS):
        time.sleep(self.POLLING_INTERVAL)

        # Update status parameter with progress
        status_msg = f"Generating... ({attempt + 1}/{self.MAX_POLLING_ATTEMPTS})"
        self.set_parameter_value("status", status_msg)

        response = requests.get(query_url, headers=headers, params={"ids": task_id})
        # ... check completion ...
```

**Best Practice**: Always provide progress feedback for operations longer than 10 seconds.

### Documentation Patterns for Node Libraries

#### Comprehensive README Structure

```markdown
# Library Name

Brief description and key features.

## Features

- Bullet list of main capabilities
- Include model options
- Highlight unique features

## Installation

### Option 1: Using uv (Recommended)

Steps for uv installation

### Option 2: Automatic Installation

Steps for pip installation

## Getting Started

### Simple Mode (Recommended for First-Time Users)

Minimal example with explanations

### Custom Mode (Advanced)

Advanced example showing all features

## Parameters

### Basic Parameters

Table with Name, Type, Description

### Advanced Parameters (Hidden by Default)

Table with Name, Type, Default, Description

### Output Parameters

Table with outputs

## Model Comparison

Table comparing models:
| Model | Max Duration | Quality | Speed | Character Limits |

## Character Limits

Clear tables showing limits by model/mode

## API Rate Limits

Document:

- Concurrency limits
- Generation time expectations
- File retention policies

## Example Workflows

3-5 complete examples covering common use cases

## Error Handling

Common errors and solutions

## Troubleshooting

FAQ-style troubleshooting guide

## API Reference

Link to official API docs

## Best Practices

Tips for optimal usage

## Support

Where to get help

## Version History

Link to CHANGELOG
```

#### Model Comparison Table

Always include a comparison table for services with multiple models:

```markdown
| Model | Max Duration | Quality  | Speed   | Character Limits          |
| ----- | ------------ | -------- | ------- | ------------------------- |
| V5    | 4 min        | Superior | Fastest | Prompt: 5000, Style: 1000 |
| V4_5  | 8 min        | High     | Fast    | Prompt: 5000, Style: 1000 |
| V4    | 4 min        | Best     | Medium  | Prompt: 3000, Style: 200  |
```

---

This guide represents the current best practices for Griptape node development, incorporating both foundational concepts and modern patterns demonstrated in production nodes. Use these patterns to create robust, user-friendly, and maintainable nodes that integrate seamlessly with the Griptape ecosystem.
