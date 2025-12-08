#!/usr/bin/env python3
"""Test script to verify prompt behavior by monitoring server output."""
import subprocess
import time
import sys

print("Starting server and monitoring for 5 seconds...")
print("Expected: ONE initial prompt '> ', then wait silently")
print("=" * 60)

proc = subprocess.Popen(
    [".venv/bin/python", "-m", "browser_agent.server.browser_server", "--wait"],
    cwd="/home/sdamk/dev/BrowserAgent",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

start_time = time.time()
prompt_count = 0
lines = []

try:
    while time.time() - start_time < 8:
        line = proc.stdout.readline()
        if line:
            lines.append(line)
            # Count prompts
            if line.strip() == ">":
                prompt_count += 1
                print(f"[{time.time()-start_time:.1f}s] PROMPT #{prompt_count}")
        time.sleep(0.1)
finally:
    proc.terminate()
    proc.wait()

print("=" * 60)
print(f"\nPrompt count in 8 seconds: {prompt_count}")
print(f"Expected: 1 (one initial prompt)")
print(f"Result: {'✓ PASS' if prompt_count <= 1 else '✗ FAIL - spam detected'}")
print("\nFull output:")
print("".join(lines))
