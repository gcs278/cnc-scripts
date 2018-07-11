#!/bin/bash
echo "Watching GCode files..."
watchmedo shell-command -w --patterns="*.gcode" --recursive --command='python /Users/grantspence/Google\ Drive/GS_Custom_Woodworking/cnc-scripts/python/macro_inject_verbose.py && python /Users/grantspence/Google\ Drive/GS_Custom_Woodworking/cnc-scripts/python/create-zinfo-file.py' /Users/grantspence/Google\ Drive/GS_Custom_Woodworking/

