#!/bin/sh

# Check if DEBUG_FLASK_APP = 1
RELOAD_CMD="--no-reload"
if [ "$FLASK_AUTO_RELOAD" = "1" ]; then
    RELOAD_CMD=""
fi
if [ "$DEBUG_FLASK_APP" = "1" ]; then
    echo "Running NLP4ALL for VSCode Debugging"
    python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m flask --no-debugger --app nlp4all run --no-reload --host=0.0.0.0 --port=5000
else
    echo "Running NLP4ALL Development Server"
    python -m flask --debug --app nlp4all run $RELOAD_CMD --host=0.0.0.0 --port=5000
fi

