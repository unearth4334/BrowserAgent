#!/usr/bin/env python3
"""
Complete workflow opening with full error/warning tracking.
Opens Workflows panel, finds and opens workflow, reports any issues.
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from src.browser_agent.server.browser_client import BrowserClient

client = BrowserClient()

print("=" * 70)
print("OPENING WORKFLOW WITH ERROR TRACKING")
print("=" * 70)

# Step 1: Open Workflows panel
print("\n📂 Step 1: Opening Workflows panel...")
result = client.eval_js("""
(() => {
    const btn = document.querySelector('button[aria-label="Workflows (w)"]');
    if (!btn) return {error: 'Workflows button not found'};
    btn.click();
    return {success: true};
})()
""")

if result.get('status') != 'success' or result.get('result', {}).get('error'):
    print(f"❌ Error: {result.get('result', {}).get('error', 'Unknown error')}")
    sys.exit(1)

print("✓ Workflows panel opened")
time.sleep(2)

# Step 2: Expand UmeAiRT folder
print("\n📁 Step 2: Expanding UmeAiRT folder...")
result = client.eval_js("""
(() => {
    const panel = document.querySelector('.side-bar-panel');
    if (!panel) return {error: 'Panel not visible'};
    
    const browseTree = panel.querySelector('.comfyui-workflows-browse .p-tree');
    if (!browseTree) return {error: 'Browse tree not found'};
    
    const nodes = browseTree.querySelectorAll('.p-tree-root-children > .p-tree-node');
    let umeNode = null;
    for (const node of nodes) {
        const label = node.querySelector('.p-tree-node-label');
        if (label && label.textContent.includes('UmeAiRT')) {
            umeNode = node;
            break;
        }
    }
    
    if (!umeNode) return {error: 'UmeAiRT folder not found'};
    
    const isExpanded = umeNode.getAttribute('aria-expanded') === 'true';
    if (!isExpanded) {
        const toggleBtn = umeNode.querySelector('.p-tree-node-toggle-button');
        if (toggleBtn) toggleBtn.click();
    }
    
    return {success: true, wasExpanded: isExpanded};
})()
""")

if result.get('status') != 'success' or result.get('result', {}).get('error'):
    print(f"❌ Error: {result.get('result', {}).get('error', 'Unknown error')}")
    sys.exit(1)

print(f"✓ Folder expanded (was already expanded: {result.get('result', {}).get('wasExpanded')})")
time.sleep(2)

# Step 3: Open workflow
print("\n🎯 Step 3: Opening WAN2.2_IMG_to_VIDEO_Base.json...")
result = client.eval_js("""
(() => {
    const panel = document.querySelector('.side-bar-panel');
    if (!panel) return {error: 'Panel not visible'};
    
    const browseTree = panel.querySelector('.comfyui-workflows-browse .p-tree');
    if (!browseTree) return {error: 'Browse tree not found'};
    
    const allNodes = Array.from(browseTree.querySelectorAll('.p-tree-node'));
    
    let workflowNode = null;
    for (const node of allNodes) {
        const label = node.querySelector('.p-tree-node-label');
        if (label && label.textContent.includes('WAN2.2_IMG_to_VIDEO_Base.json')) {
            workflowNode = node;
            break;
        }
    }
    
    if (!workflowNode) return {error: 'Workflow not found'};
    
    const nodeContent = workflowNode.querySelector('.p-tree-node-content');
    if (!nodeContent) return {error: 'Node content not clickable'};
    
    nodeContent.click();
    
    return {
        success: true,
        workflowName: workflowNode.querySelector('.p-tree-node-label').textContent.trim()
    };
})()
""")

if result.get('status') != 'success' or result.get('result', {}).get('error'):
    print(f"❌ Error: {result.get('result', {}).get('error', 'Unknown error')}")
    sys.exit(1)

print(f"✓ Clicked workflow: {result.get('result', {}).get('workflowName')}")
time.sleep(3)

# Step 4: Verify workflow loaded
print("\n📊 Step 4: Verifying workflow loaded...")
info_result = client.info()
if info_result.get('status') == 'success':
    print(f"✓ Page title: {info_result.get('title', 'Unknown')}")

graph_result = client.eval_js("""
(() => {
    if (window.app && window.app.graph && window.app.graph._nodes) {
        return {
            success: true,
            nodeCount: window.app.graph._nodes.length,
            graphTitle: window.app.graph.title || 'Untitled'
        };
    }
    return {success: false};
})()
""")

if graph_result.get('status') == 'success' and graph_result.get('result', {}).get('success'):
    print(f"✓ Workflow loaded: {graph_result['result']['nodeCount']} nodes")
else:
    print("⚠️  Workflow state unclear")

# Step 5: Check for warnings/errors/dialogs
print("\n🔍 Step 5: Checking for warnings/dialogs...")
dialog_check = client.eval_js("""
(() => {
    const results = {
        dialogs: [],
        warnings: [],
        missingModels: []
    };
    
    // Check for dialogs
    const dialogs = document.querySelectorAll('.p-dialog[role="dialog"]');
    dialogs.forEach(dialog => {
        const isVisible = dialog.offsetParent !== null;
        if (isVisible) {
            const header = dialog.querySelector('.p-dialog-header-title, .p-dialog-title, h3');
            const content = dialog.querySelector('.p-dialog-content');
            
            const dialogContent = content ? content.textContent.trim() : '';
            
            const dialogInfo = {
                title: header ? header.textContent.trim() : 'No title',
                content: dialogContent,
                className: dialog.className
            };
            
            // Check if this is a "Missing Models" dialog
            if (dialogContent.includes('Missing Models') || dialogContent.includes('models were not found')) {
                // Extract model file paths
                const lines = dialogContent.split('\\n').map(l => l.trim()).filter(l => l);
                
                // Look for lines that contain model paths
                const modelPaths = lines.filter(line => 
                    line.includes('/') && 
                    (line.includes('.safetensors') || line.includes('.ckpt') || line.includes('.pt') || line.includes('.pth'))
                );
                
                results.missingModels.push({
                    type: 'Missing Models',
                    models: modelPaths,
                    fullText: dialogContent
                });
            }
            
            results.dialogs.push(dialogInfo);
        }
    });
    
    // Check for toast notifications
    const toasts = document.querySelectorAll('.p-toast-message');
    toasts.forEach(toast => {
        const isVisible = toast.offsetParent !== null;
        if (isVisible) {
            results.warnings.push({
                content: toast.textContent.trim(),
                severity: toast.className.includes('error') ? 'error' : 
                         toast.className.includes('warn') ? 'warning' : 'info'
            });
        }
    });
    
    return {
        hasIssues: results.dialogs.length > 0 || results.warnings.length > 0,
        dialogCount: results.dialogs.length,
        warningCount: results.warnings.length,
        hasMissingModels: results.missingModels.length > 0,
        results: results
    };
})()
""")

if dialog_check.get('status') == 'success':
    dialog_data = dialog_check.get('result', {})
    
    if dialog_data.get('hasIssues'):
        print(f"\n⚠️  WARNING: Found {dialog_data.get('dialogCount')} dialog(s) and {dialog_data.get('warningCount')} warning(s)\n")
        
        # Report missing models (most critical)
        if dialog_data.get('hasMissingModels'):
            print("   ❌ MISSING MODELS DETECTED:")
            for missing in dialog_data['results']['missingModels']:
                print(f"      Type: {missing['type']}")
                if missing.get('models') and len(missing['models']) > 0:
                    print(f"      Missing files:")
                    for model in missing['models']:
                        print(f"        - {model}")
                else:
                    # Extract model info from text
                    text = missing['fullText']
                    if 'vae' in text.lower():
                        print(f"      Category: VAE models")
                    if 'wan_2.1_vae.safetensors' in text:
                        print(f"        - vae/wan_2.1_vae.safetensors (242.06 MB)")
        
        # Report other dialogs
        other_dialogs = [d for d in dialog_data['results']['dialogs'] 
                        if 'Missing Models' not in d.get('content', '')]
        for dialog in other_dialogs:
            title = dialog.get('title', 'Untitled')
            if title and title != 'No title':
                print(f"\n   📋 Dialog: {title}")
                if len(dialog['content']) > 0:
                    content_preview = dialog['content'][:200]
                    print(f"      Content: {content_preview}...")
        
        # Report toast warnings
        for warning in dialog_data['results']['warnings']:
            print(f"\n   ⚠️  {warning['severity'].upper()}: {warning['content']}")
    else:
        print("   ✓ No warnings or dialogs detected")
else:
    print("   ⚠️  Could not check for dialogs")

print("\n" + "=" * 70)
print("WORKFLOW OPENING COMPLETE")
print("=" * 70)
