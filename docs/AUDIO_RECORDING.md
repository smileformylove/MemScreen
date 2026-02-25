# Audio Recording

MemScreen supports dual audio capture during screen recording.

## Sources

- `System audio`
- `Microphone`

Both switches are independent and can be enabled together.

## Runtime mapping

- system + microphone -> `mixed`
- system only -> `system_audio`
- microphone only -> `microphone`
- both off -> `none`

## Where to configure

`Settings` -> Recording section:
- `System audio`
- `Microphone`

## Verification checklist

1. Start a short recording.
2. Play system media and speak to microphone.
3. Stop recording.
4. In `Videos`, play the output and confirm both tracks are present.

## Common issues

- No system audio in output:
  - keep `System audio` enabled
  - verify audio route/loopback setup for current macOS runtime
- No microphone audio:
  - grant Microphone permission in macOS Privacy settings
- Video has audio but local playback is muted during record:
  - check output routing mode and restore logic after stop
