# Floating Ball (macOS)

The floating ball is a native macOS control entry for quick recording operations.

## Purpose

- start/stop recording quickly
- switch between recording tools
- keep control available while main window is minimized

## Tool coverage

Floating controls are aligned with the main recording modes:
- `Screen`
- `All Screens`
- `Region`
- `Window`
- key/mouse tracking toggle (if enabled in current build)

## Behavior

- Main window can be minimized while keeping floating controls active.
- Region and window flows require explicit user confirmation before recording starts.
- Recording can be stopped from floating controls.

## Notes

- If the floating controller is missing after app switch, bring MemScreen to foreground once.
- Ensure Accessibility permission is granted for input-tracking-related actions.
