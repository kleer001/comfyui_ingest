/**
 * ComfyUI Workflow Auto-Loader Extension
 *
 * Automatically loads a workflow when ComfyUI starts.
 *
 * Usage:
 *   1. URL parameter: http://localhost:8188/?workflow=/path/to/workflow.json
 *   2. Default location: /input/auto_load_workflow.json
 *
 * The URL parameter takes precedence over the default location.
 * Paths can be absolute (/input/...) or relative to ComfyUI root.
 *
 * Installation:
 *   Copy this folder to: ComfyUI/web/extensions/comfyui_autoload/
 *
 * License: MIT
 * Repository: https://github.com/kleer001/shot-gopher
 */

import { app } from "../../scripts/app.js";

const EXTENSION_NAME = "comfyui.autoload";
const DEFAULT_WORKFLOW_PATH = "/input/auto_load_workflow.json";
const STARTUP_DELAY_MS = 1500;

function getWorkflowPathFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get("workflow");
}

async function fetchWorkflow(path) {
    const response = await fetch(path);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

async function loadWorkflowFromPath(path, source) {
    try {
        console.log(`[AutoLoad] Attempting to load workflow from ${source}: ${path}`);
        const workflow = await fetchWorkflow(path);
        await app.loadGraphData(workflow);
        console.log(`[AutoLoad] Workflow loaded successfully from ${source}`);
        return true;
    } catch (error) {
        console.log(`[AutoLoad] Could not load from ${source}: ${error.message}`);
        return false;
    }
}

app.registerExtension({
    name: EXTENSION_NAME,

    async setup() {
        await new Promise(resolve => setTimeout(resolve, STARTUP_DELAY_MS));

        const urlPath = getWorkflowPathFromURL();

        if (urlPath) {
            const loaded = await loadWorkflowFromPath(urlPath, "URL parameter");
            if (loaded) return;
        }

        await loadWorkflowFromPath(DEFAULT_WORKFLOW_PATH, "default location");
    }
});
