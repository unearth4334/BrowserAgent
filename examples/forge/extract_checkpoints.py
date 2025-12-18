#!/usr/bin/env python3
"""
Script to visit http://localhost:7860/ and extract all Checkpoint dropdown items.
"""
from browser_agent.config import Settings
from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, WaitForSelector, ExecuteJS
from pathlib import Path

def extract_checkpoint_dropdown():
    """Visit localhost:7860 and extract all checkpoint dropdown options."""
    
    # Initialize browser with visible UI
    settings = Settings.from_env()
    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=False,  # Show browser for debugging
    )
    
    try:
        # Start browser
        print("Starting browser...")
        controller.start()
        
        # Navigate to the URL
        print("Navigating to http://localhost:7860/...")
        controller.perform(Navigate("http://localhost:7860/"))
        
        # Wait for page to load (WebUI takes time)
        import time
        print("Waiting for page to fully load...")
        time.sleep(5)
        
        # JavaScript to extract all options from any kind of dropdown
        js_code = """
        (() => {
            let checkpointOptions = [];
            let dropdownInfo = {};
            
            // Strategy 1: Try regular select elements
            const selects = document.querySelectorAll('select');
            for (const select of selects) {
                const label = (select.id || select.name || select.className || '').toLowerCase();
                if (label.includes('checkpoint') || label.includes('ckpt') || label.includes('model')) {
                    if (select.options && select.options.length > 0) {
                        checkpointOptions = Array.from(select.options).map(opt => ({
                            value: opt.value,
                            text: opt.text.trim()
                        }));
                        dropdownInfo = {
                            id: select.id,
                            name: select.name,
                            className: select.className,
                            type: 'select'
                        };
                        return { dropdownInfo, options: checkpointOptions, count: checkpointOptions.length };
                    }
                }
            }
            
            // Strategy 2: Look for Gradio/WebUI inputs by label
            const allLabels = Array.from(document.querySelectorAll('label, span, div'));
            for (const label of allLabels) {
                const text = (label.textContent || '').toLowerCase().trim();
                if (text === 'checkpoint' || text === 'stable diffusion checkpoint' || text.startsWith('checkpoint')) {
                    // Look in siblings and children for input elements
                    let parent = label.parentElement;
                    if (parent) {
                        // Look for input/select within parent or nearby
                        const input = parent.querySelector('input, select, textarea, [contenteditable="true"]');
                        const dropdown = parent.querySelector('[role="listbox"], [role="combobox"], .dropdown');
                        
                        if (input) {
                            // Found an input field - might be a text input or custom dropdown
                            const dataList = input.list;
                            if (dataList && dataList.options) {
                                checkpointOptions = Array.from(dataList.options).map(opt => ({
                                    value: opt.value,
                                    text: opt.value.trim()
                                }));
                                return { 
                                    dropdownInfo: { id: input.id, type: 'datalist', foundViaLabel: text },
                                    options: checkpointOptions, 
                                    count: checkpointOptions.length 
                                };
                            }
                            
                            // Check if it's an Gradio dropdown (value contains the current selection)
                            const currentValue = input.value || input.textContent || '';
                            if (currentValue) {
                                return {
                                    dropdownInfo: { id: input.id, className: input.className, type: 'gradio-input', foundViaLabel: text },
                                    currentSelection: currentValue,
                                    note: 'Found Gradio input - need to click to see all options'
                                };
                            }
                        }
                        
                        if (dropdown) {
                            const opts = dropdown.querySelectorAll('[role="option"], .dropdown-item, option');
                            if (opts && opts.length > 0) {
                                checkpointOptions = Array.from(opts).map(opt => ({
                                    value: opt.value || opt.getAttribute('data-value') || opt.textContent.trim(),
                                    text: opt.textContent.trim()
                                }));
                                return { 
                                    dropdownInfo: { className: dropdown.className, type: 'custom-dropdown', foundViaLabel: text },
                                    options: checkpointOptions, 
                                    count: checkpointOptions.length 
                                };
                            }
                        }
                    }
                }
            }
            
            // Strategy 3: Debug - list all interactive elements
            const allInputs = Array.from(document.querySelectorAll('input, select, textarea'));
            const inputInfo = allInputs.map(inp => ({
                type: inp.tagName,
                id: inp.id,
                name: inp.name,
                className: inp.className.slice(0, 50),
                value: (inp.value || '').slice(0, 30),
                hasDatalist: !!inp.list
            }));
            
            return { 
                error: 'Checkpoint dropdown not found', 
                inputCount: allInputs.length,
                selectCount: selects.length,
                someInputs: inputInfo.slice(0, 10),
                hint: 'Check browser - the dropdown might be dynamically loaded or use a custom component'
            };
        })();
        """
        
        print("Locating checkpoint dropdown...")
        controller.perform(ExecuteJS(js_code))
        result = controller.get_last_js_result()
        
        if result and 'note' in result and 'Gradio' in result.get('note', ''):
            print(f"Found Gradio dropdown with current selection: {result.get('currentSelection')}")
            print("Clicking to open dropdown menu...")
            
            # Click on the input to open dropdown
            click_js = """
            (() => {
                const labels = Array.from(document.querySelectorAll('label, span, div'));
                for (const label of labels) {
                    const text = (label.textContent || '').toLowerCase().trim();
                    if (text === 'checkpoint' || text.startsWith('checkpoint')) {
                        const parent = label.parentElement;
                        if (parent) {
                            const input = parent.querySelector('input');
                            if (input) {
                                input.click();
                                input.focus();
                                return { clicked: true, id: input.id, className: input.className };
                            }
                        }
                    }
                }
                return { clicked: false, error: 'Input not found' };
            })();
            """
            controller.perform(ExecuteJS(click_js))
            click_result = controller.get_last_js_result()
            print(f"Click result: {click_result}")
            
            # Wait for dropdown to appear
            time.sleep(1)
            
            # Extract dropdown options from the opened menu
            extract_options_js = """
            (() => {
                // Look for the dropdown menu that appeared
                const dropdowns = document.querySelectorAll('[role="listbox"], .dropdown-menu, ul[class*="option"], ul[class*="dropdown"]');
                
                for (const dropdown of dropdowns) {
                    // Check if it's visible
                    const rect = dropdown.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const options = dropdown.querySelectorAll('[role="option"], li, .option-item, div[data-value]');
                        if (options && options.length > 0) {
                            const optList = Array.from(options).map(opt => {
                                const text = opt.textContent.trim();
                                const value = opt.getAttribute('data-value') || opt.getAttribute('value') || text;
                                return { value, text };
                            }).filter(opt => opt.text.length > 0);
                            
                            if (optList.length > 0) {
                                return {
                                    success: true,
                                    options: optList,
                                    count: optList.length,
                                    dropdownClass: dropdown.className
                                };
                            }
                        }
                    }
                }
                
                // Fallback: try to find any visible list items
                const allLists = Array.from(document.querySelectorAll('ul, ol, div[class*="menu"]'));
                for (const list of allLists) {
                    const rect = list.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const items = list.querySelectorAll('li, div[role="option"], .option, .item');
                        if (items && items.length > 2) {  // At least a few items
                            const optList = Array.from(items).map(item => ({
                                text: item.textContent.trim(),
                                value: item.getAttribute('data-value') || item.textContent.trim()
                            })).filter(opt => opt.text.length > 0 && opt.text.length < 100);
                            
                            if (optList.length > 0) {
                                return {
                                    success: true,
                                    options: optList,
                                    count: optList.length,
                                    note: 'Found via fallback method'
                                };
                            }
                        }
                    }
                }
                
                return { success: false, error: 'No dropdown menu found after click' };
            })();
            """
            
            print("Extracting options from opened dropdown...")
            controller.perform(ExecuteJS(extract_options_js))
            options_result = controller.get_last_js_result()
            
            if options_result and options_result.get('success'):
                result = options_result
        
        if result and result.get('success') or (result and 'count' in result and 'options' in result):
            print(f"\n✓ Found {result['count']} checkpoint options!")
            
            # Save to text file
            output_file = Path("checkpoint_list.txt")
            with open(output_file, 'w') as f:
                f.write(f"Checkpoint Dropdown Items from http://localhost:7860/\n")
                f.write(f"{'='*60}\n\n")
                if 'dropdownInfo' in result:
                    f.write(f"Dropdown Type: {result.get('dropdownInfo', {}).get('type', 'unknown')}\n")
                f.write(f"Total Options: {result['count']}\n\n")
                f.write(f"{'='*60}\n\n")
                
                for i, opt in enumerate(result['options'], 1):
                    f.write(f"{i}. {opt['text']}\n")
                    if opt.get('value') and opt['text'] != opt['value']:
                        f.write(f"   (value: {opt['value']})\n")
            
            print(f"\n✓ Checkpoint list saved to: {output_file.absolute()}")
            
            # Also print to console
            print("\nCheckpoint options:")
            for i, opt in enumerate(result['options'][:20], 1):  # Show first 20
                print(f"  {i}. {opt['text']}")
            if result['count'] > 20:
                print(f"  ... and {result['count'] - 20} more (see file for full list)")
        else:
            print(f"\nUnable to extract options: {result}")
            if 'someInputs' in result:
                print("\nDebug - Found these inputs:")
                for inp in result['someInputs']:
                    print(f"  - {inp}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Keep browser open for inspection
        input("\nPress Enter to close browser...")
        controller.stop()
        print("Browser closed.")

if __name__ == "__main__":
    extract_checkpoint_dropdown()
