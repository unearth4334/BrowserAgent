# Integration Tests

This directory contains integration test scripts for the BrowserAgent server and interactive features.

## Test Scripts

### test_ready_command.py
Tests the "ready" command to check if the browser server is ready for commands.

Usage:
```bash
python tests/integration/test_ready_command.py
```

### test_prompt_spam.py
Tests the server's ability to handle rapid command input.

Usage:
```bash
python tests/integration/test_prompt_spam.py
```

### test_server_demo.sh
Full demo script that:
1. Starts a browser server
2. Tests the ready command
3. Demonstrates basic server operations

Usage:
```bash
./tests/integration/test_server_demo.sh
```

### test_interactive.sh
Tests interactive session functionality.

Usage:
```bash
./tests/integration/test_interactive.sh
```

## Running from Repository Root

All scripts are designed to be run from the repository root:

```bash
# From /home/sdamk/dev/BrowserAgent
python tests/integration/test_ready_command.py
./tests/integration/test_server_demo.sh
```

## Documentation

See [INTERACTIVE_SERVER_GUIDE.md](../../docs/INTERACTIVE_SERVER_GUIDE.md) for detailed documentation on the interactive server features.
