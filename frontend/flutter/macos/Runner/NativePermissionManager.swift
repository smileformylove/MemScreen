import AppKit
import ApplicationServices
import Foundation

final class NativePermissionManager {
    func status(prompt: Bool = false) -> [String: Any] {
        let screenGranted = CGPreflightScreenCaptureAccess()
        if prompt && !screenGranted {
            _ = CGRequestScreenCaptureAccess()
        }

        let accessibilityGranted = Self.accessibilityGranted(prompt: prompt)
        let inputGranted = CGPreflightListenEventAccess()
        if prompt && !inputGranted {
            _ = CGRequestListenEventAccess()
        }

        return [
            "platform": "macOS",
            "runtime_executable": Bundle.main.bundlePath,
            "app_bundle_hint": Bundle.main.bundlePath,
            "screen_recording": [
                "granted": screenGranted,
                "message": screenGranted
                    ? "Screen Recording permission granted"
                    : "Screen Recording permission is required for native screen capture.",
                "settings_anchor": "Privacy_ScreenCapture",
            ],
            "accessibility": [
                "granted": accessibilityGranted,
                "message": accessibilityGranted
                    ? "Accessibility permission granted"
                    : "Accessibility permission is required for hotkeys and native input tracking.",
                "settings_anchor": "Privacy_Accessibility",
            ],
            "input_monitoring": [
                "granted": inputGranted,
                "message": inputGranted
                    ? "Input Monitoring permission granted"
                    : "Input Monitoring permission is required for key logging and native input tracking.",
                "settings_anchor": "Privacy_ListenEvent",
            ],
        ]
    }

    @discardableResult
    func openSettings(area: String) -> Bool {
        let key = area.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let anchors: [String: String] = [
            "screen_recording": "Privacy_ScreenCapture",
            "accessibility": "Privacy_Accessibility",
            "input_monitoring": "Privacy_ListenEvent",
        ]
        guard let anchor = anchors[key],
              let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?\(anchor)") else {
            return false
        }
        NSWorkspace.shared.open(url)
        return true
    }

    private static func accessibilityGranted(prompt: Bool) -> Bool {
        if !prompt {
            return AXIsProcessTrusted()
        }
        guard let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary? else {
            return AXIsProcessTrusted()
        }
        return AXIsProcessTrustedWithOptions(options)
    }
}
