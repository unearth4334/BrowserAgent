#!/usr/bin/env python3
"""
Script to visit http://localhost:7860/ and extract all Checkpoint dropdown items using Playwright directly.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def extract_checkpoint_dropdown():
    """Visit localhost:7860 and extract all checkpoint dropdown options."""
    
    with sync_playwright() as p:
        # Launch browser (visible for debugging)
        print("Starting browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to URL
            print("Navigating to http://localhost:7860/...")
            page.goto("http://localhost:7860/", wait_until="domcontentloaded", timeout=30000)
            
            print("Waiting for page to load...")
            time.sleep(5)
            
            # Find the checkpoint input/dropdown by label
            print("Looking for checkpoint dropdown...")
            
            # Try to find via label text
            checkpoint_found = False
            dropdown_options = []
            
            # Strategy 1: Look for input with "checkpoint" label
            labels = page.query_selector_all('label, span')
            for label in labels:
                text = label.text_content().lower().strip()
                if 'checkpoint' in text:
                    print(f"Found label: '{label.text_content().strip()}'")
                    
                    # Try to find associated input
                    parent = label.evaluate('el => el.parentElement')
                    input_elem = label.evaluate('''el => {
                        const parent = el.parentElement;
                        return parent ? parent.querySelector('input') : null;
                    }''')
                    
                    if input_elem:
                        # Get the input element
                        inputs = page.query_selector_all('input.svelte-1mhtq7j')
                        if inputs:
                            print(f"Found {len(inputs)} inputs with svelte class")
                            input_field = inputs[0]
                            
                            # Click to open dropdown
                            print("Clicking input to open dropdown...")
                            input_field.click()
                            time.sleep(0.5)
                            
                            # Look for dropdown options that appeared
                            # Gradio dropdowns often use ul/li structure
                            dropdowns = page.query_selector_all('ul, .dropdown, [role="listbox"]')
                            for dd in dropdowns:
                                if dd.is_visible():
                                    items = dd.query_selector_all('li, [role="option"], .option')
                                    if items and len(items) > 0:
                                        print(f"Found dropdown with {len(items)} items!")
                                        dropdown_options = [item.text_content().strip() for item in items]
                                        checkpoint_found = True
                                        break
                            
                            if checkpoint_found:
                                break
                    break
            
            # Strategy 2: Extract checkpoint options directly from the datalist or options
            if not checkpoint_found:
                print("Strategy 1 failed, trying direct datalist extraction...")
                
                # Look for the checkpoint input that has data-testid or specific class
                checkpoint_input = None
                labels = page.query_selector_all('label')
                for label in labels:
                    if 'checkpoint' in label.text_content().lower():
                        parent = label.evaluate('el => el.parentElement')
                        # Try to get the input within this parent
                        try:
                            checkpoint_input = label.evaluate_handle('''el => {
                                const parent = el.parentElement;
                                return parent ? parent.querySelector('input') : null;
                            }''')
                            if checkpoint_input:
                                break
                        except:
                            pass
                
                if checkpoint_input:
                    # Get the list attribute or datalist
                    list_id = checkpoint_input.evaluate('el => el.getAttribute("list")')
                    print(f"Found input with list attribute: {list_id}")
                    
                    if list_id:
                        # Get options from datalist
                        datalist = page.query_selector(f'#{list_id}')
                        if datalist:
                            options_elems = datalist.query_selector_all('option')
                            dropdown_options = [opt.get_attribute('value') for opt in options_elems if opt.get_attribute('value')]
                            if dropdown_options:
                                print(f"Found {len(dropdown_options)} options in datalist!")
                                checkpoint_found = True
            
            if checkpoint_found and dropdown_options:
                print(f"\n✓ Successfully extracted {len(dropdown_options)} checkpoint options!")
                
                # Save to file
                output_file = Path("checkpoint_list.txt")
                with open(output_file, 'w') as f:
                    f.write(f"Checkpoint Dropdown Items from http://localhost:7860/\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Total Options: {len(dropdown_options)}\n\n")
                    f.write(f"{'='*60}\n\n")
                    
                    for i, opt in enumerate(dropdown_options, 1):
                        f.write(f"{i}. {opt}\n")
                
                print(f"\n✓ Checkpoint list saved to: {output_file.absolute()}")
                
                # Print to console
                print("\nCheckpoint options:")
                for i, opt in enumerate(dropdown_options[:30], 1):
                    print(f"  {i}. {opt}")
                if len(dropdown_options) > 30:
                    print(f"  ... and {len(dropdown_options) - 30} more (see file for full list)")
            else:
                print("\n✗ Could not find checkpoint dropdown options")
                print("The page might need manual interaction or use a different UI structure")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Keep browser open for inspection
            input("\nPress Enter to close browser...")
            browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    extract_checkpoint_dropdown()
