# Recording Guide

## Recording modes

MemScreen supports 4 recording modes:
- `Screen` (single selected display)
- `All Screens`
- `Region`
- `Window`

## Recommended workflow

1. Open `Record` screen.
2. Choose mode (`Screen`, `Region`, `Window`, `All Screens`).
3. If mode requires selection:
   - `Region`: drag to select area, then confirm
   - `Window`: pick target window, then confirm
4. Click stop from the floating control when done.
5. Open `Videos` for immediate playback and organization.

## Audio behavior

Audio toggles are in `Settings`:
- `System audio`
- `Microphone`

Both can be enabled simultaneously.

## Keyboard and mouse tracking

`Key-Mouse tracking` can auto-start with recording (configurable in Settings).

## Troubleshooting

- Region selection on wrong screen:
  - make sure the target screen is selected before opening region selector
- No system audio:
  - verify system audio capture route in macOS settings and keep `System audio` enabled
- No microphone audio:
  - grant Microphone permission to the app/terminal runtime
