import Cocoa
import FlutterMacOS

/// Native macOS floating ball window for MemScreen Flutter
class FloatingBallWindow: NSPanel {
    private var ballView: FloatingBallView!
    private var toolbarPanel: ToolbarPanel?
    private var regionSelector: RegionSelectionPanel?
    private var flutterChannel: FlutterMethodChannel?

    // Store parent window reference to restore visibility
    private weak var parentWindowRef: NSWindow?

    // State
    var isRecording: Bool = false
    var isPaused: Bool = false
    private var isToolbarExpanded: Bool = false
    private var selectedRegionForNextRecording: [Double]?
    private var consumeSelectedRegionOnRecordStart = false

    // Drag state
    private var initialMouseLocation: NSPoint?
    private var initialWindowLocation: NSPoint?
    private var isDragging: Bool = false
    private let dragThreshold: CGFloat = 5.0

    // Callbacks
    var onClick: (() -> Void)?
    var onQuit: (() -> Void)?

    init(contentRect: NSRect, flutterChannel: FlutterMethodChannel?, parentWindow: NSWindow?) {
        super.init(
            contentRect: contentRect,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )

        self.flutterChannel = flutterChannel
        self.parentWindowRef = parentWindow

        // Configure window properties
        self.level = .popUpMenu  // Higher than floating for better visibility
        self.isOpaque = false
        self.backgroundColor = .clear
        self.isMovableByWindowBackground = true

        // Configure panel behavior to NOT show in dock
        self.isFloatingPanel = true
        self.becomesKeyOnlyIfNeeded = true

        // Use ignoresCycle to prevent dock icon and cmd+tab cycling
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]

        // Create ball view in window-local coordinates.
        // Using global `contentRect` here makes the view render outside the panel.
        self.ballView = FloatingBallView(
            frame: NSRect(x: 0, y: 0, width: contentRect.width, height: contentRect.height)
        )
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

        // Close toolbar if clicking on ball
        if isToolbarExpanded {
            collapseToolbar()
        }
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
                // Close toolbar when dragging
                if isToolbarExpanded {
                    collapseToolbar()
                }
            }
        }

        let newOrigin = NSPoint(
            x: initialWindow.x + deltaX,
            y: initialWindow.y + deltaY
        )

        self.setFrameOrigin(newOrigin)

        // Update toolbar position if expanded
        if isToolbarExpanded {
            updateToolbarPosition()
        }
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
        // Toggle toolbar instead of showing context menu
        if isToolbarExpanded {
            collapseToolbar()
        } else {
            expandToolbar()
        }
    }

    private func expandToolbar() {
        guard toolbarPanel == nil else { return }

        let ballFrame = self.frame
        let toolbarWidth: CGFloat = 260
        let toolbarHeight: CGFloat = 280
        let padding: CGFloat = 10

        // Position toolbar to the left of the ball (or right if no space)
        var toolbarX = ballFrame.origin.x - toolbarWidth - padding

        if toolbarX < 0 {
            toolbarX = ballFrame.origin.x + ballFrame.width + padding
        }

        let toolbarY = ballFrame.origin.y + (ballFrame.height - toolbarHeight) / 2

        let toolbarRect = NSRect(x: toolbarX, y: toolbarY, width: toolbarWidth, height: toolbarHeight)

        toolbarPanel = ToolbarPanel(
            contentRect: toolbarRect,
            flutterChannel: flutterChannel,
            onToggleRecording: { [weak self] in
                self?.toggleRecordingFromToolbar()
            },
            onSelectRegion: { [weak self] in
                self?.selectRegionForNextRecording()
            },
            onQuit: { [weak self] in
                self?.onQuit?()
            }
        )
        toolbarPanel?.setSelectedRegion(selectedRegionForNextRecording)
        toolbarPanel?.updateRecordingState(isRecording)
        toolbarPanel?.updatePausedState(isPaused)

        toolbarPanel?.makeKeyAndOrderFront(nil)
        isToolbarExpanded = true
        ballView.isToolbarExpanded = true
        ballView.needsDisplay = true
    }

    private func collapseToolbar() {
        toolbarPanel?.close()
        toolbarPanel = nil
        isToolbarExpanded = false
        ballView.isToolbarExpanded = false
        ballView.needsDisplay = true
    }

    private func updateToolbarPosition() {
        guard let toolbar = toolbarPanel else { return }

        let ballFrame = self.frame
        let padding: CGFloat = 10

        var toolbarX = ballFrame.origin.x - toolbar.frame.width - padding

        if toolbarX < 0 {
            toolbarX = ballFrame.origin.x + ballFrame.width + padding
        }

        let toolbarY = ballFrame.origin.y + (ballFrame.height - toolbar.frame.height) / 2

        toolbar.setFrameOrigin(NSPoint(x: toolbarX, y: toolbarY))
    }

    func setRecordingState(_ recording: Bool) {
        isRecording = recording
        if recording, consumeSelectedRegionOnRecordStart {
            selectedRegionForNextRecording = nil
            consumeSelectedRegionOnRecordStart = false
        } else if !recording {
            consumeSelectedRegionOnRecordStart = false
        }
        ballView.isRecording = recording
        ballView.needsDisplay = true
        toolbarPanel?.updateRecordingState(recording)
        toolbarPanel?.setSelectedRegion(selectedRegionForNextRecording)
    }

    func setPausedState(_ paused: Bool) {
        isPaused = paused
        ballView.isPaused = paused
        ballView.needsDisplay = true
        toolbarPanel?.updatePausedState(paused)
    }

    private func selectRegionForNextRecording() {
        guard !isRecording else {
            toolbarPanel?.showStatus("Status: Stop recording first", color: NSColor.systemOrange)
            return
        }

        let shouldReopenToolbar = isToolbarExpanded
        if let parentWindow = parentWindowRef, !parentWindow.isMiniaturized {
            parentWindow.miniaturize(nil)
        }

        let previousVisibility = self.isVisible
        collapseToolbar()
        self.orderOut(nil)

        let screen = selectionScreen()
        regionSelector = RegionSelectionPanel(screen: screen) { [weak self] region in
            guard let self = self else { return }

            self.regionSelector = nil
            if previousVisibility {
                self.orderFront(nil)
                self.makeKeyAndOrderFront(nil)
            }

            if shouldReopenToolbar {
                self.expandToolbar()
            }

            guard let selectedRegion = region else {
                self.toolbarPanel?.setSelectedRegion(self.selectedRegionForNextRecording)
                self.toolbarPanel?.showStatus("Status: Region selection cancelled", color: NSColor.secondaryLabelColor)
                return
            }

            self.selectedRegionForNextRecording = selectedRegion
            self.consumeSelectedRegionOnRecordStart = false
            self.toolbarPanel?.setSelectedRegion(selectedRegion)

            let width = Int(max(0, (selectedRegion[2] - selectedRegion[0]).rounded()))
            let height = Int(max(0, (selectedRegion[3] - selectedRegion[1]).rounded()))
            self.toolbarPanel?.showStatus("Status: Region \(width)x\(height) ready", color: NSColor.systemGreen)
        }
        regionSelector?.show()
    }

    private func toggleRecordingFromToolbar() {
        if isRecording {
            toolbarPanel?.showStatus("Status: Stopping recording...", color: NSColor.systemOrange)
            flutterChannel?.invokeMethod("stopRecording", arguments: nil)
            return
        }

        if let selectedRegion = selectedRegionForNextRecording {
            consumeSelectedRegionOnRecordStart = true
            let width = Int(max(0, (selectedRegion[2] - selectedRegion[0]).rounded()))
            let height = Int(max(0, (selectedRegion[3] - selectedRegion[1]).rounded()))
            toolbarPanel?.showStatus("Status: Starting region \(width)x\(height)...", color: NSColor.systemBlue)
            invokeStartRecording(mode: "region", region: selectedRegion, screenIndex: nil)
            return
        }

        toolbarPanel?.showStatus("Status: Starting full-screen recording...", color: NSColor.systemBlue)
        invokeStartRecording(mode: "fullscreen", region: nil, screenIndex: nil)
    }

    private func selectionScreen() -> NSScreen {
        let mouseLocation = NSEvent.mouseLocation
        for screen in NSScreen.screens {
            if screen.frame.contains(mouseLocation) {
                return screen
            }
        }
        if let parentScreen = parentWindowRef?.screen {
            return parentScreen
        }
        return NSScreen.main ?? NSScreen.screens.first!
    }

    private func invokeStartRecording(mode: String, region: [Double]?, screenIndex: Int?) {
        var args: [String: Any] = ["mode": mode]
        if let region = region {
            args["region"] = region
        }
        if let screenIndex = screenIndex {
            args["screenIndex"] = screenIndex
        }
        flutterChannel?.invokeMethod("startRecording", arguments: args)
    }

    override func close() {
        collapseToolbar()
        regionSelector?.orderOut(nil)
        regionSelector?.close()
        regionSelector = nil
        super.close()
    }

    override func makeKeyAndOrderFront(_ sender: Any?) {
        self.level = .floating
        super.makeKeyAndOrderFront(sender)
    }
}

/// Toolbar panel showing quick action buttons
class ToolbarPanel: NSPanel {
    private var flutterChannel: FlutterMethodChannel?

    private var startStopButton: NSButton!
    private var selectRegionButton: NSButton!
    private var quickChatButton: NSButton!
    private var videosButton: NSButton!
    private var settingsButton: NSButton!
    private var quitButton: NSButton!
    private var statusLabel: NSTextField?

    private var onToggleRecording: (() -> Void)?
    private var onSelectRegion: (() -> Void)?
    private var onQuit: (() -> Void)?
    private var currentRecording = false
    private var currentPaused = false
    private var selectedRegionSummary: String?

    init(
        contentRect: NSRect,
        flutterChannel: FlutterMethodChannel?,
        onToggleRecording: @escaping () -> Void,
        onSelectRegion: @escaping () -> Void,
        onQuit: @escaping () -> Void
    ) {
        super.init(
            contentRect: contentRect,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )

        self.flutterChannel = flutterChannel
        self.onToggleRecording = onToggleRecording
        self.onSelectRegion = onSelectRegion
        self.onQuit = onQuit

        self.level = .popUpMenu  // Higher than floating for better visibility
        self.isOpaque = false
        self.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.95)
        self.isMovableByWindowBackground = false

        self.isFloatingPanel = true
        self.becomesKeyOnlyIfNeeded = true
        // Use ignoresCycle to prevent dock icon
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]

        // Setup content view
        setupUI()
    }

    private func setupUI() {
        let containerView = NSView(frame: self.contentView!.bounds)
        containerView.wantsLayer = true
        containerView.layer?.cornerRadius = 12
        containerView.layer?.masksToBounds = true

        // Title
        let titleLabel = NSTextField(labelWithString: "MemScreen")
        titleLabel.font = NSFont.systemFont(ofSize: 16, weight: .bold)
        titleLabel.textColor = NSColor.controlTextColor
        titleLabel.alignment = .center
        titleLabel.frame = NSRect(x: 0, y: containerView.bounds.height - 35, width: containerView.bounds.width, height: 25)
        containerView.addSubview(titleLabel)

        statusLabel = NSTextField(labelWithString: "Status: Ready")
        statusLabel?.font = NSFont.systemFont(ofSize: 11)
        statusLabel?.textColor = NSColor.secondaryLabelColor
        statusLabel?.alignment = .center
        statusLabel?.frame = NSRect(x: 0, y: containerView.bounds.height - 55, width: containerView.bounds.width, height: 16)
        if let statusLabel = statusLabel {
            containerView.addSubview(statusLabel)
        }

        startStopButton = createActionButton(
            title: "⏺ Start Recording",
            color: NSColor.systemRed,
            action: #selector(toggleRecording)
        )
        startStopButton.frame = NSRect(x: 15, y: 185, width: 230, height: 36)
        containerView.addSubview(startStopButton)

        selectRegionButton = createActionButton(
            title: "🎯 Select Region",
            color: NSColor.systemPurple,
            action: #selector(selectRegionAndRecord)
        )
        selectRegionButton.frame = NSRect(x: 15, y: 145, width: 230, height: 36)
        containerView.addSubview(selectRegionButton)

        // Quick Chat button
        quickChatButton = createActionButton(
            title: "💬 Quick Chat",
            color: NSColor.systemBlue,
            action: #selector(openQuickChat)
        )
        quickChatButton.frame = NSRect(x: 15, y: 105, width: 230, height: 36)
        containerView.addSubview(quickChatButton)

        // Videos button
        videosButton = createActionButton(
            title: "📁 Videos",
            color: NSColor.systemGreen,
            action: #selector(openVideos)
        )
        videosButton.frame = NSRect(x: 15, y: 65, width: 230, height: 36)
        containerView.addSubview(videosButton)

        // Settings button
        settingsButton = createActionButton(
            title: "⚙️ Settings",
            color: NSColor.systemGray,
            action: #selector(openSettings)
        )
        settingsButton.frame = NSRect(x: 15, y: 20, width: 110, height: 36)
        containerView.addSubview(settingsButton)

        // Quit button
        quitButton = createActionButton(
            title: "🚪 Quit",
            color: NSColor.systemRed,
            action: #selector(quitApp)
        )
        quitButton.frame = NSRect(x: 135, y: 20, width: 110, height: 36)
        containerView.addSubview(quitButton)

        self.contentView = containerView
    }

    private func createActionButton(title: String, color: NSColor, action: Selector) -> NSButton {
        let button = NSButton(title: title, target: self, action: action)
        button.bezelStyle = .rounded
        button.wantsLayer = true
        button.layer?.backgroundColor = color.withAlphaComponent(0.15).cgColor
        button.layer?.cornerRadius = 8
        button.font = NSFont.systemFont(ofSize: 13, weight: .medium)
        return button
    }

    @objc private func openQuickChat() {
        flutterChannel?.invokeMethod("openQuickChat", arguments: nil)
    }

    @objc private func openVideos() {
        flutterChannel?.invokeMethod("openVideos", arguments: nil)
    }

    @objc private func openSettings() {
        flutterChannel?.invokeMethod("openSettings", arguments: nil)
    }

    @objc private func quitApp() {
        if let onQuit = onQuit {
            onQuit()
        } else {
            flutterChannel?.invokeMethod("quitApp", arguments: nil)
        }
    }

    @objc private func toggleRecording() {
        onToggleRecording?()
    }

    @objc private func selectRegionAndRecord() {
        if currentRecording {
            showStatus("Status: Stop recording before selecting region", color: NSColor.systemOrange)
            return
        }
        onSelectRegion?()
    }

    func updateRecordingState(_ isRecording: Bool) {
        currentRecording = isRecording
        if !isRecording {
            currentPaused = false
        }
        refreshStatus()
        refreshActionButtons()
    }

    func updatePausedState(_ isPaused: Bool) {
        currentPaused = isPaused
        refreshStatus()
        refreshActionButtons()
    }

    func setSelectedRegion(_ region: [Double]?) {
        guard let region = region, region.count == 4 else {
            selectedRegionSummary = nil
            refreshStatus()
            refreshActionButtons()
            return
        }

        let width = Int(max(0, (region[2] - region[0]).rounded()))
        let height = Int(max(0, (region[3] - region[1]).rounded()))
        selectedRegionSummary = "Region \(width)x\(height)"
        refreshStatus()
        refreshActionButtons()
    }

    func showStatus(_ text: String, color: NSColor = NSColor.secondaryLabelColor) {
        DispatchQueue.main.async { [weak self] in
            self?.statusLabel?.stringValue = text
            self?.statusLabel?.textColor = color
        }
    }

    private func refreshStatus() {
        if currentPaused {
            showStatus("Status: Paused", color: NSColor.systemOrange)
            return
        }
        if currentRecording {
            showStatus("Status: Recording", color: NSColor.systemRed)
            return
        }
        if let selectedRegionSummary = selectedRegionSummary {
            showStatus("Status: \(selectedRegionSummary) ready", color: NSColor.systemGreen)
            return
        }
        showStatus("Status: Ready")
    }

    private func refreshActionButtons() {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            if self.currentRecording {
                self.startStopButton.title = "⏹ Stop Recording"
            } else if self.selectedRegionSummary != nil {
                self.startStopButton.title = "⏺ Start Region Recording"
            } else {
                self.startStopButton.title = "⏺ Start Recording"
            }
            self.selectRegionButton.title = self.selectedRegionSummary == nil ? "🎯 Select Region" : "🎯 Re-select Region"
            self.selectRegionButton.isEnabled = !self.currentRecording
            self.selectRegionButton.alphaValue = self.currentRecording ? 0.6 : 1.0
        }
    }
}

private class RegionSelectionPanel: NSPanel {
    private var selectionView: RegionSelectionView!
    private var onComplete: (([Double]?) -> Void)?
    private var hasCompleted = false

    init(screen: NSScreen, onComplete: @escaping ([Double]?) -> Void) {
        let frame = screen.frame
        super.init(
            contentRect: frame,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )

        self.onComplete = onComplete

        level = .screenSaver
        isOpaque = false
        backgroundColor = .clear
        hasShadow = false
        ignoresMouseEvents = false
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]

        let localFrame = NSRect(x: 0, y: 0, width: frame.width, height: frame.height)
        selectionView = RegionSelectionView(frame: localFrame, panelFrame: frame) { [weak self] region in
            self?.finish(with: region)
        }
        contentView = selectionView
    }

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

    func show() {
        makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        makeFirstResponder(selectionView)
    }

    private func finish(with region: [Double]?) {
        guard !hasCompleted else { return }
        hasCompleted = true
        orderOut(nil)
        close()
        onComplete?(region)
    }

    override func cancelOperation(_ sender: Any?) {
        finish(with: nil)
    }
}

private class RegionSelectionView: NSView {
    private let minSelectionSize: CGFloat = 10
    private var startPoint: NSPoint?
    private var currentPoint: NSPoint?
    private let panelFrame: NSRect
    private let completion: ([Double]?) -> Void

    init(frame frameRect: NSRect, panelFrame: NSRect, completion: @escaping ([Double]?) -> Void) {
        self.panelFrame = panelFrame
        self.completion = completion
        super.init(frame: frameRect)
        wantsLayer = true
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var acceptsFirstResponder: Bool { true }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        NSColor.black.withAlphaComponent(0.30).setFill()
        NSBezierPath(rect: dirtyRect).fill()

        guard let rect = selectionRect else { return }

        NSColor.systemPurple.withAlphaComponent(0.25).setFill()
        rect.fill()

        let borderPath = NSBezierPath(rect: rect)
        borderPath.lineWidth = 2
        NSColor.systemPurple.withAlphaComponent(0.95).setStroke()
        borderPath.stroke()
    }

    override func mouseDown(with event: NSEvent) {
        let location = convert(event.locationInWindow, from: nil)
        startPoint = location
        currentPoint = location
        needsDisplay = true
    }

    override func mouseDragged(with event: NSEvent) {
        currentPoint = convert(event.locationInWindow, from: nil)
        needsDisplay = true
    }

    override func mouseUp(with event: NSEvent) {
        currentPoint = convert(event.locationInWindow, from: nil)
        finalizeSelection()
    }

    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 {  // ESC
            completion(nil)
            return
        }
        super.keyDown(with: event)
    }

    private var selectionRect: NSRect? {
        guard let start = startPoint, let current = currentPoint else { return nil }
        return NSRect(
            x: min(start.x, current.x),
            y: min(start.y, current.y),
            width: abs(start.x - current.x),
            height: abs(start.y - current.y)
        )
    }

    private func finalizeSelection() {
        guard let rect = selectionRect else {
            completion(nil)
            return
        }

        guard rect.width >= minSelectionSize, rect.height >= minSelectionSize else {
            completion(nil)
            return
        }

        let x1 = panelFrame.origin.x + rect.minX
        let x2 = panelFrame.origin.x + rect.maxX
        let y1 = panelFrame.origin.y + rect.minY
        let y2 = panelFrame.origin.y + rect.maxY

        let mainHeight = NSScreen.main?.frame.height ?? panelFrame.height
        let top = mainHeight - y2
        let bottom = mainHeight - y1

        let region: [Double] = [
            Double(floor(x1)),
            Double(floor(top)),
            Double(ceil(x2)),
            Double(ceil(bottom))
        ]
        completion(region)
    }
}

/// Custom view for drawing the floating ball
class FloatingBallView: NSView {
    var isRecording: Bool = false
    var isPaused: Bool = false
    var isToolbarExpanded: Bool = false

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

        // Draw outer glow with animation hint when toolbar is expanded
        let glowAlpha: CGFloat = isToolbarExpanded ? 0.5 : 0.3
        let glowPath = NSBezierPath(ovalIn: bounds)
        let glowColor = NSColor(red: 0.6, green: 0.4, blue: 0.75, alpha: glowAlpha)
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

        // Draw toolbar expansion indicator
        if isToolbarExpanded {
            drawExpansionIndicator(in: bounds)
        } else {
            // Draw status icon
            drawStatusIcon(in: bounds)
        }
    }

    private func drawExpansionIndicator(in bounds: NSRect) {
        // Draw small dots menu icon (···)
        NSColor.white.setFill()

        let dotSize: CGFloat = 6
        let spacing: CGFloat = 10
        let startX = (bounds.width - (dotSize * 3 + spacing * 2)) / 2
        let y = bounds.height / 2 - dotSize / 2

        for i in 0..<3 {
            let dotRect = NSRect(
                x: startX + CGFloat(i) * (dotSize + spacing),
                y: y,
                width: dotSize,
                height: dotSize
            )
            NSBezierPath(ovalIn: dotRect).fill()
        }
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
