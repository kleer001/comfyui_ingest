# ComfyUI REST API Reference

Base URL: `http://127.0.0.1:8188`

## Core Endpoints

### POST /prompt
Queue a workflow for execution.

**Request:**
```json
{
  "prompt": { /* workflow nodes keyed by node ID */ },
  "client_id": "my-client"
}
```

**Response:**
```json
{
  "prompt_id": "abc123-uuid",
  "number": 5,
  "node_errors": {}
}
```

**Workflow format for API** (different from saved .json):
```json
{
  "1": {
    "class_type": "VHS_LoadImagesPath",
    "inputs": {
      "directory": "source/frames",
      "skip_first_images": 0
    }
  },
  "2": {
    "class_type": "SaveImage",
    "inputs": {
      "images": ["1", 0],
      "filename_prefix": "output"
    }
  }
}
```

Links are expressed as `["node_id", output_slot_index]`.

### GET /history/{prompt_id}
Retrieve execution results.

**Response:**
```json
{
  "abc123-uuid": {
    "prompt": [...],
    "outputs": {
      "5": {
        "images": [
          {"filename": "output_00001.png", "subfolder": "", "type": "output"}
        ]
      }
    },
    "status": {
      "completed": true,
      "messages": []
    }
  }
}
```

### GET /queue
Current queue status.

**Response:**
```json
{
  "queue_running": [["prompt_id", 0, {...}, {...}]],
  "queue_pending": []
}
```

### POST /interrupt
Stop currently executing workflow.

### POST /free
Unload models from VRAM, run garbage collection.

**Request:**
```json
{"unload_models": true, "free_memory": true}
```

### GET /view
Retrieve generated images.

**Query params:**
- `filename` - Image filename
- `subfolder` - Subdirectory (optional)
- `type` - `output`, `input`, or `temp`

**Example:** `/view?filename=depth_00001.png&type=output`

### GET /object_info
List all available node types with their inputs/outputs.

**Response (partial):**
```json
{
  "SaveImage": {
    "input": {
      "required": {
        "images": ["IMAGE"]
      },
      "optional": {
        "filename_prefix": ["STRING", {"default": "ComfyUI"}]
      }
    },
    "output": [],
    "output_name": [],
    "category": "image"
  }
}
```

### GET /object_info/{node_type}
Get info for a specific node type.

## WebSocket /ws

Real-time execution updates.

**Connect:** `ws://127.0.0.1:8188/ws?clientId=my-client`

**Messages received:**
```json
{"type": "status", "data": {"status": {"exec_info": {"queue_remaining": 1}}}}
{"type": "execution_start", "data": {"prompt_id": "abc123"}}
{"type": "executing", "data": {"node": "3", "prompt_id": "abc123"}}
{"type": "executed", "data": {"node": "3", "output": {...}}}
{"type": "execution_complete", "data": {"prompt_id": "abc123"}}
```

## Python Client Example

```python
import json
import urllib.request

def queue_prompt(workflow: dict, server: str = "127.0.0.1:8188") -> str:
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"http://{server}/prompt", data=data)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())["prompt_id"]

def get_history(prompt_id: str, server: str = "127.0.0.1:8188") -> dict:
    with urllib.request.urlopen(f"http://{server}/history/{prompt_id}") as response:
        return json.loads(response.read())
```

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Invalid workflow JSON |
| 500 | Execution error (check node_errors) |

Common errors in `node_errors`:
- `"required input is missing"` - Unconnected required input
- `"invalid type"` - Type mismatch on connection
- `"KeyError"` - Missing widget value or bad reference
