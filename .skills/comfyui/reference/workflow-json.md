# ComfyUI Workflow JSON Structure

Two formats exist: **saved workflow** (from UI) and **API format** (for /prompt endpoint).

## Saved Workflow Format

Used in `workflow_templates/*.json` files.

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "revision": 1,
  "last_node_id": 7,
  "last_link_id": 5,
  "nodes": [...],
  "links": [...],
  "groups": [...],
  "config": {},
  "extra": {
    "ds": {"scale": 0.8, "offset": [0, 0]},
    "info": {
      "name": "Workflow Name",
      "author": "Author",
      "description": "Description"
    }
  },
  "version": 0.4
}
```

### Node Object

```json
{
  "id": 1,
  "type": "NodeClassName",
  "pos": [100, 200],
  "size": [320, 200],
  "flags": {},
  "order": 0,
  "mode": 0,
  "inputs": [
    {"name": "image", "type": "IMAGE", "link": 1}
  ],
  "outputs": [
    {"name": "IMAGE", "type": "IMAGE", "links": [2, 3], "slot_index": 0}
  ],
  "properties": {"Node name for S&R": "NodeClassName"},
  "widgets_values": ["value1", 123, true, null],
  "title": "Custom Display Title"
}
```

| Field | Description |
|-------|-------------|
| id | Unique node ID (integer) |
| type | Node class name |
| pos | [x, y] canvas position |
| size | [width, height] in pixels |
| mode | 0=normal, 2=muted, 4=bypassed |
| inputs | Array of input slots |
| outputs | Array of output slots |
| widgets_values | Array of widget values in order |
| title | Optional custom title |

### Link Array

```json
[link_id, from_node_id, from_slot_index, to_node_id, to_slot_index, "TYPE"]
```

Example:
```json
[1, 1, 0, 3, 1, "IMAGE"]
```
Means: Link #1 connects node 1's output slot 0 to node 3's input slot 1, carrying IMAGE type.

### Groups

Visual grouping for organization (no execution effect).

```json
{
  "title": "INPUT",
  "bounding": [80, 180, 380, 400],
  "color": "#3f789e"
}
```
Bounding: [x, y, width, height]

## API Format

Used when submitting to `/prompt` endpoint. Nodes keyed by ID string, links expressed inline.

```json
{
  "1": {
    "class_type": "VHS_LoadImagesPath",
    "inputs": {
      "directory": "source/frames",
      "skip_first_images": 0,
      "select_every_nth": 1
    }
  },
  "2": {
    "class_type": "VideoDepthAnythingProcess",
    "inputs": {
      "vda_model": ["3", 0],
      "images": ["1", 0],
      "max_resolution": 518
    }
  },
  "3": {
    "class_type": "LoadVideoDepthAnythingModel",
    "inputs": {
      "model_name": "video_depth_anything_vits.pth"
    }
  }
}
```

### Link Format in API

References another node's output:
```json
"input_name": ["node_id_string", output_slot_index]
```

### Converting Saved → API Format

1. Change node IDs from integers to strings
2. Replace `type` with `class_type`
3. Convert `widgets_values` array to named `inputs` object
4. Replace link references with `["node_id", slot]` format
5. Remove `pos`, `size`, `outputs`, `links`, `groups`, `extra`

## Common Type Strings

| Type | Description |
|------|-------------|
| IMAGE | Batch of images [B, H, W, C] |
| MASK | Mask tensor [B, H, W] |
| INT | Integer |
| FLOAT | Float |
| STRING | Text |
| VDAMODEL | Video Depth Anything model |
| SAM3_MODEL | SAM3 model reference |
| SAM3_VIDEO_STATE | SAM3 video state |
| SAM3_VIDEO_MASKS | SAM3 mask output |
| SAM3_POINTS_PROMPT | Point coordinates |
| DEPTHS | Depth tensor |

## Modifying Workflows Programmatically

Common modifications in Python:

```python
import json

def load_workflow(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def find_node_by_type(workflow: dict, node_type: str) -> dict | None:
    for node in workflow["nodes"]:
        if node["type"] == node_type:
            return node
    return None

def set_widget_value(node: dict, index: int, value):
    node["widgets_values"][index] = value

def set_input_path(workflow: dict, node_type: str, path: str):
    node = find_node_by_type(workflow, node_type)
    if node and node["type"] == "VHS_LoadImagesPath":
        node["widgets_values"][0] = path

def set_output_prefix(workflow: dict, prefix: str):
    for node in workflow["nodes"]:
        if node["type"] == "SaveImage":
            node["widgets_values"][0] = prefix
```

## Validation Checklist

- [ ] All link IDs unique
- [ ] All node IDs unique
- [ ] Link references exist (from_node, to_node)
- [ ] Slot indices within bounds
- [ ] Type strings match between connected slots
- [ ] widgets_values array length matches node requirements
- [ ] Required inputs all connected
