# Rule: Cross-Platform Standards
**Activation Mode**: Always On
**Scope**: Workspace-wide

---

## Operating System Portability
- **Path Separation:** Always use `os.path.join()`, `os.path.normpath()`, or Python's built-in `pathlib` for file system paths. Do not use hardcoded Unix forward slashes `/` or Windows backslashes `\\` for absolute paths.
- **Home Directory:** Use `os.path.expanduser("~")` to refer to the user's home directory across different OS environments.
- **OS Differentiated Blocks:** When execution requires platform-specific behavior (e.g. running terminal commands, checking ports, writing files), use:
  ```python
  import sys
  if sys.platform.startswith('win'):
      # Windows-specific behavior
  else:
      # Linux/Unix-specific behavior
  ```

## Serial Communication Portability
- **Port Naming:**
  - Linux uses `/dev/tty*`, `/dev/ttyUSB*`, `/dev/ttyACM*`.
  - Windows uses `COM*` (e.g. `COM1`, `COM3`).
- **Connection Flags:**
  - Ensure the connection routine dynamically supports `COM` prefixes.
  - Do not hardcode a specific check (like `msg[:8] == "/dev/tty"`) that excludes `COM` ports. Allow any validated port string to be opened.
- **Port Permission & Diagnostics:**
  - On Linux, if port opening fails due to permissions, prompt the user to add themselves to the `dialout` group.
  - On Windows, if port opening fails, check if the port is already in use by another serial terminal or IDE, and prompt the user accordingly.
