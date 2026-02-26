import Cocoa
import FlutterMacOS
import os.log

private let flutterWindowReadyNotification = Notification.Name("MemScreenFlutterWindowReady")

@main
class AppDelegate: FlutterAppDelegate {
    private var floatingBall: FloatingBallWindow?
    private var methodChannel: FlutterMethodChannel?
    private var creationTimer: Timer?
    private var creationAttempts = 0
    private var shouldForceQuit = false
    private var mainWindow: NSWindow?
    private var lastKnownFlutterController: FlutterViewController?
    private var floatingBallHealthTimer: Timer?

    let logger = OSLog(subsystem: "com.memscreen", category: "AppDelegate")

    override func applicationWillFinishLaunching(_ notification: Notification) {
        super.applicationWillFinishLaunching(notification)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleFlutterWindowReady(_:)),
            name: flutterWindowReadyNotification,
            object: nil
        )
    }

    override func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        os_log("Terminate after last window closed", log: logger, type: .info)
        creationTimer?.invalidate()
        creationTimer = nil

        if shouldForceQuit {
            floatingBall?.close()
            floatingBall = nil
            return true
        }

        // Keep the floating ball alive when users close the main window.
        if let ball = floatingBall {
            ball.orderFront(nil)
            ball.makeKeyAndOrderFront(nil)
        } else if let controller = resolveFlutterController() {
            createFloatingBall(with: controller)
        } else {
            pollForFlutterController()
        }
        return false
    }

    func forceQuit() {
        os_log("Force quit called", log: logger, type: .info)
        os_log("Total windows before quit: %{public}d", log: logger, type: .info, NSApplication.shared.windows.count)
        shouldForceQuit = true

        // Close floating ball first
        floatingBall?.close()
        floatingBall = nil

        // Stop timer
        creationTimer?.invalidate()
        creationTimer = nil

        // Close all windows and terminate app immediately
        DispatchQueue.main.async { [weak self] in
            guard let strongSelf = self else { return }
            let log = strongSelf.logger

            for window in NSApplication.shared.windows {
                os_log("Closing window: %{public}@",
                       log: log, type: .info,
                       String(describing: type(of: window)))
                window.close()
            }

            // Force quit after short delay
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                os_log("Calling terminate and exit",
                       log: log, type: .info)
                NSApplication.shared.reply(toApplicationShouldTerminate: true)
                NSApplication.shared.terminate(nil)

                // Force exit with code 0 after another delay
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    exit(0)
                }
            }
        }
    }

    override func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        return true
    }

    override func applicationDidFinishLaunching(_ notification: Notification) {
        super.applicationDidFinishLaunching(notification)
        os_log("App did finish launching", log: logger, type: .info)
        // Build the floating ball after Flutter window/controller is ready.
        // We keep the main window visible to avoid blank-screen startup edge cases.
        DispatchQueue.main.async { [weak self] in
            self?.pollForFlutterController()
            self?.startFloatingBallHealthMonitor()
        }
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
        floatingBallHealthTimer?.invalidate()
        floatingBallHealthTimer = nil
    }

    @objc private func handleFlutterWindowReady(_ notification: Notification) {
        if let window = notification.object as? NSWindow {
            mainWindow = window
        }
        if let vc = notification.userInfo?["flutterViewController"] as? FlutterViewController {
            lastKnownFlutterController = vc
        }

        ensureMethodChannel(with: resolveFlutterController())

        if floatingBall == nil {
            createFloatingBall(with: resolveFlutterController())
        }
    }

    func attachMainFlutterWindow(_ window: NSWindow, controller: FlutterViewController) {
        mainWindow = window
        ensureMethodChannel(with: controller)
        if floatingBall == nil {
            createFloatingBall(with: controller)
        }
    }

    private func pollForFlutterController() {
        creationTimer?.invalidate()
        creationAttempts = 0
        os_log("Starting poll for Flutter controller", log: logger, type: .info)
        let log = logger
        creationTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] timer in
            guard let strongSelf = self else {
                os_log("Self is nil", log: log, type: .error)
                timer.invalidate()
                return
            }

            strongSelf.creationAttempts += 1

            // Only create floating ball once
            if strongSelf.floatingBall == nil {
                os_log("Searching for FlutterViewController, total windows: %{public}d",
                       log: log, type: .info,
                       NSApplication.shared.windows.count)

                // Prefer FlutterAppDelegate's main window when available.
                if let flutterVC = strongSelf.resolveFlutterController() {
                    if let window = strongSelf.findFlutterWindow() {
                        strongSelf.mainWindow = window
                    }
                    os_log("Found FlutterViewController, creating floating ball",
                           log: log, type: .info)
                    strongSelf.createFloatingBall(with: flutterVC)
                    timer.invalidate()
                    strongSelf.creationTimer = nil
                    return
                }

                if strongSelf.creationAttempts >= 20 {
                    os_log("Failed to find FlutterViewController after retries; creating fallback floating ball",
                           log: log, type: .error)
                    if strongSelf.floatingBall == nil {
                        strongSelf.createFloatingBall(with: nil)
                    }
                    timer.invalidate()
                    strongSelf.creationTimer = nil
                }
            } else {
                os_log("Floating ball already exists, skipping poll",
                       log: log, type: .info)
                timer.invalidate()
                strongSelf.creationTimer = nil
            }
        }
    }

    private func createFloatingBall(with controller: FlutterViewController?) {
        guard floatingBall == nil else { return }
        os_log("Creating floating ball", log: logger, type: .info)

        ensureMethodChannel(with: controller)

        // Force the primary screen (origin 0,0) so the ball does not end up on another monitor.
        let targetScreen: NSScreen
        if let primaryScreen = NSScreen.screens.first(where: { screen in
            screen.frame.origin.x == 0 && screen.frame.origin.y == 0
        }) {
            targetScreen = primaryScreen
        } else if let windowScreen = findFlutterWindow()?.screen {
            targetScreen = windowScreen
        } else {
            targetScreen = NSScreen.main ?? NSScreen.screens.first!
        }
        let screenFrame = targetScreen.visibleFrame
        let ballSize: CGFloat = 80
        let margin: CGFloat = 20

        let x = screenFrame.origin.x + screenFrame.width - ballSize - margin
        let y = screenFrame.origin.y + screenFrame.height - ballSize - margin

        let contentRect = NSRect(x: x, y: y, width: ballSize, height: ballSize)

        // Create floating ball as an auxiliary always-on-top controller.
        floatingBall = FloatingBallWindow(
            contentRect: contentRect,
            flutterChannel: methodChannel,
            parentWindow: findFlutterWindow()
        )

        floatingBall?.onClick = { [weak self] in
            // When floating ball is clicked, just show the main window (but keep it hidden)
            // Actually, let's show it since user wants to see the main window
            NSApp.setActivationPolicy(.regular)
            if let window = self?.findFlutterWindow() {
                if window.isMiniaturized {
                    window.deminiaturize(nil)
                }
                window.setIsVisible(true)
                window.makeKeyAndOrderFront(nil)
                if let strongSelf = self {
                    os_log("Main window shown", log: strongSelf.logger, type: .info)
                }
            }
        }
        floatingBall?.onQuit = { [weak self] in
            self?.forceQuit()
        }

        // Show floating ball above everything
        floatingBall?.orderFront(nil)
        floatingBall?.makeKeyAndOrderFront(nil)
        floatingBall?.level = .popUpMenu

        // Ensure app activation policy is regular
        NSApp.setActivationPolicy(.regular)

        // Activate app to ensure floating ball is visible
        NSApp.activate(ignoringOtherApps: true)

        os_log("Floating ball created at %{public}f, %{public}f", log: logger, type: .info, x, y)
    }

    private func startFloatingBallHealthMonitor() {
        floatingBallHealthTimer?.invalidate()
        floatingBallHealthTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            if self.shouldForceQuit { return }

            if self.floatingBall == nil {
                if let controller = self.resolveFlutterController() {
                    os_log("Floating ball missing, recreating", log: self.logger, type: .error)
                    self.createFloatingBall(with: controller)
                }
                return
            }

            if let ball = self.floatingBall, !ball.isVisible {
                os_log("Floating ball hidden unexpectedly, restoring", log: self.logger, type: .error)
                ball.orderFront(nil)
                ball.makeKeyAndOrderFront(nil)
                ball.level = .popUpMenu
            }
        }
    }

    private func ensureMethodChannel(with controller: FlutterViewController?) {
        if let controller = controller {
            lastKnownFlutterController = controller
        }
        if methodChannel == nil, let channelController = lastKnownFlutterController {
            methodChannel = FlutterMethodChannel(
                name: "com.memscreen/floating_ball",
                binaryMessenger: channelController.engine.binaryMessenger
            )

            methodChannel?.setMethodCallHandler { [weak self] (call, result) in
                self?.handleMethodCall(call, result: result)
            }
        }
    }

    private func findFlutterWindow() -> NSWindow? {
        if let mainWindow = mainWindow {
            return mainWindow
        }
        if let appMainWindow = mainFlutterWindow {
            return appMainWindow
        }
        for window in NSApplication.shared.windows {
            if let _ = window.contentViewController as? FlutterViewController {
                return window
            }
        }
        return nil
    }

    private func resolveFlutterController() -> FlutterViewController? {
        if let vc = lastKnownFlutterController {
            return vc
        }
        if let main = mainFlutterWindow,
           let vc = main.contentViewController as? FlutterViewController {
            return vc
        }
        for window in NSApplication.shared.windows {
            if let vc = window.contentViewController as? FlutterViewController {
                return vc
            }
        }
        return nil
    }

    private func toggleMainWindow() {
        guard let window = findFlutterWindow() else { return }

        if window.isMiniaturized {
            window.deminiaturize(nil)
            window.makeKeyAndOrderFront(nil)
            os_log("Main window restored from dock", log: logger, type: .info)
        } else if !window.isVisible {
            window.setIsVisible(true)
            window.makeKeyAndOrderFront(nil)
            os_log("Main window shown", log: logger, type: .info)
        } else {
            // Hide instead of minimizing to avoid extra dock icon
            window.orderOut(nil)
            os_log("Main window hidden", log: logger, type: .info)
        }
    }

    private func showMainWindowAndSwitch(to tabIndex: Int) {
        // Show main window
        if let window = findFlutterWindow() {
            if window.isMiniaturized {
                window.deminiaturize(nil)
            }
            window.setIsVisible(true)
            window.makeKeyAndOrderFront(nil)
        }

        // Notify Flutter to switch tab
        methodChannel?.invokeMethod("switchTab", arguments: ["index": tabIndex])
    }

    private func minimizeMainWindow() {
        guard let window = findFlutterWindow() else { return }
        if !window.isMiniaturized {
            window.miniaturize(nil)
        }
    }

    private func handleMethodCall(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        os_log("Method called: %{public}@", log: logger, type: .info, call.method)

        switch call.method {
        case "showFloatingBall":
            if floatingBall == nil {
                if let controller = resolveFlutterController() {
                    createFloatingBall(with: controller)
                } else {
                    pollForFlutterController()
                }
            }
            floatingBall?.orderFront(nil)
            floatingBall?.makeKeyAndOrderFront(nil)
            result(nil)
        case "hideFloatingBall":
            floatingBall?.orderOut(nil)
            result(nil)
        case "setRecordingState":
            if let args = call.arguments as? [String: Any],
               let isRecording = args["isRecording"] as? Bool {
                floatingBall?.setRecordingState(isRecording)
                result(nil)
            } else {
                result(FlutterError(code: "INVALID_ARGS", message: "Expected isRecording argument", details: nil))
            }
        case "setPausedState":
            if let args = call.arguments as? [String: Any],
               let isPaused = args["isPaused"] as? Bool {
                floatingBall?.setPausedState(isPaused)
                result(nil)
            } else {
                result(FlutterError(code: "INVALID_ARGS", message: "Expected isPaused argument", details: nil))
            }
        case "setTrackingState":
            if let args = call.arguments as? [String: Any],
               let isTracking = args["isTracking"] as? Bool {
                floatingBall?.setTrackingState(isTracking)
                result(nil)
            } else {
                result(FlutterError(code: "INVALID_ARGS", message: "Expected isTracking argument", details: nil))
            }
        case "openQuickChat":
            showMainWindowAndSwitch(to: 3)
            result(nil)
        case "openVideos":
            showMainWindowAndSwitch(to: 1)
            result(nil)
        case "openSettings":
            showMainWindowAndSwitch(to: 4)
            result(nil)
        case "quitApp":
            forceQuit()
            result(nil)
        case "switchTab":
            if let args = call.arguments as? [String: Any],
               let index = args["index"] as? Int {
                showMainWindowAndSwitch(to: index)
                result(nil)
            } else {
                result(FlutterError(code: "INVALID_ARGS", message: "Expected index argument", details: nil))
            }
        case "prepareRegionSelection":
            var requestedScreenIndex: Int?
            var requestedScreenDisplayID: Int?
            if let args = call.arguments as? [String: Any] {
                if let idx = args["screenIndex"] as? Int {
                    requestedScreenIndex = idx
                } else if let idxNum = args["screenIndex"] as? NSNumber {
                    requestedScreenIndex = idxNum.intValue
                }
                if let displayID = args["screenDisplayId"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayID = args["screen_display_id"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayIDNum = args["screenDisplayId"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                } else if let displayIDNum = args["screen_display_id"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                }
            }
            if floatingBall == nil {
                if let controller = resolveFlutterController() {
                    createFloatingBall(with: controller)
                } else {
                    pollForFlutterController()
                }
            }
            floatingBall?.orderFront(nil)
            floatingBall?.makeKeyAndOrderFront(nil)
            floatingBall?.setSelectedScreen(
                requestedScreenIndex,
                displayID: requestedScreenDisplayID
            )
            minimizeMainWindow()
            floatingBall?.beginRegionSelectionFromMainUI()
            result(nil)
        case "prepareWindowSelection":
            var requestedScreenIndex: Int?
            var requestedScreenDisplayID: Int?
            if let args = call.arguments as? [String: Any] {
                if let idx = args["screenIndex"] as? Int {
                    requestedScreenIndex = idx
                } else if let idxNum = args["screenIndex"] as? NSNumber {
                    requestedScreenIndex = idxNum.intValue
                }
                if let displayID = args["screenDisplayId"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayID = args["screen_display_id"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayIDNum = args["screenDisplayId"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                } else if let displayIDNum = args["screen_display_id"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                }
            }
            if floatingBall == nil {
                if let controller = resolveFlutterController() {
                    createFloatingBall(with: controller)
                } else {
                    pollForFlutterController()
                }
            }
            floatingBall?.orderFront(nil)
            floatingBall?.makeKeyAndOrderFront(nil)
            floatingBall?.setSelectedScreen(
                requestedScreenIndex,
                displayID: requestedScreenDisplayID
            )
            minimizeMainWindow()
            floatingBall?.beginWindowSelectionFromMainUI()
            result(nil)
        case "prepareScreenRecording":
            var requestedScreenIndex: Int?
            var requestedScreenDisplayID: Int?
            if let args = call.arguments as? [String: Any] {
                if let idx = args["screenIndex"] as? Int {
                    requestedScreenIndex = idx
                } else if let idxNum = args["screenIndex"] as? NSNumber {
                    requestedScreenIndex = idxNum.intValue
                }
                if let displayID = args["screenDisplayId"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayID = args["screen_display_id"] as? Int {
                    requestedScreenDisplayID = displayID
                } else if let displayIDNum = args["screenDisplayId"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                } else if let displayIDNum = args["screen_display_id"] as? NSNumber {
                    requestedScreenDisplayID = displayIDNum.intValue
                }
            }
            if floatingBall == nil {
                if let controller = resolveFlutterController() {
                    createFloatingBall(with: controller)
                } else {
                    pollForFlutterController()
                }
            }
            floatingBall?.orderFront(nil)
            floatingBall?.makeKeyAndOrderFront(nil)
            floatingBall?.setSelectedScreen(
                requestedScreenIndex,
                displayID: requestedScreenDisplayID
            )
            minimizeMainWindow()
            result(nil)
        default:
            result(FlutterMethodNotImplemented)
        }
    }
}
