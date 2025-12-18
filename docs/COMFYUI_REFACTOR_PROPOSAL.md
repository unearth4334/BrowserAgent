# ComfyUI Browser Agent Refactoring Proposal

**Date**: December 18, 2025  
**Version**: 1.0  
**Status**: Proposal

---

## Executive Summary

This proposal outlines a comprehensive refactoring plan to transform the current ComfyUI browser automation scripts from standalone examples into a modular, extensible library. The refactoring will establish clear separation between:

1. **Base Browser Agent** - Low-level browser control primitives
2. **ComfyUI Integration Layer** - Domain-specific ComfyUI operations
3. **CLI & API Interface** - User-facing tools and programmatic access

---

## Current State Analysis

### Existing Scripts

Located in `examples/comfyui/`:

| Script | Purpose | Status |
|--------|---------|--------|
| `queue_workflow_ui_click.py` | ✅ **PRIMARY** - UI-native queuing via button click | Production-ready, full compatibility |
| `queue_workflow_simple.py` | HTTP API queuing | Superseded, faster but limited compatibility |
| `queue_hybrid.py` | Browser load + HTTP queue | Experimental, intermediate approach |
| `queue_comfyui_workflow_direct.py` | JavaScript injection method | Development checkpoint |
| `queue_with_screenshots.py` | UI-click with debug screenshots | Debugging tool |
| `debug_workflow_with_screenshots.py` | Extended debugging | Development tool |
| `queue_simple.py` | Pure HTTP API | Early prototype |

### Problems with Current Structure

1. **Code Duplication**: Each script repeats browser setup, workflow loading, error handling
2. **No Reusability**: Cannot compose operations (e.g., load workflow + modify parameters + queue)
3. **Hard to Test**: Business logic mixed with infrastructure code
4. **Limited Extensibility**: Adding features requires modifying multiple scripts
5. **No Version Management**: Changes risk breaking existing integrations
6. **Documentation Scattered**: Each script documents similar concepts differently

### Success: `queue_workflow_ui_click.py`

This script represents the "golden path" because:
- ✅ Full metadata preservation (UI format → localStorage → ComfyUI load)
- ✅ Compatible with all custom nodes (e.g., WidgetToString)
- ✅ Reliable workflow execution
- ✅ Successfully deployed in production (cloud instance integration)

---

## Proposed Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────────┐
│                   User Interfaces                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  CLI Tool    │  │  Python API  │  │  REST API    │  │
│  │ (comfyui-*) │  │  (library)   │  │  (FastAPI)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              ComfyUI Integration Layer                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  High-Level Operations                             │ │
│  │  • WorkflowManager   • QueueManager                │ │
│  │  • ParameterSetter   • StatusMonitor              │ │
│  │  • WorkflowConverter • FileUploader               │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ComfyUI-Specific Actions                          │ │
│  │  • LoadWorkflowAction   • QueuePromptAction       │ │
│  │  • SetParameterAction   • CheckQueueAction        │ │
│  │  • ClickQueueButton     • GetPromptIDAction       │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│           Base Browser Agent (Existing)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Browser Primitives                                │ │
│  │  • BrowserServer      • BrowserClient              │ │
│  │  • Navigate, Click    • Type, EvalJS               │ │
│  │  • WaitForSelector    • Screenshot                │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### Directory Structure

```
browser_agent/
├── src/
│   └── browser_agent/
│       ├── browser/          # (existing) Base browser primitives
│       ├── server/           # (existing) Browser server/client
│       ├── agent/            # (existing) Agent core
│       └── comfyui/          # NEW: ComfyUI integration
│           ├── __init__.py
│           ├── actions/
│           │   ├── __init__.py
│           │   ├── workflow.py      # LoadWorkflow, QueueWorkflow actions
│           │   ├── parameters.py    # SetParameter, GetParameter actions
│           │   ├── queue.py         # CheckQueue, GetPromptID actions
│           │   └── files.py         # UploadImage, GetOutput actions
│           ├── managers/
│           │   ├── __init__.py
│           │   ├── workflow_manager.py    # High-level workflow operations
│           │   ├── queue_manager.py       # Queue management & monitoring
│           │   └── parameter_manager.py   # Parameter handling & validation
│           ├── converters/
│           │   ├── __init__.py
│           │   ├── ui_to_api.py     # UI format → API format conversion
│           │   └── validator.py     # Workflow validation
│           ├── cli.py        # ComfyUI-specific CLI commands
│           ├── config.py     # ComfyUI configuration & defaults
│           └── exceptions.py # ComfyUI-specific exceptions
│
├── examples/
│   ├── comfyui/
│   │   ├── README.md                    # Overview & migration guide
│   │   ├── legacy/                      # Archive old scripts
│   │   │   ├── queue_workflow_simple.py
│   │   │   ├── queue_hybrid.py
│   │   │   └── ...
│   │   ├── basic_queue.py               # Simple example using new API
│   │   ├── advanced_queue.py            # Complex example with parameters
│   │   ├── batch_processing.py          # Batch workflow execution
│   │   └── monitoring.py                # Status monitoring example
│   └── vast_api/           # (existing)
│
├── tests/
│   └── comfyui/            # NEW: ComfyUI-specific tests
│       ├── test_workflow_manager.py
│       ├── test_queue_manager.py
│       ├── test_actions.py
│       └── fixtures/
│           ├── sample_workflow.json
│           └── mock_comfyui.py
│
└── docs/
    ├── comfyui/            # NEW: Comprehensive ComfyUI docs
    │   ├── API.md                     # API reference
    │   ├── QUICKSTART.md              # Getting started guide
    │   ├── ACTIONS.md                 # Action catalog
    │   ├── WORKFLOWS.md               # Workflow management guide
    │   └── EXAMPLES.md                # Example gallery
    └── COMFYUI_REFACTOR_PROPOSAL.md   # This document
```

---

## Core Components

### 1. ComfyUI Actions (`comfyui/actions/`)

**Purpose**: Atomic, reusable operations specific to ComfyUI.

#### `workflow.py`

```python
@dataclass
class LoadWorkflowAction:
    """Load workflow from file or dict into ComfyUI."""
    workflow_source: Path | dict
    method: Literal["ui_native", "api", "hybrid"] = "ui_native"
    
@dataclass
class QueueWorkflowAction:
    """Queue the loaded workflow for execution."""
    method: Literal["ui_click", "http_api"] = "ui_click"
    
@dataclass  
class GetPromptIDAction:
    """Extract prompt ID after queuing."""
    timeout: float = 10.0
```

#### `parameters.py`

```python
@dataclass
class SetNodeParameterAction:
    """Set parameter value for a specific node."""
    node_id: str
    field_name: str
    value: Any
    
@dataclass
class BatchParameterAction:
    """Set multiple parameters at once."""
    parameters: Dict[str, Dict[str, Any]]  # node_id -> field -> value
```

#### `queue.py`

```python
@dataclass
class CheckQueueStatusAction:
    """Check if workflow is pending/running/completed."""
    prompt_id: str
    
@dataclass
class GetQueueLengthAction:
    """Get number of pending workflows."""
    pass
```

### 2. ComfyUI Managers (`comfyui/managers/`)

**Purpose**: High-level orchestration of actions.

#### `workflow_manager.py`

```python
class WorkflowManager:
    """High-level workflow operations."""
    
    def __init__(self, browser_client: BrowserClient, comfyui_url: str):
        self.client = browser_client
        self.url = comfyui_url
        self._current_workflow = None
        
    def load(self, workflow_path: Path, method: str = "ui_native") -> bool:
        """Load workflow into ComfyUI."""
        
    def set_parameters(self, params: Dict[str, Dict[str, Any]]) -> bool:
        """Set multiple workflow parameters."""
        
    def queue(self, method: str = "ui_click") -> str | None:
        """Queue workflow, return prompt ID."""
        
    def load_and_queue(self, workflow_path: Path, 
                       params: Dict | None = None) -> str | None:
        """Convenience: load, set params, queue in one call."""
```

#### `queue_manager.py`

```python
class QueueManager:
    """Manage workflow queue and execution status."""
    
    def __init__(self, browser_client: BrowserClient, comfyui_url: str):
        self.client = browser_client
        self.url = comfyui_url
        
    def get_status(self, prompt_id: str) -> QueueStatus:
        """Check workflow execution status."""
        
    def wait_for_completion(self, prompt_id: str, 
                           timeout: float = 600) -> bool:
        """Wait for workflow to complete."""
        
    def get_queue_length(self) -> Tuple[int, int]:
        """Return (pending, running) counts."""
```

### 3. CLI Interface (`comfyui/cli.py`)

**Purpose**: User-friendly command-line tools.

```python
import typer

app = typer.Typer(name="comfyui", help="ComfyUI workflow automation")

@app.command()
def queue(
    workflow: Path = typer.Argument(..., help="Workflow JSON file"),
    comfyui_url: str = typer.Option("http://localhost:18188"),
    method: str = typer.Option("ui-click", help="ui-click or http-api"),
    wait: bool = typer.Option(False, help="Wait for completion"),
    params: str = typer.Option(None, help="JSON params: {node_id: {field: value}}"),
):
    """Queue a ComfyUI workflow for execution."""
    
@app.command()
def status(
    prompt_id: str = typer.Argument(...),
    comfyui_url: str = typer.Option("http://localhost:18188"),
):
    """Check workflow execution status."""

@app.command()
def batch(
    workflow: Path = typer.Argument(...),
    count: int = typer.Option(1, help="Number of executions"),
    comfyui_url: str = typer.Option("http://localhost:18188"),
):
    """Queue multiple executions of a workflow."""
```

### 4. Python API

**Purpose**: Library interface for programmatic use.

```python
from browser_agent.comfyui import ComfyUIClient

# Simple usage
client = ComfyUIClient("http://localhost:18188")
prompt_id = client.queue_workflow("workflow.json")
client.wait_for_completion(prompt_id)

# Advanced usage
client = ComfyUIClient("http://localhost:18188")
client.connect()

# Load workflow
client.workflow.load("workflow.json")

# Set parameters
client.parameters.set("node_123", "seed", 42)
client.parameters.set("node_456", "steps", 20)

# Queue
prompt_id = client.queue.submit(method="ui_click")

# Monitor
status = client.queue.get_status(prompt_id)
print(f"Status: {status.state} - {status.message}")

# Cleanup
client.disconnect()
```

---

## Migration Strategy

### Phase 1: Foundation (Week 1)

**Goals**: 
- Create directory structure
- Implement core actions
- Establish testing framework

**Tasks**:
1. Create `src/browser_agent/comfyui/` directory structure
2. Implement basic actions in `actions/workflow.py`:
   - `LoadWorkflowAction` (UI-native method from queue_workflow_ui_click.py)
   - `QueueWorkflowAction` (UI-click method)
   - `GetPromptIDAction`
3. Create test fixtures and mocks
4. Write unit tests for actions
5. Move old scripts to `examples/comfyui/legacy/`

**Deliverables**:
- Working action framework
- 80%+ test coverage for actions
- Legacy scripts archived

### Phase 2: Managers (Week 2)

**Goals**:
- Implement high-level managers
- Establish clean API patterns

**Tasks**:
1. Implement `WorkflowManager`:
   - Extract logic from queue_workflow_ui_click.py
   - Add error handling and retry logic
   - Support both UI-native and HTTP methods
2. Implement `QueueManager`:
   - Status checking from CLOUD_DEPLOYMENT_GUIDE.md patterns
   - Wait-for-completion with timeout
   - Queue length monitoring
3. Create integration tests with mock browser
4. Write manager documentation

**Deliverables**:
- `WorkflowManager` class (fully tested)
- `QueueManager` class (fully tested)
- Integration test suite
- API documentation

### Phase 3: CLI & Examples (Week 3)

**Goals**:
- User-facing CLI tools
- Example scripts showing best practices

**Tasks**:
1. Implement CLI commands in `comfyui/cli.py`
2. Integrate with main `browser-agent` CLI
3. Create new example scripts:
   - `examples/comfyui/basic_queue.py` - Simplest case
   - `examples/comfyui/advanced_queue.py` - With parameters
   - `examples/comfyui/batch_processing.py` - Multiple workflows
4. Update documentation:
   - Quick start guide
   - API reference
   - Migration guide for existing users

**Deliverables**:
- Working CLI commands
- 3+ example scripts
- Comprehensive documentation

### Phase 4: Advanced Features (Week 4)

**Goals**:
- Add convenience features
- Optimize performance

**Tasks**:
1. Implement parameter management:
   - Type validation
   - Parameter templates
   - Batch parameter setting
2. Add workflow converters:
   - UI format ↔ API format
   - Workflow validation
3. Implement file operations:
   - Image upload actions
   - Output file retrieval
4. Performance optimizations:
   - Connection pooling
   - Caching
5. Create REST API wrapper (FastAPI)

**Deliverables**:
- Complete feature set
- REST API server
- Performance benchmarks
- Final documentation

---

## API Design Examples

### Example 1: Simple Queue (Basic Use Case)

```python
from browser_agent.comfyui import ComfyUIClient

# One-liner for simple cases
client = ComfyUIClient("http://localhost:18188")
prompt_id = client.queue_workflow("my_workflow.json")
print(f"Queued: {prompt_id}")
```

### Example 2: Queue with Parameters

```python
from browser_agent.comfyui import ComfyUIClient

client = ComfyUIClient("http://localhost:18188")
client.connect()

# Load workflow
client.workflow.load("img2video.json")

# Set parameters
client.workflow.set_parameter("seed_node", "seed", 12345)
client.workflow.set_parameter("sampler_node", "steps", 30)
client.workflow.set_parameter("video_node", "fps", 24)

# Queue
prompt_id = client.workflow.queue()

# Wait and monitor
if client.queue.wait_for_completion(prompt_id, timeout=600):
    print("✅ Workflow completed!")
else:
    print("❌ Workflow failed or timed out")

client.disconnect()
```

### Example 3: Batch Processing

```python
from browser_agent.comfyui import ComfyUIClient

client = ComfyUIClient("http://localhost:18188")
client.connect()

# Queue multiple variations
seeds = [100, 200, 300, 400, 500]
prompt_ids = []

for seed in seeds:
    client.workflow.load("generate.json")
    client.workflow.set_parameter("seed_node", "seed", seed)
    prompt_id = client.workflow.queue()
    prompt_ids.append(prompt_id)
    print(f"Queued seed {seed}: {prompt_id}")

# Monitor all
for prompt_id in prompt_ids:
    status = client.queue.get_status(prompt_id)
    print(f"{prompt_id}: {status.state}")

client.disconnect()
```

### Example 4: Remote Execution (Cloud Integration)

```python
from browser_agent.comfyui import RemoteComfyUIClient

# Connect to remote instance
client = RemoteComfyUIClient(
    hostname="172.219.157.164",
    port=19361,
    username="root",
    key_filename="~/.ssh/id_rsa",
    comfyui_url="http://localhost:18188"
)

client.connect()

# Upload workflow
remote_path = client.upload_workflow("local_workflow.json")

# Queue on remote
prompt_id = client.queue_workflow(remote_path, method="ui_click")

# Check status
status = client.check_status(prompt_id)

client.disconnect()
```

### Example 5: CLI Usage

```bash
# Basic queue
comfyui-queue workflow.json

# With parameters
comfyui-queue workflow.json \
    --params '{"node_1": {"seed": 42, "steps": 20}}'

# Queue and wait
comfyui-queue workflow.json --wait

# Check status
comfyui-status a1b2c3d4-5678-90ab-cdef-1234567890ab

# Batch execution
comfyui-batch workflow.json --count 10

# Remote execution
comfyui-queue workflow.json \
    --remote 172.219.157.164:19361 \
    --user root \
    --key ~/.ssh/id_rsa
```

---

## Benefits

### For Users

1. **Simpler Integration**: Import library, call functions
2. **Better Documentation**: Centralized, comprehensive guides
3. **More Features**: Parameter management, status monitoring, batch processing
4. **Stable API**: Semantic versioning, backward compatibility
5. **Better Error Messages**: Clear, actionable error reporting

### For Developers

1. **Testable Code**: Actions and managers are unit-testable
2. **Extensible**: Easy to add new actions/features
3. **Maintainable**: Clear separation of concerns
4. **Reusable**: Compose actions into complex workflows
5. **Type-Safe**: Full type hints throughout

### For the Project

1. **Professional Structure**: Industry-standard architecture
2. **Easier Contributions**: Clear patterns to follow
3. **Better CI/CD**: Modular tests, selective testing
4. **Documentation as Code**: API docs generated from code
5. **Growth Ready**: Foundation for future features

---

## Backward Compatibility

### Deprecated Scripts

Old scripts will be moved to `examples/comfyui/legacy/` with deprecation notices:

```python
# examples/comfyui/legacy/queue_workflow_ui_click.py

import warnings

warnings.warn(
    "This script is deprecated. Use the new API:\n"
    "  from browser_agent.comfyui import ComfyUIClient\n"
    "  client = ComfyUIClient('http://localhost:18188')\n"
    "  client.queue_workflow('workflow.json')\n"
    "See docs/comfyui/MIGRATION.md for details.",
    DeprecationWarning,
    stacklevel=2
)

# ... original code still works ...
```

### Migration Guide

Create `docs/comfyui/MIGRATION.md` mapping old patterns to new:

| Old Pattern | New Pattern |
|-------------|-------------|
| `queue_workflow_ui_click.py --workflow-path X` | `comfyui-queue X` or `client.queue_workflow(X)` |
| Manual browser setup + client | `ComfyUIClient(url)` |
| Custom workflow loading | `client.workflow.load(path)` |
| HTTP API queuing | `client.queue(method="http_api")` |

---

## Testing Strategy

### Unit Tests

- Test each action in isolation
- Mock browser client responses
- Validate parameter handling
- Test error conditions

### Integration Tests

- Test manager orchestration
- Use mock ComfyUI server
- Test end-to-end workflows
- Validate state transitions

### System Tests

- Test against real ComfyUI instance
- Validate actual workflow execution
- Performance benchmarks
- Compatibility testing

### Test Coverage Goals

- Actions: 90%+
- Managers: 85%+
- CLI: 80%+
- Overall: 85%+

---

## Documentation Plan

### User Documentation

1. **Quick Start** (`docs/comfyui/QUICKSTART.md`)
   - Installation
   - First workflow queue
   - Common patterns

2. **API Reference** (`docs/comfyui/API.md`)
   - All classes, methods, parameters
   - Auto-generated from docstrings

3. **Action Catalog** (`docs/comfyui/ACTIONS.md`)
   - Complete list of actions
   - Parameters, return values
   - Usage examples

4. **Workflow Guide** (`docs/comfyui/WORKFLOWS.md`)
   - Workflow formats (UI vs API)
   - Parameter management
   - Best practices

5. **Examples Gallery** (`docs/comfyui/EXAMPLES.md`)
   - Copy-paste examples
   - Common use cases
   - Advanced patterns

### Developer Documentation

1. **Architecture** (this document)
2. **Contributing Guide**
3. **Testing Guide**
4. **Release Process**

---

## Success Metrics

### Quantitative

- ✅ 85%+ test coverage
- ✅ <5 GitHub issues per month
- ✅ Documentation for 100% of public API
- ✅ Zero breaking changes in minor versions
- ✅ <100ms overhead vs direct browser control

### Qualitative

- ✅ Users can queue workflows in <10 lines of code
- ✅ New features can be added without modifying core
- ✅ Contributors can understand architecture in <30 minutes
- ✅ Integration with existing projects requires <1 hour

---

## Risks & Mitigations

### Risk: Breaking Existing Integrations

**Mitigation**: 
- Keep old scripts working (with deprecation warnings)
- Provide migration guide
- 6-month deprecation period before removal

### Risk: Performance Regression

**Mitigation**:
- Benchmark before/after
- Profile hot paths
- Optimize if >10% slower

### Risk: Increased Complexity

**Mitigation**:
- Maintain simple API for common cases
- Hide complexity in optional advanced features
- Provide examples for all levels

### Risk: Maintenance Burden

**Mitigation**:
- Comprehensive test suite
- CI/CD automation
- Clear contribution guidelines

---

## Timeline

| Phase | Duration | End Date | Deliverable |
|-------|----------|----------|-------------|
| Phase 1: Foundation | 1 week | Week 1 | Actions, tests, legacy archived |
| Phase 2: Managers | 1 week | Week 2 | WorkflowManager, QueueManager |
| Phase 3: CLI & Examples | 1 week | Week 3 | CLI tools, examples, docs |
| Phase 4: Advanced | 1 week | Week 4 | Full feature set, REST API |
| **Total** | **4 weeks** | **Month 1** | **Production-ready library** |

---

## Next Steps

1. **Review & Approve**: Stakeholder review of this proposal
2. **Create Issues**: Break down into GitHub issues/tasks
3. **Setup Branch**: Create `refactor/comfyui-integration` branch
4. **Phase 1 Kickoff**: Begin implementation
5. **Weekly Check-ins**: Review progress, adjust as needed

---

## Appendix A: Key Files to Extract Logic From

| Current File | Logic to Extract | Target Location |
|--------------|------------------|-----------------|
| `queue_workflow_ui_click.py` | Workflow loading via localStorage chunks | `WorkflowManager.load()` |
| `queue_workflow_ui_click.py` | UI button click queuing | `QueueWorkflowAction` |
| `queue_workflow_ui_click.py` | Prompt ID extraction | `GetPromptIDAction` |
| `queue_hybrid.py` | Workflow conversion | `converters/ui_to_api.py` |
| `queue_simple.py` | HTTP API queuing | `QueueWorkflowAction` (http method) |
| `CLOUD_DEPLOYMENT_GUIDE.md` | Remote execution patterns | `RemoteComfyUIClient` |
| `CLOUD_DEPLOYMENT_GUIDE.md` | Status checking | `QueueManager.get_status()` |

---

## Appendix B: Import Paths

### Current (Examples)

```python
# examples/comfyui/queue_workflow_ui_click.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
```

### New (Library)

```python
# User code
from browser_agent.comfyui import ComfyUIClient
from browser_agent.comfyui.actions import LoadWorkflowAction, QueueWorkflowAction
from browser_agent.comfyui.managers import WorkflowManager, QueueManager
```

---

## Appendix C: Configuration

### Default Configuration (`comfyui/config.py`)

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class ComfyUIConfig:
    """ComfyUI client configuration."""
    
    # Connection
    url: str = "http://localhost:18188"
    timeout: float = 30.0
    
    # Workflow Loading
    default_load_method: Literal["ui_native", "api", "hybrid"] = "ui_native"
    chunk_size: int = 50000  # For localStorage chunking
    
    # Queuing
    default_queue_method: Literal["ui_click", "http_api"] = "ui_click"
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Monitoring
    check_interval: float = 2.0
    max_wait_time: float = 600.0
    
    # Browser
    headless: bool = True
    browser_port: int = 9999
    
    @classmethod
    def from_env(cls) -> "ComfyUIConfig":
        """Load configuration from environment variables."""
        import os
        return cls(
            url=os.getenv("COMFYUI_URL", cls.url),
            timeout=float(os.getenv("COMFYUI_TIMEOUT", cls.timeout)),
            # ... etc
        )
```

---

**End of Proposal**

This refactoring will transform the ComfyUI browser agent from a collection of scripts into a professional, maintainable, and extensible library while preserving all existing functionality and maintaining backward compatibility.
