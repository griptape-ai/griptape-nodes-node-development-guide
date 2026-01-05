# Griptape Nodes — Node Development Guide

This repository contains the **canonical Node Development Guide** for building custom nodes and node libraries for
[`griptape-nodes`](https://github.com/griptape-ai/griptape-nodes).

## Start here

- **Main guide**: [`node-development-guide-v3.md`](./node-development-guide-v3.md)
- **Example**: [`example_control_node.py`](./example_control_node.py)

## Who this is for

- Developers who are **new to the Griptape Nodes ecosystem** and want the authoritative reference
- Contributors who need details on:
  - node base classes (`DataNode`, `ControlNode`, `StartNode`, `EndNode`, etc.)
  - parameters, traits, containers, and lifecycle callbacks
  - async patterns (`AsyncResult`)
  - practical UI/UX and error-handling guidance

## Related docs

The `griptape-nodes` repo also contains a shorter onboarding page intended as a “front door” for newcomers:
- `griptape-nodes/docs/how_to/developing_nodes.md`

## Contributing

Improvements and corrections are welcome.
When updating the guide, please verify the content against the current `griptape-nodes` codebase.
