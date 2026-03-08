import AppKit
import ApplicationServices
import Foundation

final class NativeInputTracker {
    private var globalKeyMonitor: Any?
    private var localKeyMonitor: Any?
    private var globalMouseMonitor: Any?
    private var localMouseMonitor: Any?
    private var isTracking = false
    private var startedAt: Date?
    private var events: [[String: Any]] = []

    func start() -> [String: Any] {
        if isTracking {
            return ["ok": true, "isTracking": true, "eventCount": events.count]
        }

        let accessibilityGranted = AXIsProcessTrusted()
        let inputGranted = CGPreflightListenEventAccess()
        if !accessibilityGranted || !inputGranted {
            return [
                "ok": false,
                "error": "Accessibility/Input Monitoring permission is required for native input tracking.",
                "accessibilityGranted": accessibilityGranted,
                "inputMonitoringGranted": inputGranted,
            ]
        }

        startedAt = Date()
        events.removeAll()
        installMonitors()
        isTracking = true
        return ["ok": true, "isTracking": true, "eventCount": 0]
    }

    func stop() -> [String: Any] {
        removeMonitors()
        isTracking = false
        return ["ok": true, "isTracking": false, "eventCount": events.count]
    }

    func status() -> [String: Any] {
        return [
            "isTracking": isTracking,
            "eventCount": events.count,
            "accessibilityGranted": AXIsProcessTrusted(),
            "inputMonitoringGranted": CGPreflightListenEventAccess(),
        ]
    }

    func saveSession() -> [String: Any] {
        guard !events.isEmpty else {
            return ["ok": false, "error": "No events to save"]
        }
        let sorted = events.sorted { lhs, rhs in
            (lhs["time"] as? String ?? "") < (rhs["time"] as? String ?? "")
        }
        let startTime = sorted.first?["time"] as? String ?? ""
        let endTime = sorted.last?["time"] as? String ?? startTime
        let savedCount = sorted.count
        events.removeAll()
        startedAt = Date()
        return [
            "ok": true,
            "events": sorted,
            "eventsSaved": savedCount,
            "startTime": startTime,
            "endTime": endTime,
        ]
    }

    private func installMonitors() {
        let keyMask: NSEvent.EventTypeMask = [.keyDown]
        let mouseMask: NSEvent.EventTypeMask = [.leftMouseDown, .rightMouseDown, .otherMouseDown]

        globalKeyMonitor = NSEvent.addGlobalMonitorForEvents(matching: keyMask) { [weak self] event in
            self?.handleKey(event)
        }
        localKeyMonitor = NSEvent.addLocalMonitorForEvents(matching: keyMask) { [weak self] event in
            self?.handleKey(event)
            return event
        }
        globalMouseMonitor = NSEvent.addGlobalMonitorForEvents(matching: mouseMask) { [weak self] event in
            self?.handleMouse(event)
        }
        localMouseMonitor = NSEvent.addLocalMonitorForEvents(matching: mouseMask) { [weak self] event in
            self?.handleMouse(event)
            return event
        }
    }

    private func removeMonitors() {
        if let globalKeyMonitor {
            NSEvent.removeMonitor(globalKeyMonitor)
            self.globalKeyMonitor = nil
        }
        if let localKeyMonitor {
            NSEvent.removeMonitor(localKeyMonitor)
            self.localKeyMonitor = nil
        }
        if let globalMouseMonitor {
            NSEvent.removeMonitor(globalMouseMonitor)
            self.globalMouseMonitor = nil
        }
        if let localMouseMonitor {
            NSEvent.removeMonitor(localMouseMonitor)
            self.localMouseMonitor = nil
        }
    }

    private func handleKey(_ event: NSEvent) {
        guard isTracking else { return }
        let text = event.charactersIgnoringModifiers ?? event.characters ?? "keyCode:\(event.keyCode)"
        events.append([
            "type": "keypress",
            "text": "keyboard: press (\(text))",
            "time": Self.timestampString(from: Date()),
        ])
    }

    private func handleMouse(_ event: NSEvent) {
        guard isTracking else { return }
        let button: String
        switch event.type {
        case .leftMouseDown:
            button = "left"
        case .rightMouseDown:
            button = "right"
        default:
            button = "other"
        }
        events.append([
            "type": "click",
            "text": "mouse: press (\(button))",
            "time": Self.timestampString(from: Date()),
        ])
    }

    private static func timestampString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.string(from: date)
    }
}
