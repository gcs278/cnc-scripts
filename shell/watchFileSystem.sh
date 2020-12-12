#!/bin/bash
echo "Watching GCode files..."
COMMAND="python /Users/grantspence/Google\ Drive/GS_Custom_Woodworking/cnc-scripts/python/macro_inject_verbose.py && python /Users/grantspence/Google\ Drive/GS_Custom_Woodworking/cnc-scripts/python/create-zinfo-file.py"

# Run it once
eval "$COMMAND"

# Watch file system and run it
watchmedo shell-command -w --patterns="*.gcode" --recursive --command="$COMMAND" /Users/grantspence/Google\ Drive/

