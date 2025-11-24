# Manifest for freezing Python scripts into firmware
# This file defines which Python modules should be compiled and frozen into the firmware

# Freeze startup.py (the default embedded script)
# To freeze a different script, modify this file or specify FROZEN_SCRIPT in your Makefile
freeze("$(PORT_DIR)", "startup.py")
