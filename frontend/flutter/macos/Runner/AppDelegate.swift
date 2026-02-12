import Cocoa
import FlutterMacOS
import os.log

@main
class AppDelegate: FlutterAppDelegate {
    private var floatingBall: FloatingBallWindow?
    private var methodChannel: FlutterMethodChannel?
    private var creationTimer: Timer?
    private var shouldForceQuit = false

    let logger = OSLog(subsystem: "com.memscreen", category: "AppDelegate")

    override func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        os_log("Terminate after last window closed", log: logger, type: .info)
        creationTimer?.invalidate()
        creationTimer = nil
        if shouldForceQuit {
            return true
        }
        return false
    }

    func forceQuit() {
        os_log("Force quit called", log: logger, type: .info)
        shouldForceQuit = true
        for window in NSApplication.shared.windows {
            window.close()
        }
        creationTimer?.invalidate()
        creationTimer = nil
        NSApplication.shared.reply(toApplicationShouldTerminate: true)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            NSApplication.shared.terminate(nil)
        }
    }

    override func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        return true
    }

    override func applicationDidFinishLaunching(_ notification: Notification) {
        os_log("App did finish launching", log: logger, type: .info)
        pollForFlutterController()
    }

    private func pollForFlutterController() {
        os_log("Starting poll for Flutter controller", log: logger, type: .info)
        let log = logger
        creationTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] timer in
            guard let strongSelf = self else {
                os_log("Self is nil", log: log, type: .error)
                timer.invalidate()
                return
            }

            if strongSelf.floatingBall == nil {
                os_log("Searching for FlutterViewController, windows: %{public}d", log: log, type: .info, NSApplication.shared.windows.count)
                for window in NSApplication.shared.windows {
                    if let flutterVC = window.contentViewController as? FlutterViewController {
                        os_log("Found FlutterViewController", log: log, type: .info)
                        strongSelf.createFloatingBall(with: flutterVC)
                        timer.invalidate()
                        return
                    }
                }
            } else {
                timer.invalidate()
            }
        }
    }

    private func createFloatingBall(with controller: FlutterViewController) {
        guard floatingBall == nil else { return }
        os_log("Creating floating ball", log: logger, type: .info)

        if methodChannel == nil {
            methodChannel = FlutterMethodChannel(
                name: "com.memscreen/floating_ball",
                binaryMessenger: controller.engine.binaryMessenger
            )

            methodChannel?.setMethodCallHandler { [weak self] (call, result) in
                self?.handleMethodCall(call, result: result)
            }
        }

        let screenSize = NSScreen.main?.frame ?? NSRect.zero
        let ballSize: CGFloat = 80
        let margin: CGFloat = 20

        let x = screenSize.origin.x + screenSize.width - ballSize - margin
        let y = screenSize.origin.y + screenSize.height - ballSize - margin

        let contentRect = NSRect(x: x, y: y, width: ballSize, height: ballSize)

        floatingBall = FloatingBallWindow(
            contentRect: contentRect,
            flutterChannel: methodChannel
        )

        floatingBall?.onClick = {
            for window in NSApplication.shared.windows {
                if window.contentViewController is FlutterViewController {
                    window.setIsVisible(true)
                    window.makeKeyAndOrderFront(nil)
                    break
                }
            }
        }

        floatingBall?.orderFront(nil)

        os_log("Floating ball created at %{public}f, %{public}f", log: logger, type: .info, x, y)
    }

    private func handleMethodCall(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "showFloatingBall":
            floatingBall?.makeKeyAndOrderFront(nil)
            result(nil)

        case "hideFloatingBall":
            floatingBall?.orderOut(nil)
            result(nil)

        case "setRecordingState":
            if let args = call.arguments as? [String: Any],
               let isRecording = args["isRecording"] as? Bool {
                floatingBall?.setRecordingState(isRecording)
                os_log("Recording state set to %{public}@", log: logger, type: .info, isRecording)
                result(nil)
            } else {
                result(FlutterError(code: "invalid_args", message: "isRecording required", details: nil))
            }

        case "setPausedState":
            if let args = call.arguments as? [String: Any],
               let isPaused = args["isPaused"] as? Bool {
                floatingBall?.setPausedState(isPaused)
                os_log("Paused state set to %{public}@", log: logger, type: .info, isPaused)
                result(nil)
            } else {
                result(FlutterError(code: "invalid_args", message: "isPaused required", details: nil))
            }

        case "quitApp":
            floatingBall?.close()
            NSApplication.shared.terminate(nil)
            result(nil)

        default:
            result(FlutterMethodNotImplemented)
        }
    }
}
