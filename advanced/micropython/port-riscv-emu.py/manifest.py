# Manifest for freezing Python scripts into firmware
# This file defines which Python modules should be compiled and frozen into the firmware

# Freeze startup.py from the port directory
# For HEADLESS and UART modes, startup.py will be automatically executed on boot
freeze("$(PORT_DIR)", "startup.py")
