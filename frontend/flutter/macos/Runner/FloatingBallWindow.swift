import Cocoa
import FlutterMacOS

/// Native macOS floating ball window for MemScreen Flutter
class FloatingBallWindow: NSPanel {
    private var ballView: FloatingBallView!
    private var flutterChannel: FlutterMethodChannel?

    // State
    var isRecording: Bool = false
    var isPaused: Bool = false

    // Drag state
    private var initialMouseLocation: NSPoint?
    private var initialWindowLocation: NSPoint?
    private var isDragging: Bool = false
    private let dragThreshold: CGFloat = 5.0

    // Callbacks
    var onClick: (() -> Void)?
    var onRightClick: (() -> Void)?

    init(contentRect: NSRect, flutterChannel: FlutterMethodChannel?) {
        super.init(
            contentRect: contentRect,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )

        self.flutterChannel = flutterChannel

        // Configure window properties
        self.level = .floating
        self.isOpaque = false
        self.backgroundColor = .clear
        self.isMovableByWindowBackground = true

        // Note: Don't set parent property - it can cause issues on some macOS versions

        // Configure panel behavior
        self.isFloatingPanel = true
        self.becomesKeyOnlyIfNeeded = true

        // Set collection behavior to join all spaces
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]

        // Create ball view
        self.ballView = FloatingBallView(frame: contentRect)
        self.contentView = self.ballView

        // Setup mouse tracking
        self.ballView.onMouseDown = { [weak self] event in
            self?.handleMouseDown(event)
        }
        self.ballView.onMouseDragged = { [weak self] event in
            self?.handleMouseDragged(event)
        }
        self.ballView.onMouseUp = { [weak self] event in
            self?.handleMouseUp(event)
        }
        self.ballView.onRightMouseDown = { [weak self] event in
            self?.handleRightMouseDown(event)
        }

        // Don't hide when app loses focus
        self.hidesOnDeactivate = false
    }

    private func handleMouseDown(_ event: NSEvent) {
        initialMouseLocation = event.locationInWindow
        initialWindowLocation = self.frame.origin
        isDragging = false
    }

    private func handleMouseDragged(_ event: NSEvent) {
        guard let initialMouse = initialMouseLocation,
              let initialWindow = initialWindowLocation else { return }

        let currentMouseLocation = event.locationInWindow
        let deltaX = currentMouseLocation.x - initialMouse.x
        let deltaY = currentMouseLocation.y - initialMouse.y

        // Check if moved beyond threshold
        if !isDragging {
            let distance = sqrt(deltaX * deltaX + deltaY * deltaY)
            if distance > dragThreshold {
                isDragging = true
            }
        }

        let newOrigin = NSPoint(
            x: initialWindow.x + deltaX,
            y: initialWindow.y + deltaY
        )

        self.setFrameOrigin(newOrigin)
    }

    private func handleMouseUp(_ event: NSEvent) {
        // If not dragging, treat as click
        if !isDragging && initialMouseLocation != nil {
            onClick?()
        }

        // Reset drag state
        isDragging = false
        initialMouseLocation = nil
        initialWindowLocation = nil
    }

    private func handleRightMouseDown(_ event: NSEvent) {
        onRightClick?()
        showContextMenu(at: event.locationInWindow)
    }

    private func showContextMenu(at location: NSPoint) {
        let menu = NSMenu()
        menu.autoenablesItems = false

        // Status info
        let statusText = isRecording ? "Status: Recording" : "Status: Ready"
        let statusItem = NSMenuItem(title: statusText, action: nil, keyEquivalent: "")
        statusItem.isEnabled = false
        menu.addItem(statusItem)

        menu.addItem(NSMenuItem.separator())

        // Start/Stop Recording
        if isRecording {
            let stopItem = NSMenuItem(
                title: "⏹ Stop Recording",
                action: #selector(stopRecording),
                keyEquivalent: ""
            )
            stopItem.target = self
            menu.addItem(stopItem)

            let pauseText = isPaused ? "▶ Resume" : "⏸ Pause"
            let pauseItem = NSMenuItem(
                title: pauseText,
                action: #selector(togglePause),
                keyEquivalent: ""
            )
            pauseItem.target = self
            menu.addItem(pauseItem)
        } else {
            let startItem = NSMenuItem(
                title: "⏺ Start Recording",
                action: #selector(startRecording),
                keyEquivalent: ""
            )
            startItem.target = self
            menu.addItem(startItem)
        }

        menu.addItem(NSMenuItem.separator())

        // Quit
        let quitItem = NSMenuItem(
            title: "🚪 Quit MemScreen",
            action: #selector(quitApp),
            keyEquivalent: "q"
        )
        quitItem.target = self
        menu.addItem(quitItem)

        // Show menu
        menu.popUp(positioning: nil, at: location, in: self.ballView)
    }

    @objc private func startRecording() {
        flutterChannel?.invokeMethod("startRecording", arguments: nil)
    }

    @objc private func stopRecording() {
        flutterChannel?.invokeMethod("stopRecording", arguments: nil)
    }

    @objc private func togglePause() {
        flutterChannel?.invokeMethod("togglePause", arguments: nil)
    }

    @objc private func quitApp() {
        debugPrint("[FloatingBall] quitApp called - requesting app termination")

        // Close floating ball window
        self.close()

        // Use AppDelegate's forceQuit method for clean termination
        if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
            appDelegate.forceQuit()
        } else {
            // Fallback: direct termination
            NSApplication.shared.terminate(nil)
        }
    }

    func setRecordingState(_ recording: Bool) {
        isRecording = recording
        ballView.isRecording = recording
        ballView.needsDisplay = true
    }

    func setPausedState(_ paused: Bool) {
        isPaused = paused
        ballView.isPaused = paused
        ballView.needsDisplay = true
    }

    override func makeKeyAndOrderFront(_ sender: Any?) {
        self.level = .floating
        super.makeKeyAndOrderFront(sender)
    }
}

/// Custom view for drawing the floating ball
class FloatingBallView: NSView {
    var isRecording: Bool = false
    var isPaused: Bool = false

    var onMouseDown: ((NSEvent) -> Void)?
    var onMouseDragged: ((NSEvent) -> Void)?
    var onMouseUp: ((NSEvent) -> Void)?
    var onRightMouseDown: ((NSEvent) -> Void)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        let bounds = self.bounds

        // Draw outer glow
        let glowPath = NSBezierPath(ovalIn: bounds)
        let glowColor = NSColor(red: 0.6, green: 0.4, blue: 0.75, alpha: 0.3)
        glowColor.setFill()
        glowPath.fill()

        // Determine main color based on state
        let mainColor: NSColor
        if isPaused {
            mainColor = NSColor(red: 1.0, green: 0.7, blue: 0.2, alpha: 1.0)  // Yellow
        } else if isRecording {
            mainColor = NSColor(red: 0.8, green: 0.2, blue: 0.3, alpha: 1.0)  // Red
        } else {
            mainColor = NSColor(red: 0.6, green: 0.4, blue: 0.75, alpha: 1.0)  // Purple
        }

        // Draw main circle
        let clipRect = NSRect(
            x: 2,
            y: 2,
            width: bounds.width - 4,
            height: bounds.height - 4
        )
        let mainPath = NSBezierPath(ovalIn: clipRect)
        mainColor.setFill()
        mainPath.fill()

        // Draw border
        let borderColor = NSColor.white.withAlphaComponent(0.2)
        borderColor.setStroke()
        mainPath.lineWidth = 1.5
        mainPath.stroke()

        // Draw status icon
        drawStatusIcon(in: bounds)
    }

    private func drawStatusIcon(in bounds: NSRect) {
        NSColor.white.setFill()

        if isPaused {
            // Draw pause bars (II)
            let barWidth: CGFloat = 4
            let barHeight: CGFloat = 20
            let x1 = bounds.width / 2 - 6
            let x2 = bounds.width / 2 + 2
            let y = bounds.height / 2 - barHeight / 2

            let rect1 = NSRect(x: x1, y: y, width: barWidth, height: barHeight)
            let rect2 = NSRect(x: x2, y: y, width: barWidth, height: barHeight)

            NSBezierPath(rect: rect1).fill()
            NSBezierPath(rect: rect2).fill()
        } else if isRecording {
            // Draw recording dot (●)
            let dotSize: CGFloat = 16
            let dotRect = NSRect(
                x: (bounds.width - dotSize) / 2,
                y: (bounds.height - dotSize) / 2,
                width: dotSize,
                height: dotSize
            )
            NSBezierPath(ovalIn: dotRect).fill()
        } else {
            // Draw ready circle (○)
            let circleSize: CGFloat = 16
            let circleRect = NSRect(
                x: (bounds.width - circleSize) / 2,
                y: (bounds.height - circleSize) / 2,
                width: circleSize,
                height: circleSize
            )
            let circle = NSBezierPath(ovalIn: circleRect)
            circle.lineWidth = 2
            circle.stroke()
        }
    }

    override func mouseDown(with event: NSEvent) {
        onMouseDown?(event)
    }

    override func mouseDragged(with event: NSEvent) {
        onMouseDragged?(event)
    }

    override func mouseUp(with event: NSEvent) {
        onMouseUp?(event)
    }

    override func rightMouseDown(with event: NSEvent) {
        onRightMouseDown?(event)
    }
}
