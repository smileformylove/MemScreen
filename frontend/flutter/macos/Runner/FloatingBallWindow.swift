import Cocoa
import CoreGraphics
import FlutterMacOS

/// Native macOS floating ball window for MemScreen Flutter
class FloatingBallWindow: NSPanel {
    private var ballView: FloatingBallView!
    private var toolbarPanel: ToolbarPanel?
    private var regionSelector: RegionSelectionPanel?
    private var windowSelector: WindowSelectionPanel?
    private var flutterChannel: FlutterMethodChannel?

    // Store parent window reference to restore visibility
    private weak var parentWindowRef: NSWindow?

    // State
    var isRecording: Bool = false
    var isPaused: Bool = false
    var isTracking: Bool = false
    private var isToolbarExpanded: Bool = false
    private var selectedRegionForNextRecording: [Double]?
    private var selectedRegionScreenIndexForNextRecording: Int?
    private var consumeSelectedRegionOnRecordStart = false
    private var selectedWindowRegionForNextRecording: [Double]?
    private var selectedWindowSummaryForNextRecording: String?
    private var consumeSelectedWindowOnRecordStart = false
    private var selectedScreenIndexForNextRecording: Int?
    private var localKeyboardMonitor: Any?
    private var globalKeyboardMonitor: Any?

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
        installKeyboardShortcuts()
    }

    deinit {
        if let monitor = localKeyboardMonitor {
            NSEvent.removeMonitor(monitor)
            localKeyboardMonitor = nil
        }
        if let monitor = globalKeyboardMonitor {
            NSEvent.removeMonitor(monitor)
            globalKeyboardMonitor = nil
        }
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
        let toolbarHeight: CGFloat = 404
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
            onSelectWindow: { [weak self] in
                self?.selectWindowForNextRecording()
            },
            onToggleTracking: { [weak self] in
                self?.toggleTrackingFromToolbar()
            },
            onScreenSelectionChanged: { [weak self] screenIndex in
                self?.setSelectedScreenIndex(screenIndex)
            },
            onQuit: { [weak self] in
                self?.onQuit?()
            }
        )
        toolbarPanel?.setSelectedScreen(selectedScreenIndexForNextRecording)
        toolbarPanel?.setSelectedRegion(selectedRegionForNextRecording)
        toolbarPanel?.setSelectedWindow(selectedWindowSummaryForNextRecording)
        toolbarPanel?.updateRecordingState(isRecording)
        toolbarPanel?.updatePausedState(isPaused)
        toolbarPanel?.updateTrackingState(isTracking)

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
            selectedRegionScreenIndexForNextRecording = nil
            consumeSelectedRegionOnRecordStart = false
        } else if recording, consumeSelectedWindowOnRecordStart {
            selectedWindowRegionForNextRecording = nil
            selectedWindowSummaryForNextRecording = nil
            consumeSelectedWindowOnRecordStart = false
        } else if !recording {
            consumeSelectedRegionOnRecordStart = false
            consumeSelectedWindowOnRecordStart = false
        }
        ballView.isRecording = recording
        ballView.needsDisplay = true
        toolbarPanel?.updateRecordingState(recording)
        toolbarPanel?.setSelectedRegion(selectedRegionForNextRecording)
        toolbarPanel?.setSelectedWindow(selectedWindowSummaryForNextRecording)
    }

    func setPausedState(_ paused: Bool) {
        isPaused = paused
        ballView.isPaused = paused
        ballView.needsDisplay = true
        toolbarPanel?.updatePausedState(paused)
    }

    func setTrackingState(_ tracking: Bool) {
        isTracking = tracking
        toolbarPanel?.updateTrackingState(tracking)
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

        collapseToolbar()

        let screen = selectionScreen()
        let selectionScreenIndex = NSScreen.screens.firstIndex(where: { $0 == screen })
        regionSelector = RegionSelectionPanel(screen: screen) { [weak self] result in
            guard let self = self else { return }

            self.regionSelector = nil
            self.orderFront(nil)
            self.makeKeyAndOrderFront(nil)

            if case .cancelled = result {
                if shouldReopenToolbar {
                    self.expandToolbar()
                }
                self.toolbarPanel?.setSelectedRegion(self.selectedRegionForNextRecording)
                self.toolbarPanel?.showStatus("Status: Region selection cancelled", color: NSColor.secondaryLabelColor)
                return
            }

            guard case let .confirmed(selectedRegion) = result else {
                return
            }
            self.selectedWindowRegionForNextRecording = nil
            self.selectedWindowSummaryForNextRecording = nil
            self.consumeSelectedWindowOnRecordStart = false
            self.selectedRegionForNextRecording = selectedRegion
            self.selectedRegionScreenIndexForNextRecording = selectionScreenIndex
            self.consumeSelectedRegionOnRecordStart = true
            self.toolbarPanel?.setSelectedRegion(selectedRegion)
            self.toolbarPanel?.setSelectedWindow(nil)

            let width = Int(max(0, (selectedRegion[2] - selectedRegion[0]).rounded()))
            let height = Int(max(0, (selectedRegion[3] - selectedRegion[1]).rounded()))
            self.toolbarPanel?.showStatus("Status: Starting region \(width)x\(height)...", color: NSColor.systemBlue)
            self.invokeStartRecording(mode: "region", region: selectedRegion, screenIndex: selectionScreenIndex, windowTitle: nil)
        }
        regionSelector?.show()
    }

    func beginRegionSelectionFromMainUI() {
        if !self.isVisible {
            self.orderFront(nil)
            self.makeKeyAndOrderFront(nil)
        }
        selectRegionForNextRecording()
    }

    private func selectWindowForNextRecording() {
        guard !isRecording else {
            toolbarPanel?.showStatus("Status: Stop recording first", color: NSColor.systemOrange)
            return
        }

        let shouldReopenToolbar = isToolbarExpanded
        if let parentWindow = parentWindowRef, !parentWindow.isMiniaturized {
            parentWindow.miniaturize(nil)
        }

        collapseToolbar()

        let screen = selectionScreen()
        windowSelector = WindowSelectionPanel(screen: screen) { [weak self] result in
            guard let self = self else { return }
            self.windowSelector = nil

            self.orderFront(nil)
            self.makeKeyAndOrderFront(nil)

            if case .cancelled = result {
                if shouldReopenToolbar {
                    self.expandToolbar()
                }
                self.toolbarPanel?.setSelectedWindow(self.selectedWindowSummaryForNextRecording)
                self.toolbarPanel?.showStatus("Status: Window selection cancelled", color: NSColor.secondaryLabelColor)
                return
            }

            guard case let .confirmed(selectedRegion, summary) = result else {
                return
            }
            self.selectedRegionForNextRecording = nil
            self.selectedRegionScreenIndexForNextRecording = nil
            self.consumeSelectedRegionOnRecordStart = false
            self.selectedWindowRegionForNextRecording = selectedRegion
            self.selectedWindowSummaryForNextRecording = summary
            self.consumeSelectedWindowOnRecordStart = true
            self.toolbarPanel?.setSelectedRegion(nil)
            self.toolbarPanel?.setSelectedWindow(summary)

            self.toolbarPanel?.showStatus("Status: Starting \(summary)...", color: NSColor.systemBlue)
            self.invokeStartRecording(mode: "region", region: selectedRegion, screenIndex: nil, windowTitle: summary)
        }
        windowSelector?.show()
    }

    func beginWindowSelectionFromMainUI() {
        if !self.isVisible {
            self.orderFront(nil)
            self.makeKeyAndOrderFront(nil)
        }
        selectWindowForNextRecording()
    }

    func setSelectedScreenIndex(_ screenIndex: Int?) {
        if let idx = screenIndex, idx >= 0 {
            selectedScreenIndexForNextRecording = idx
        } else {
            selectedScreenIndexForNextRecording = nil
        }
        toolbarPanel?.setSelectedScreen(selectedScreenIndexForNextRecording)
    }

    private func toggleRecordingFromToolbar() {
        if isRecording {
            toolbarPanel?.showStatus("Status: Stopping recording...", color: NSColor.systemOrange)
            flutterChannel?.invokeMethod("stopRecording", arguments: nil)
            collapseToolbar()
            return
        }

        if let selectedRegion = selectedRegionForNextRecording {
            consumeSelectedRegionOnRecordStart = true
            let width = Int(max(0, (selectedRegion[2] - selectedRegion[0]).rounded()))
            let height = Int(max(0, (selectedRegion[3] - selectedRegion[1]).rounded()))
            toolbarPanel?.showStatus("Status: Starting region \(width)x\(height)...", color: NSColor.systemBlue)
            invokeStartRecording(mode: "region", region: selectedRegion, screenIndex: selectedRegionScreenIndexForNextRecording, windowTitle: nil)
            collapseToolbar()
            return
        }

        if let selectedWindowRegion = selectedWindowRegionForNextRecording {
            consumeSelectedWindowOnRecordStart = true
            let title = selectedWindowSummaryForNextRecording ?? "window"
            toolbarPanel?.showStatus("Status: Starting \(title)...", color: NSColor.systemBlue)
            invokeStartRecording(mode: "region", region: selectedWindowRegion, screenIndex: nil, windowTitle: selectedWindowSummaryForNextRecording)
            collapseToolbar()
            return
        }

        if let idx = selectedScreenIndexForNextRecording {
            toolbarPanel?.showStatus("Status: Starting screen \(idx + 1) recording...", color: NSColor.systemBlue)
            invokeStartRecording(mode: "fullscreen-single", region: nil, screenIndex: idx, windowTitle: nil)
        } else {
            toolbarPanel?.showStatus("Status: Starting full-screen recording...", color: NSColor.systemBlue)
            invokeStartRecording(mode: "fullscreen", region: nil, screenIndex: nil, windowTitle: nil)
        }
        collapseToolbar()
    }

    private func toggleTrackingFromToolbar() {
        if isTracking {
            toolbarPanel?.showStatus("Status: Stopping input tracking...", color: NSColor.systemOrange)
        } else {
            toolbarPanel?.showStatus("Status: Starting input tracking...", color: NSColor.systemBlue)
        }
        flutterChannel?.invokeMethod("toggleTracking", arguments: nil)
    }

    private func installKeyboardShortcuts() {
        localKeyboardMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self = self else { return event }
            if self.handleShortcutKeyDown(event) {
                return nil
            }
            return event
        }

        globalKeyboardMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self = self else { return }
            DispatchQueue.main.async {
                _ = self.handleShortcutKeyDown(event)
            }
        }
    }

    private func handleShortcutKeyDown(_ event: NSEvent) -> Bool {
        let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        guard flags.contains([.command, .shift]) else { return false }

        let key = shortcutKey(from: event)
        if key == "r" {
            selectRegionForNextRecording()
            return true
        }
        if key == "s" {
            toggleRecordingFromToolbar()
            return true
        }
        if key == "," {
            flutterChannel?.invokeMethod("openSettings", arguments: nil)
            collapseToolbar()
            return true
        }
        if key == "x" {
            onQuit?()
            return true
        }
        return false
    }

    private func shortcutKey(from event: NSEvent) -> String {
        switch event.keyCode {
        case 15: return "r"   // R
        case 1: return "s"    // S
        case 0: return "a"    // A
        case 13: return "w"   // W
        case 8: return "c"    // C
        case 9: return "v"    // V
        case 43: return ","   // Comma
        case 7: return "x"    // X
        case 40: return "k"   // K
        default:
            return event.charactersIgnoringModifiers?.lowercased() ?? ""
        }
    }

    private func selectionScreen() -> NSScreen {
        if let idx = selectedScreenIndexForNextRecording {
            let screens = NSScreen.screens
            if idx >= 0 && idx < screens.count {
                return screens[idx]
            }
        }
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

    private func invokeStartRecording(mode: String, region: [Double]?, screenIndex: Int?, windowTitle: String?) {
        var args: [String: Any] = ["mode": mode]
        if let region = region {
            args["region"] = region
        }
        if let screenIndex = screenIndex {
            args["screenIndex"] = screenIndex
        }
        if let windowTitle = windowTitle, !windowTitle.isEmpty {
            args["windowTitle"] = windowTitle
        }
        flutterChannel?.invokeMethod("startRecording", arguments: args)
    }

    override func close() {
        collapseToolbar()
        regionSelector?.orderOut(nil)
        regionSelector?.close()
        regionSelector = nil
        windowSelector?.orderOut(nil)
        windowSelector?.close()
        windowSelector = nil
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
    private var selectWindowButton: NSButton!
    private var trackingButton: NSButton!
    private var quickChatButton: NSButton!
    private var videosButton: NSButton!
    private var settingsButton: NSButton!
    private var quitButton: NSButton!
    private var screenPopup: NSPopUpButton!
    private var statusLabel: NSTextField?

    private var onToggleRecording: (() -> Void)?
    private var onSelectRegion: (() -> Void)?
    private var onSelectWindow: (() -> Void)?
    private var onToggleTracking: (() -> Void)?
    private var onScreenSelectionChanged: ((Int?) -> Void)?
    private var onQuit: (() -> Void)?
    private var currentRecording = false
    private var currentPaused = false
    private var currentTracking = false
    private var selectedRegionSummary: String?
    private var selectedWindowSummary: String?

    init(
        contentRect: NSRect,
        flutterChannel: FlutterMethodChannel?,
        onToggleRecording: @escaping () -> Void,
        onSelectRegion: @escaping () -> Void,
        onSelectWindow: @escaping () -> Void,
        onToggleTracking: @escaping () -> Void,
        onScreenSelectionChanged: @escaping (Int?) -> Void,
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
        self.onSelectWindow = onSelectWindow
        self.onToggleTracking = onToggleTracking
        self.onScreenSelectionChanged = onScreenSelectionChanged
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

        screenPopup = NSPopUpButton(
            frame: NSRect(x: 15, y: 308, width: 230, height: 30),
            pullsDown: false
        )
        screenPopup.font = NSFont.systemFont(ofSize: 12)
        screenPopup.target = self
        screenPopup.action = #selector(screenSelectionChanged)
        screenPopup.addItem(withTitle: "Screen: All Screens")
        screenPopup.lastItem?.tag = -1
        for (idx, screen) in NSScreen.screens.enumerated() {
            let suffix = screen == NSScreen.main ? " [Primary]" : ""
            screenPopup.addItem(withTitle: "Screen \(idx + 1)\(suffix)")
            screenPopup.lastItem?.tag = idx
        }
        containerView.addSubview(screenPopup)

        startStopButton = createActionButton(
            title: "⏺ Start Recording (⌘⇧S)",
            color: NSColor.systemRed,
            action: #selector(toggleRecording)
        )
        startStopButton.frame = NSRect(x: 15, y: 264, width: 230, height: 36)
        containerView.addSubview(startStopButton)

        selectRegionButton = createActionButton(
            title: "🎯 Select Region (⌘⇧R)",
            color: NSColor.systemPurple,
            action: #selector(selectRegionAndRecord)
        )
        selectRegionButton.frame = NSRect(x: 15, y: 224, width: 230, height: 36)
        containerView.addSubview(selectRegionButton)

        selectWindowButton = createActionButton(
            title: "🪟 Record App Window",
            color: NSColor.systemTeal,
            action: #selector(selectWindowAndRecord)
        )
        selectWindowButton.frame = NSRect(x: 15, y: 184, width: 230, height: 36)
        containerView.addSubview(selectWindowButton)

        trackingButton = createActionButton(
            title: "⌨️ Input Record",
            color: NSColor.systemIndigo,
            action: #selector(toggleTracking)
        )
        trackingButton.frame = NSRect(x: 15, y: 144, width: 230, height: 36)
        containerView.addSubview(trackingButton)

        // Quick Chat button
        quickChatButton = createActionButton(
            title: "💬 Quick Chat",
            color: NSColor.systemBlue,
            action: #selector(openQuickChat)
        )
        quickChatButton.frame = NSRect(x: 15, y: 104, width: 230, height: 36)
        containerView.addSubview(quickChatButton)

        // Videos button
        videosButton = createActionButton(
            title: "📁 Videos",
            color: NSColor.systemGreen,
            action: #selector(openVideos)
        )
        videosButton.frame = NSRect(x: 15, y: 64, width: 230, height: 36)
        containerView.addSubview(videosButton)

        // Settings button
        settingsButton = createActionButton(
            title: "⚙️ Settings (⌘⇧,)",
            color: NSColor.systemGray,
            action: #selector(openSettings)
        )
        settingsButton.frame = NSRect(x: 15, y: 19, width: 110, height: 36)
        containerView.addSubview(settingsButton)

        // Quit button
        quitButton = createActionButton(
            title: "🚪 Quit (⌘⇧X)",
            color: NSColor.systemRed,
            action: #selector(quitApp)
        )
        quitButton.frame = NSRect(x: 135, y: 19, width: 110, height: 36)
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

    @objc private func toggleTracking() {
        onToggleTracking?()
    }

    @objc private func selectRegionAndRecord() {
        if currentRecording {
            showStatus("Status: Stop recording before selecting region", color: NSColor.systemOrange)
            return
        }
        onSelectRegion?()
    }

    @objc private func selectWindowAndRecord() {
        if currentRecording {
            showStatus("Status: Stop recording before selecting app window", color: NSColor.systemOrange)
            return
        }
        onSelectWindow?()
    }

    @objc private func screenSelectionChanged() {
        let selectedTag = screenPopup.selectedTag()
        onScreenSelectionChanged?(selectedTag >= 0 ? selectedTag : nil)
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

    func updateTrackingState(_ isTracking: Bool) {
        currentTracking = isTracking
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

    func setSelectedWindow(_ summary: String?) {
        selectedWindowSummary = summary
        refreshStatus()
        refreshActionButtons()
    }

    func setSelectedScreen(_ screenIndex: Int?) {
        let tag = screenIndex ?? -1
        let idx = screenPopup.indexOfItem(withTag: tag)
        if idx >= 0 {
            screenPopup.selectItem(at: idx)
            return
        }
        let allIdx = screenPopup.indexOfItem(withTag: -1)
        if allIdx >= 0 {
            screenPopup.selectItem(at: allIdx)
        }
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
        if currentRecording && currentTracking {
            showStatus("Status: Recording + input tracking", color: NSColor.systemRed)
            return
        }
        if currentRecording {
            showStatus("Status: Recording", color: NSColor.systemRed)
            return
        }
        if currentTracking {
            showStatus("Status: Input tracking", color: NSColor.systemBlue)
            return
        }
        if let selectedRegionSummary = selectedRegionSummary {
            showStatus("Status: \(selectedRegionSummary) ready", color: NSColor.systemGreen)
            return
        }
        if let selectedWindowSummary = selectedWindowSummary {
            showStatus("Status: \(selectedWindowSummary) ready", color: NSColor.systemGreen)
            return
        }
        showStatus("Status: Ready")
    }

    private func refreshActionButtons() {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            if self.currentRecording {
                self.startStopButton.title = "⏹ Stop Recording (⌘⇧S)"
            } else if self.selectedRegionSummary != nil {
                self.startStopButton.title = "⏺ Start Region Recording (⌘⇧S)"
            } else if self.selectedWindowSummary != nil {
                self.startStopButton.title = "⏺ Start App Recording (⌘⇧S)"
            } else {
                self.startStopButton.title = "⏺ Start Recording (⌘⇧S)"
            }
            self.selectRegionButton.title = self.selectedRegionSummary == nil
                ? "🎯 Select Region (⌘⇧R)"
                : "🎯 Re-select Region (⌘⇧R)"
            self.selectWindowButton.title = self.selectedWindowSummary == nil
                ? "🪟 Record App Window"
                : "🪟 Re-select App Window"
            self.trackingButton.title = self.currentTracking
                ? "⌨️ Stop Input Record"
                : "⌨️ Input Record"
            self.selectRegionButton.isEnabled = !self.currentRecording
            self.selectRegionButton.alphaValue = self.currentRecording ? 0.6 : 1.0
            self.selectWindowButton.isEnabled = !self.currentRecording
            self.selectWindowButton.alphaValue = self.currentRecording ? 0.6 : 1.0
        }
    }
}

private enum RegionSelectionResult {
    case cancelled
    case confirmed([Double])
}

private enum WindowSelectionResult {
    case cancelled
    case confirmed([Double], String)
}

private class RegionSelectionPanel: NSPanel {
    private var selectionView: RegionSelectionView!
    private var onComplete: ((RegionSelectionResult) -> Void)?
    private var hasCompleted = false

    init(screen: NSScreen, onComplete: @escaping (RegionSelectionResult) -> Void) {
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
        hidesOnDeactivate = false

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

    private func finish(with result: RegionSelectionResult) {
        guard !hasCompleted else { return }
        hasCompleted = true
        orderOut(nil)
        close()
        onComplete?(result)
    }

    override func cancelOperation(_ sender: Any?) {
        finish(with: .cancelled)
    }
}

private struct CandidateWindow {
    let bounds: CGRect  // Global top-left coordinates from CGWindow API.
    let ownerName: String
    let windowName: String
    let ownerPID: pid_t
}

private class WindowSelectionPanel: NSPanel {
    private var selectionView: WindowSelectionView!
    private var onComplete: ((WindowSelectionResult) -> Void)?
    private var hasCompleted = false

    init(screen: NSScreen, onComplete: @escaping (WindowSelectionResult) -> Void) {
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
        hidesOnDeactivate = false

        let localFrame = NSRect(x: 0, y: 0, width: frame.width, height: frame.height)
        selectionView = WindowSelectionView(frame: localFrame, panelFrame: frame) { [weak self] result in
            self?.finish(with: result)
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

    private func finish(with result: WindowSelectionResult) {
        guard !hasCompleted else { return }
        hasCompleted = true
        orderOut(nil)
        close()
        onComplete?(result)
    }

    override func cancelOperation(_ sender: Any?) {
        finish(with: .cancelled)
    }
}

private class WindowSelectionView: NSView {
    private let panelFrame: NSRect
    private let completion: (WindowSelectionResult) -> Void
    private var windows: [CandidateWindow] = []
    private var selectedIndex: Int?
    private var confirmButtonRect: NSRect = .zero
    private var refreshTimer: Timer?
    private var lastSelectedBounds: CGRect?

    init(frame frameRect: NSRect, panelFrame: NSRect, completion: @escaping (WindowSelectionResult) -> Void) {
        self.panelFrame = panelFrame
        self.completion = completion
        super.init(frame: frameRect)
        wantsLayer = true
        refreshWindows(autoSelectTopMost: true)
        startRefreshLoop()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var acceptsFirstResponder: Bool { true }

    deinit {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        NSColor.black.withAlphaComponent(0.30).setFill()
        NSBezierPath(rect: dirtyRect).fill()

        if let idx = selectedIndex, idx >= 0, idx < windows.count {
            let win = windows[idx]
            let rect = localRect(for: win.bounds)
            if !rect.isEmpty {
                // Highlight only the current top/selected app window to avoid overlap clutter.
                let color: NSColor = .systemTeal
                color.withAlphaComponent(0.20).setFill()
                rect.fill()

                let border = NSBezierPath(rect: rect)
                border.lineWidth = 2.2
                color.withAlphaComponent(0.95).setStroke()
                border.stroke()
            }
            drawSelectedWindowTitle(windows[idx])
            drawConfirmButton(under: rect)
        } else {
            confirmButtonRect = .zero
            drawHint("Switch to target app or click its window to select")
        }
    }

    override func mouseDown(with event: NSEvent) {
        let location = convert(event.locationInWindow, from: nil)

        if !confirmButtonRect.isEmpty, confirmButtonRect.contains(location),
           let payload = selectedPayload() {
            completion(.confirmed(payload.region, payload.summary))
            return
        }

        refreshWindows(autoSelectTopMost: false)
        selectedIndex = topMostWindowIndex(at: location)
        if selectedIndex == nil {
            selectedIndex = topMostWindowIndex()
        }
        needsDisplay = true
    }

    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 {  // ESC
            completion(.cancelled)
            return
        }
        // Enter
        if event.keyCode == 36 || event.keyCode == 76 {
            if let payload = selectedPayload() {
                completion(.confirmed(payload.region, payload.summary))
            }
            return
        }
        // R: clear selection
        if event.charactersIgnoringModifiers?.lowercased() == "r" {
            selectedIndex = nil
            confirmButtonRect = .zero
            refreshWindows(autoSelectTopMost: true)
            needsDisplay = true
            return
        }
        super.keyDown(with: event)
    }

    private func startRefreshLoop() {
        refreshTimer?.invalidate()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] _ in
            self?.refreshWindows(autoSelectTopMost: true)
        }
    }

    private func refreshWindows(autoSelectTopMost: Bool) {
        let previousSummary = selectedSummary()
        let previousBounds = selectedWindowBounds()
        windows = loadCandidateWindows()
        if windows.isEmpty {
            selectedIndex = nil
            lastSelectedBounds = nil
            if !confirmButtonRect.isEmpty {
                confirmButtonRect = .zero
            }
            needsDisplay = true
            return
        }

        if autoSelectTopMost {
            selectedIndex = topMostWindowIndex()
        } else if let idx = selectedIndex, idx >= 0, idx < windows.count {
            // Keep existing selected index only if still valid after refresh.
            selectedIndex = idx
        } else {
            selectedIndex = topMostWindowIndex()
        }

        let currentSummary = selectedSummary()
        let currentBounds = selectedWindowBounds()
        if previousSummary != currentSummary || previousBounds != currentBounds {
            lastSelectedBounds = currentBounds
            needsDisplay = true
        }
    }

    private func selectedSummary() -> String? {
        guard let idx = selectedIndex, idx >= 0, idx < windows.count else { return nil }
        let win = windows[idx]
        if win.windowName.isEmpty {
            return win.ownerName
        }
        return "\(win.ownerName)::\(win.windowName)"
    }

    private func selectedWindowBounds() -> CGRect? {
        guard let idx = selectedIndex, idx >= 0, idx < windows.count else { return nil }
        return windows[idx].bounds
    }

    private func loadCandidateWindows() -> [CandidateWindow] {
        guard let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)
            as? [[String: Any]] else {
            return []
        }

        var out: [CandidateWindow] = []
        let selfPID = ProcessInfo.processInfo.processIdentifier
        for info in list {
            guard let layer = info[kCGWindowLayer as String] as? Int, layer == 0 else {
                continue
            }
            if let ownerPID = info[kCGWindowOwnerPID as String] as? NSNumber,
               ownerPID.int32Value == selfPID {
                continue
            }
            guard let boundsDict = info[kCGWindowBounds as String] as? NSDictionary,
                  let bounds = CGRect(dictionaryRepresentation: boundsDict) else {
                continue
            }

            if bounds.width < 120 || bounds.height < 80 {
                continue
            }

            let ownerName = (info[kCGWindowOwnerName as String] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            if ownerName.isEmpty || ownerName == "Window Server" {
                continue
            }
            let windowName = (info[kCGWindowName as String] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""

            let local = localRect(for: bounds)
            if local.intersection(self.bounds).isEmpty {
                continue
            }

            let pidValue = (info[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value ?? 0
            out.append(CandidateWindow(bounds: bounds, ownerName: ownerName, windowName: windowName, ownerPID: pidValue))
        }
        return out
    }

    private func localRect(for topLeftRect: CGRect) -> NSRect {
        let mainHeight = NSScreen.main?.frame.height ?? panelFrame.height
        let bottomY = mainHeight - (topLeftRect.origin.y + topLeftRect.height)
        return NSRect(
            x: topLeftRect.origin.x - panelFrame.origin.x,
            y: bottomY - panelFrame.origin.y,
            width: topLeftRect.width,
            height: topLeftRect.height
        )
    }

    private func topMostWindowIndex(at localPoint: NSPoint) -> Int? {
        for (idx, win) in windows.enumerated() {
            if localRect(for: win.bounds).contains(localPoint) {
                return idx
            }
        }
        return nil
    }

    private func topMostWindowIndex() -> Int? {
        for (idx, win) in windows.enumerated() {
            if !localRect(for: win.bounds).isEmpty {
                return idx
            }
        }
        return nil
    }

    private func selectedPayload() -> (region: [Double], summary: String)? {
        guard let idx = selectedIndex, idx >= 0, idx < windows.count else {
            return nil
        }
        let win = windows[idx]
        let bounds = win.bounds
        let region: [Double] = [
            Double(floor(bounds.origin.x)),
            Double(floor(bounds.origin.y)),
            Double(ceil(bounds.origin.x + bounds.width)),
            Double(ceil(bounds.origin.y + bounds.height))
        ]
        let summary: String
        if win.windowName.isEmpty {
            summary = "Window: \(win.ownerName)"
        } else {
            summary = "Window: \(win.ownerName) · \(win.windowName)"
        }
        return (region, summary)
    }

    private func drawSelectedWindowTitle(_ win: CandidateWindow) {
        let text: String
        if win.windowName.isEmpty {
            text = "Selected: \(win.ownerName)"
        } else {
            text = "Selected: \(win.ownerName) · \(win.windowName)"
        }
        drawHint(text)
    }

    private func drawHint(_ text: String) {
        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 14, weight: .semibold),
            .foregroundColor: NSColor.white.withAlphaComponent(0.92)
        ]
        let size = text.size(withAttributes: attrs)
        let point = NSPoint(x: max(12, bounds.midX - size.width / 2), y: bounds.height - size.height - 20)
        text.draw(at: point, withAttributes: attrs)
    }

    private func drawConfirmButton(under rect: NSRect) {
        guard selectedIndex != nil else {
            confirmButtonRect = .zero
            return
        }

        let width: CGFloat = 190
        let height: CGFloat = 34
        let x = min(max(rect.midX - width / 2, 12), bounds.width - width - 12)
        let y = max(rect.minY - height - 10, 12)
        confirmButtonRect = NSRect(x: x, y: y, width: width, height: height)

        let buttonPath = NSBezierPath(roundedRect: confirmButtonRect, xRadius: 8, yRadius: 8)
        NSColor.systemGreen.withAlphaComponent(0.92).setFill()
        buttonPath.fill()

        NSColor.white.withAlphaComponent(0.95).setStroke()
        buttonPath.lineWidth = 1.2
        buttonPath.stroke()

        let title = "✅ Confirm Recording (Enter)"
        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 13, weight: .semibold),
            .foregroundColor: NSColor.white
        ]
        let size = title.size(withAttributes: attrs)
        let textPoint = NSPoint(
            x: confirmButtonRect.midX - size.width / 2,
            y: confirmButtonRect.midY - size.height / 2
        )
        title.draw(at: textPoint, withAttributes: attrs)

        let hint = "ESC Cancel · R Reselect"
        let hintAttrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 11, weight: .regular),
            .foregroundColor: NSColor.white.withAlphaComponent(0.85)
        ]
        let hintSize = hint.size(withAttributes: hintAttrs)
        hint.draw(
            at: NSPoint(
                x: confirmButtonRect.midX - hintSize.width / 2,
                y: confirmButtonRect.minY - hintSize.height - 6
            ),
            withAttributes: hintAttrs
        )
    }
}

private class RegionSelectionView: NSView {
    private let minSelectionSize: CGFloat = 10
    private var startPoint: NSPoint?
    private var currentPoint: NSPoint?
    private let panelFrame: NSRect
    private let completion: (RegionSelectionResult) -> Void
    private var lastConfirmedRegion: [Double]?
    private var confirmButtonRect: NSRect = .zero

    init(frame frameRect: NSRect, panelFrame: NSRect, completion: @escaping (RegionSelectionResult) -> Void) {
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

        drawConfirmButton(under: rect)
    }

    override func mouseDown(with event: NSEvent) {
        let location = convert(event.locationInWindow, from: nil)
        if !confirmButtonRect.isEmpty, confirmButtonRect.contains(location), let region = lastConfirmedRegion {
            completion(.confirmed(region))
            return
        }
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
        let location = convert(event.locationInWindow, from: nil)
        if !confirmButtonRect.isEmpty, confirmButtonRect.contains(location), let region = lastConfirmedRegion {
            completion(.confirmed(region))
            return
        }
        finalizeSelection()
    }

    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 {  // ESC
            completion(.cancelled)
            return
        }
        // Enter: confirm and start recording
        if event.keyCode == 36 || event.keyCode == 76 {
            if let region = lastConfirmedRegion {
                completion(.confirmed(region))
            }
            return
        }
        // R: clear current selection and reselect
        if event.charactersIgnoringModifiers?.lowercased() == "r" {
            startPoint = nil
            currentPoint = nil
            lastConfirmedRegion = nil
            confirmButtonRect = .zero
            needsDisplay = true
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
            completion(.cancelled)
            return
        }

        guard rect.width >= minSelectionSize, rect.height >= minSelectionSize else {
            startPoint = nil
            currentPoint = nil
            lastConfirmedRegion = nil
            confirmButtonRect = .zero
            needsDisplay = true
            return
        }

        // Return region in screen-local top-left coordinates.
        // Backend will map it onto the selected screen using screen_index.
        let x1 = rect.minX
        let x2 = rect.maxX
        let top = panelFrame.height - rect.maxY
        let bottom = panelFrame.height - rect.minY

        let region: [Double] = [
            Double(floor(x1)),
            Double(floor(top)),
            Double(ceil(x2)),
            Double(ceil(bottom))
        ]
        lastConfirmedRegion = region
        needsDisplay = true
    }

    private func drawConfirmButton(under rect: NSRect) {
        guard lastConfirmedRegion != nil else {
            confirmButtonRect = .zero
            return
        }

        let width: CGFloat = 190
        let height: CGFloat = 34
        let x = min(max(rect.midX - width / 2, 12), bounds.width - width - 12)
        let y = max(rect.minY - height - 10, 12)
        confirmButtonRect = NSRect(x: x, y: y, width: width, height: height)

        let buttonPath = NSBezierPath(roundedRect: confirmButtonRect, xRadius: 8, yRadius: 8)
        NSColor.systemGreen.withAlphaComponent(0.92).setFill()
        buttonPath.fill()

        NSColor.white.withAlphaComponent(0.95).setStroke()
        buttonPath.lineWidth = 1.2
        buttonPath.stroke()

        let title = "✅ Confirm Recording (Enter)"
        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 13, weight: .semibold),
            .foregroundColor: NSColor.white
        ]
        let size = title.size(withAttributes: attrs)
        let textPoint = NSPoint(
            x: confirmButtonRect.midX - size.width / 2,
            y: confirmButtonRect.midY - size.height / 2
        )
        title.draw(at: textPoint, withAttributes: attrs)

        let hint = "ESC Cancel · R Reselect"
        let hintAttrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 11, weight: .regular),
            .foregroundColor: NSColor.white.withAlphaComponent(0.85)
        ]
        let hintSize = hint.size(withAttributes: hintAttrs)
        hint.draw(
            at: NSPoint(
                x: confirmButtonRect.midX - hintSize.width / 2,
                y: confirmButtonRect.minY - hintSize.height - 6
            ),
            withAttributes: hintAttrs
        )
    }
}

/// Custom view for drawing the floating ball
class FloatingBallView: NSView {
    var isRecording: Bool = false
    var isPaused: Bool = false
    var isToolbarExpanded: Bool = false
    private lazy var logoImage: NSImage? = {
        if let image = NSImage(named: "FloatingBallLogo") {
            return image
        }
        if let icon = NSApp.applicationIconImage {
            return icon
        }
        if let named = NSImage(named: NSImage.applicationIconName) {
            return named
        }
        return nil
    }()

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

        // Draw outer glow and state ring
        let ringColor: NSColor
        if isPaused {
            ringColor = NSColor.systemOrange
        } else if isRecording {
            ringColor = NSColor.systemRed
        } else {
            ringColor = NSColor.white
        }

        let glowAlpha: CGFloat = isToolbarExpanded ? 0.45 : 0.25
        let glowPath = NSBezierPath(ovalIn: bounds)
        let glowColor = ringColor.withAlphaComponent(glowAlpha)
        glowColor.setFill()
        glowPath.fill()

        let clipRect = NSRect(
            x: 2,
            y: 2,
            width: bounds.width - 4,
            height: bounds.height - 4
        )
        let mainPath = NSBezierPath(ovalIn: clipRect)
        NSGraphicsContext.saveGraphicsState()
        mainPath.addClip()
        if let logo = logoImage {
            logo.draw(in: clipRect, from: .zero, operation: .sourceOver, fraction: 1.0)
        } else {
            ringColor.setFill()
            mainPath.fill()
        }
        NSGraphicsContext.restoreGraphicsState()

        // Draw border ring
        let borderColor = ringColor.withAlphaComponent(0.9)
        borderColor.setStroke()
        mainPath.lineWidth = 2.0
        mainPath.stroke()

        // Draw toolbar expansion indicator
        if isToolbarExpanded {
            drawExpansionIndicator(in: bounds)
        } else {
            drawStateBadge(in: bounds)
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

    private func drawStateBadge(in bounds: NSRect) {
        let badgeSize: CGFloat = 14
        let badgeRect = NSRect(
            x: bounds.maxX - badgeSize - 5,
            y: 5,
            width: badgeSize,
            height: badgeSize
        )

        let badgeColor: NSColor
        if isPaused {
            badgeColor = NSColor.systemOrange
        } else if isRecording {
            badgeColor = NSColor.systemRed
        } else {
            badgeColor = NSColor.systemGreen
        }

        NSColor.white.withAlphaComponent(0.9).setStroke()
        let path = NSBezierPath(ovalIn: badgeRect)
        path.lineWidth = 1.3
        badgeColor.setFill()
        path.fill()
        path.stroke()
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
