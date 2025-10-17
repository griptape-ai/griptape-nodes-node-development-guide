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
15. [Appendix](#appendix)

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
- **settable**: bool (default True) - False for computed/output parameters
- **user_defined**: bool (default False)
- **parent_container_name**: str|None for grouping

### Traits

Add functionality via `add_trait()`:

- **Options**: `Options(choices=list[str]|list[tuple[str,Any]])`
- **Slider**: `Slider(min_val:int|float, max_val:int|float)`
- **Button**: `Button(button_type:str)` (e.g., "save", "open", "action")
- **ColorPicker**: `ColorPicker(format="hex")`

### Containers

- **ParameterList**: For multiple inputs of the same type
- **ParameterDictionary**: For key-value parameter collections
- **ParameterGroup**: For UI grouping

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
tools = self.get_parameter_list_value("tools")  # Always returns list
for tool in tools:
    # Process each tool
```

**Benefits:**
- Multiple connection points in UI
- Automatic aggregation of inputs
- Flexible workflow design
- Follows Griptape design patterns

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
def _update_option_choices(self, param_name: str, choices: list, default_value: str):
    """Update Options trait choices dynamically."""
    param = self.get_parameter_by_name(param_name)
    if param and param.traits:
        for trait in param.traits:
            if hasattr(trait, 'choices'):
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

class BaseIterativeStartNode(StartLoopNode):
    """Base class for all iterative start nodes (ForEach, ForLoop, etc.)."""
    
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)
        self._current_iteration_count = 0
        self._total_iterations = 0
        
        # Common parameters for all iterative nodes
        self.index_count = Parameter(
            name="index",
            tooltip="Current index of the iteration",
            type=ParameterTypeBuiltin.INT.value,
            allowed_modes={ParameterMode.PROPERTY, ParameterMode.OUTPUT},
            settable=False,
            default_value=0,
        )
    
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
        "secrets_to_register": [
          "MY_SERVICE_API_KEY",
          "MY_OTHER_API_KEY"
        ]
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
- **categories**: Group nodes in UI with colors and icons
- **nodes**: List node classes, file paths, and metadata
- **workflows**: Template workflow files

**Important:** The `secrets_to_register` array tells the system which secrets your library needs. Users will be prompted to configure these secrets through the UI or environment variables.

Use flat directory structures. The engine automatically registers and loads libraries.

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
    StartLoopNode, EndLoopNode
)
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
    dict_to_image_url_artifact, load_pil_from_url
)
from griptape_nodes_library.utils.file_utils import generate_filename
```

### Advanced Parameter Types

- **ControlParameterInput/Output**: For execution flow control
- **ParameterGroup**: For organizing related parameters with collapsible UI
- **ParameterMessage**: For status updates and external links
- **ParameterList**: For accepting multiple inputs of the same type

### Enumerations

- **NodeResolutionState**: UNRESOLVED, RESOLVING, RESOLVED
- **ParameterMode**: INPUT, OUTPUT, PROPERTY
- **ParameterTypeBuiltin**: STR("str"), BOOL("bool"), INT("int"), FLOAT("float"), ANY("any"), NONE("none"), ALL("all")

### Advanced Node Types

- **BaseNode**: Most basic node type for custom implementations
- **DataNode**: For data processing without execution flow
- **ControlNode**: For nodes that manage execution flow
- **SuccessFailureNode**: For operations that can succeed or fail
- **StartLoopNode/EndLoopNode**: For iterative operations
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

---

This guide represents the current best practices for Griptape node development, incorporating both foundational concepts and modern patterns demonstrated in production nodes. Use these patterns to create robust, user-friendly, and maintainable nodes that integrate seamlessly with the Griptape ecosystem.
