# sysmanager

A simple Linux system management suite written in C.

## Components

### process_manager/
A terminal-based process manager that reads directly from `/proc`.

**Features:**
- List all running processes (PID, name, state, cmdline)
- Search process by name
- Kill process by PID (SIGKILL / SIGTERM)
- Show detailed process info (threads, memory)
- Top CPU processes
- Memory usage with ASCII bar graph

**Build & run:**
```sh
cd process_manager
make
./procman
```

---

### desktop_env/
A minimal X11 desktop environment / window manager.

**Features:**
- Manages and frames all X windows
- Mouse-drag to move windows
- Taskbar showing open windows + clock
- Click taskbar button to raise/focus window
- Alt+Tab  : cycle window focus
- Alt+F2   : open terminal (xterm)
- Alt+F4   : close focused window
- Alt+Q    : quit desktop

**Dependencies:**
```sh
# Debian/Ubuntu
sudo apt install libx11-dev libxft-dev libxinerama-dev

# Arch
sudo pacman -S libx11 libxft libxinerama
```

**Build & run:**
```sh
cd desktop_env
make
# Add to ~/.xinitrc:
exec ./desktop
# Then start with: startx
```

---

## Build everything at once
```sh
make        # builds both
make clean  # cleans both
```
