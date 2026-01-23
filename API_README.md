# Trigger predefined macros
curl -X POST http://localhost:5000/macro/close_tab  # Ctrl+W
curl -X POST http://localhost:5000/macro/back       # Alt+Left
curl -X POST http://localhost:5000/macro/save       # Ctrl+S
curl -X POST http://localhost:5000/macro/enter      # Enter

# Send custom key combinations
curl -X POST http://localhost:5000/keys -H "Content-Type: application/json" \
  -d '{"keys": "ctrl+shift+n"}'

# Type text
curl -X POST http://localhost:5000/type -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'

# List available macros
curl http://localhost:5000/macros

# Health check
curl http://localhost:5000/health