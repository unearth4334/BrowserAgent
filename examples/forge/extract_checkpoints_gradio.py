#!/usr/bin/env python3
"""
Script to extract Checkpoint dropdown items from Gradio-based WebUI at http://localhost:7860/
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import time
import json

def extract_checkpoint_dropdown():
    """Visit localhost:7860 and extract checkpoint options using Gradio's internal structure."""
    
    with sync_playwright() as p:
        # Launch browser (visible)
        print("Starting browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate
            print("Navigating to http://localhost:7860/...")
            page.goto("http://localhost:7860/", wait_until="domcontentloaded", timeout=30000)
            
            print("Waiting for Gradio to initialize...")
            time.sleep(5)
            
            # Strategy: Inspect Gradio's component structure directly
            print("Extracting checkpoint options from Gradio components...")
            
            result = page.evaluate("""
                () => {
                    // Try to find Gradio dropdown component data
                    // Gradio stores choices in component data structures
                    
                    // Method 1: Look for select/dropdown wrapper with data-testid
                    const checkpointElements = Array.from(document.querySelectorAll('*')).filter(el => {
                        const text = el.textContent || '';
                        const lower = text.toLowerCase();
                        return el.children.length > 0 && 
                               (lower.includes('checkpoint') && text.length < 50);
                    });
                    
                    if (checkpointElements.length > 0) {
                        const elem = checkpointElements[0];
                        // Look for input field with choices
                        const input = elem.parentElement?.querySelector('input');
                        if (input) {
                            // Check if there's a choices array attached to the component
                            // or look for siblings/nearby elements with options
                            
                            // Try to trigger the dropdown by clicking
                            input.click();
                            
                            // Wait a tiny bit for DOM update (synchronously in JS is tricky)
                            // Instead, let's look for existing dropdown elements
                        }
                    }
                    
                    // Method 2: Look for datalist element (HTML5 native)
                    const datalists = Array.from(document.querySelectorAll('datalist'));
                    for (const dl of datalists) {
                        const options = Array.from(dl.querySelectorAll('option'));
                        if (options.length > 0) {
                            return {
                                success: true,
                                method: 'datalist',
                                options: options.map(opt => opt.value || opt.textContent).filter(Boolean),
                                count: options.length
                            };
                        }
                    }
                    
                    // Method 3: Look for the actual Gradio component's internal state
                    // Gradio v4+ uses Svelte stores
                    const allInputs = Array.from(document.querySelectorAll('input'));
                    const checkpointInput = allInputs.find(inp => {
                        const parent = inp.closest('label') || inp.parentElement;
                        return parent && parent.textContent.toLowerCase().includes('checkpoint');
                    });
                    
                    if (checkpointInput) {
                        // Check for associated choices in Gradio's internal data
                        // This might be in a __gradio__ property or similar
                        const choices = checkpointInput.__choices || 
                                      checkpointInput.dataset.choices ||
                                      checkpointInput.getAttribute('aria-autocomplete');
                        
                        if (choices) {
                            try {
                                const parsed = typeof choices === 'string' ? JSON.parse(choices) : choices;
                                return {
                                    success: true,
                                    method: 'gradio-internal',
                                    options: Array.isArray(parsed) ? parsed : [],
                                    count: Array.isArray(parsed) ? parsed.length : 0
                                };
                            } catch (e) {}
                        }
                    }
                    
                    return {
                        success: false,
                        error: 'Could not find checkpoint options',
                        foundInputs: allInputs.length,
                        foundDataLists: datalists.length
                    };
                }
            """)
            
            print(f"Evaluation result: {json.dumps(result, indent=2)}")
            
            # If we didn't find it yet, try clicking and waiting for dropdown
            if not result.get('success'):
                print("\nTrying interactive click method...")
                
                # Click the checkbox input
                checkpoint_input = page.locator('text=Checkpoint').locator('..').locator('input').first
                if checkpoint_input.count() > 0:
                    print("Found checkpoint input, clicking...")
                    checkpoint_input.click()
                    time.sleep(1)
                    
                    # Now look for visible dropdown menu
                    dropdown_result = page.evaluate("""
                        () => {
                            // Look for newly appeared dropdown/listbox
                            const menus = Array.from(document.querySelectorAll('[role="listbox"], .dropdown, ul'));
                            
                            for (const menu of menus) {
                                const rect = menu.getBoundingClientRect();
                                // Check if visible and has reasonable size
                                if (rect.width > 50 && rect.height > 50) {
                                    const items = Array.from(menu.querySelectorAll('li, [role="option"], button, .option'));
                                    if (items.length > 1) {
                                        const options = items
                                            .map(item => item.textContent.trim())
                                            .filter(text => text && text.length > 0 && text.length < 100);
                                        
                                        if (options.length > 1) {
                                            return {
                                                success: true,
                                                method: 'dropdown-menu',
                                                options: options,
                                                count: options.length,
                                                menuClass: menu.className
                                            };
                                        }
                                    }
                                }
                            }
                            
                            return { success: false, error: 'No visible dropdown found' };
                        }
                    """)
                    
                    print(f"Dropdown result: {json.dumps(dropdown_result, indent=2)}")
                    result = dropdown_result
            
            # Process results
            if result.get('success') and result.get('options'):
                options = result['options']
                print(f"\n✓ Successfully extracted {len(options)} checkpoint options!")
                
                # Save to file
                output_file = Path("checkpoint_list.txt")
                with open(output_file, 'w') as f:
                    f.write(f"Checkpoint Dropdown Items from http://localhost:7860/\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Extraction Method: {result.get('method', 'unknown')}\n")
                    f.write(f"Total Options: {len(options)}\n\n")
                    f.write(f"{'='*60}\n\n")
                    
                    for i, opt in enumerate(options, 1):
                        f.write(f"{i}. {opt}\n")
                
                print(f"\n✓ Checkpoint list saved to: {output_file.absolute()}")
                
                # Print to console
                print("\nCheckpoint options:")
                for i, opt in enumerate(options[:30], 1):
                    print(f"  {i}. {opt}")
                if len(options) > 30:
                    print(f"  ... and {len(options) - 30} more (see file for full list)")
            else:
                print(f"\n✗ Could not extract checkpoint options")
                print(f"Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            input("\nPress Enter to close browser...")
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    extract_checkpoint_dropdown()
