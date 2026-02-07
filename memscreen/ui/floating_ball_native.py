#!/usr/bin/env python3
"""
Native macOS Floating Ball Window - Fixed Version
Uses PyObjC to create a real floating window that stays on top of the main window
"""

import sys
from typing import Optional, Callable

# Check if running on macOS
if sys.platform != 'darwin':
    raise NotImplementedError("Native floating ball is only supported on macOS")

import objc
from Cocoa import (
    NSApplication,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSEvent,
    NSPanel,
    NSPoint,
    NSRect,
    NSSize,
    NSView,
    NSWindow,
    NSWindowStyleMaskBorderless,
)

# Floating window level (use NSFloatingWindowLevel from AppKit)
try:
    from AppKit import NSFloatingWindowLevel
    NSWindowLevelFloating = NSFloatingWindowLevel
except:
    NSWindowLevelFloating = 3  # Fallback


class FloatingBallView(NSView):
    """The view that draws the floating ball"""

    def initWithFrame_(self, frame):
        # Use objc.super correctly
        self = objc.super(FloatingBallView, self).initWithFrame_(frame)
        if self is None:
            return None

        self.color = NSColor.colorWithRed_green_blue_alpha_(0.6, 0.4, 0.75, 1.0)  # Purple
        self.is_recording = False
        self.is_paused = False
        self.mouse_down_callback = None
        self.mouse_dragged_callback = None
        self.right_click_callback = None
        self.mouse_up_callback = None  # For detecting clicks vs drags
        return self

    def drawRect_(self, rect):
        """Draw the circular ball"""
        bounds = self.bounds()

        # Draw outer glow
        glow = NSBezierPath.bezierPathWithOvalInRect_(bounds)
        glow_color = self.color.colorWithAlphaComponent_(0.3)
        glow_color.set()
        glow.fill()

        # Draw main ball (slightly smaller)
        main_rect = NSRect(NSPoint(2, 2), NSSize(bounds.size.width - 4, bounds.size.height - 4))
        main = NSBezierPath.bezierPathWithOvalInRect_(main_rect)
        self.color.set()
        main.fill()

        # Draw highlight
        highlight_rect = NSRect(NSPoint(bounds.size.width * 0.3, bounds.size.height * 0.3),
                                NSSize(bounds.size.width * 0.3, bounds.size.height * 0.3))
        highlight = NSBezierPath.bezierPathWithOvalInRect_(highlight_rect)
        NSColor.whiteColor().colorWithAlphaComponent_(0.3).set()
        highlight.fill()

        # Draw status icon
        self._draw_status_icon(bounds)

    def _draw_status_icon(self, bounds):
        """Draw recording status icon"""
        if self.is_paused:
            # Draw pause bars (II)
            bar_color = NSColor.whiteColor()
            bar_color.set()

            bar_width = 4
            bar_height = 20
            x1 = bounds.size.width / 2 - 6
            x2 = bounds.size.width / 2 + 2
            y = bounds.size.height / 2 - bar_height / 2

            rect1 = NSRect(NSPoint(x1, y), NSSize(bar_width, bar_height))
            rect2 = NSRect(NSPoint(x2, y), NSSize(bar_width, bar_height))

            NSBezierPath.bezierPathWithRect_(rect1).fill()
            NSBezierPath.bezierPathWithRect_(rect2).fill()

        elif self.is_recording:
            # Draw recording dot (●)
            dot_color = NSColor.whiteColor()
            dot_color.set()

            dot_size = 16
            dot_rect = NSRect(
                NSPoint((bounds.size.width - dot_size) / 2,
                       (bounds.size.height - dot_size) / 2),
                NSSize(dot_size, dot_size)
            )
            NSBezierPath.bezierPathWithOvalInRect_(dot_rect).fill()

        else:
            # Draw ready circle (○)
            stroke_color = NSColor.whiteColor()
            stroke_color.set()

            circle_size = 16
            circle_rect = NSRect(
                NSPoint((bounds.size.width - circle_size) / 2,
                       (bounds.size.height - circle_size) / 2),
                NSSize(circle_size, circle_size)
            )
            circle = NSBezierPath.bezierPathWithOvalInRect_(circle_rect)
            circle.setLineWidth_(2)
            circle.stroke()

    def setRecordingState_(self, is_recording):
        """Update recording state"""
        self.is_recording = is_recording
        self.setNeedsDisplay_(True)

    def setPaused_(self, is_paused):
        """Update pause state"""
        self.is_paused = is_paused
        self.setNeedsDisplay_(True)

    # Python method (not exposed to Objective-C)
    def set_rgba_color(self, red, green, blue, alpha):
        """Set ball color from RGBA values"""
        self.color = NSColor.colorWithRed_green_blue_alpha_(red, green, blue, alpha)
        self.setNeedsDisplay_(True)

    def mouseDown_(self, event):
        """Handle mouse down - start dragging"""
        if self.mouse_down_callback:
            self.mouse_down_callback(event)

    def mouseDragged_(self, event):
        """Handle mouse drag - move window"""
        if self.mouse_dragged_callback:
            self.mouse_dragged_callback(event)

    def rightMouseDown_(self, event):
        """Handle right click - show menu"""
        if self.right_click_callback:
            self.right_click_callback(event)

    def mouseUp_(self, event):
        """Handle mouse up - detect click vs drag"""
        if self.mouse_up_callback:
            self.mouse_up_callback(event)


class FloatingBallWindow(NSPanel):
    """
    A native macOS floating window for screen recording control.

    This is a real floating window that:
    - Stays on top of all windows
    - Can be dragged around the screen
    - Shows recording status
    - Responds to right-click menu
    """

    def initWithContentRect_styleMask_backing_defer_(
        self, contentRect, styleMask, backing, defer
    ):
        self = objc.super(FloatingBallWindow, self).initWithContentRect_styleMask_backing_defer_(
            contentRect, styleMask, backing, defer
        )
        if self is None:
            return None

        # Configure window properties
        self.setLevel_(NSWindowLevelFloating)
        self.setOpaque_(False)
        self.setBackgroundColor_(NSColor.clearColor())
        self.setMovableByWindowBackground_(True)

        # Configure panel behavior to stay visible across all spaces
        self.setFloatingPanel_(True)  # Keep floating above other windows
        self.setBecomesKeyOnlyIfNeeded_(True)  # Don't steal focus

        # Set collection behavior to join all spaces and stay in fullscreen
        # NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 6
        # NSWindowCollectionBehaviorFullScreenAuxiliary = 1 << 8
        # NSWindowCollectionBehaviorIgnoresCycle = 1 << 10
        self.setCollectionBehavior_((1 << 6) | (1 << 8) | (1 << 10))

        # Create ball view
        ball_view = FloatingBallView.alloc().initWithFrame_(contentRect)
        self.setContentView_(ball_view)

        # Callbacks
        self.presenter = None
        self.on_stop_callback = None
        self.on_pause_callback = None
        self.on_main_window_callback = None
        self.on_show_main_window_callback = None  # New: show main window without closing ball

        # Drag state
        self.initial_mouse_location = None
        self.initial_window_location = None
        self.is_dragging = False
        self.drag_threshold = 5.0  # Pixels to consider as drag

        # Setup callbacks
        ball_view.mouse_down_callback = self._on_mouse_down
        ball_view.mouse_dragged_callback = self._on_mouse_dragged
        ball_view.right_click_callback = self._on_right_click
        ball_view.mouse_up_callback = self._on_mouse_up

        return self

    def _on_mouse_down(self, event):
        """Handle mouse down - save initial positions"""
        self.initial_mouse_location = event.locationInWindow()
        self.initial_window_location = self.frame().origin
        self.is_dragging = False

    def _on_mouse_dragged(self, event):
        """Handle mouse drag - move window"""
        if self.initial_mouse_location is None:
            return

        current_mouse_location = event.locationInWindow()
        delta_x = current_mouse_location.x - self.initial_mouse_location.x
        delta_y = current_mouse_location.y - self.initial_mouse_location.y

        # Check if moved beyond threshold
        if not self.is_dragging:
            distance = (delta_x ** 2 + delta_y ** 2) ** 0.5
            if distance > self.drag_threshold:
                self.is_dragging = True

        new_origin = NSPoint(
            self.initial_window_location.x + delta_x,
            self.initial_window_location.y + delta_y
        )

        self.setFrameOrigin_(new_origin)

    def _on_mouse_up(self, event):
        """Handle mouse up - detect click vs drag"""
        # If not dragging, treat as click
        if not self.is_dragging and self.initial_mouse_location is not None:
            # Left click action: show main window without closing ball
            if self.on_show_main_window_callback:
                self.on_show_main_window_callback()

        # Reset drag state
        self.is_dragging = False
        self.initial_mouse_location = None

    def _on_right_click(self, event):
        """Handle right click - show context menu"""
        from AppKit import NSMenu, NSMenuItem

        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)

        # Recording info
        if self.presenter:
            try:
                status = self.presenter.get_recording_status()
                info_text = f"Frames: {status['frame_count']}\nTime: {status['elapsed_time']:.1f}s"
                info_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    info_text, "", ""
                )
                info_item.setEnabled_(False)
                menu.addItem_(info_item)
            except:
                pass

        menu.addItem_(NSMenuItem.separatorItem())

        # Stop Recording
        stop_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⏹ Stop Recording", "stopRecording:", ""
        )
        stop_item.setTarget_(self)
        menu.addItem_(stop_item)

        # Pause/Resume
        if self.contentView().is_recording:
            pause_text = "⏸ Pause" if not self.contentView().is_paused else "▶ Resume"
            pause_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                pause_text, "togglePause:", ""
            )
            pause_item.setTarget_(self)
            menu.addItem_(pause_item)

        # Main Window
        main_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🏠 Main Window", "showMainWindow:", ""
        )
        main_item.setTarget_(self)
        menu.addItem_(main_item)

        # Show menu
        menu.popUpMenuPositioningItem_atLocation_inView_(
            None, event.locationInWindow(), self.contentView()
        )

    def stopRecording_(self, sender):
        """Stop recording"""
        if self.presenter:
            self.presenter.stop_recording()
        if self.on_stop_callback:
            self.on_stop_callback()

    def togglePause_(self, sender):
        """Toggle pause/resume"""
        self.contentView().setPaused_(not self.contentView().is_paused)
        if self.on_pause_callback:
            self.on_pause_callback()

    def showMainWindow_(self, sender):
        """Show main window without closing floating ball"""
        if self.on_show_main_window_callback:
            self.on_show_main_window_callback()

    def setRecordingState_(self, is_recording):
        """Update recording state"""
        self.contentView().setRecordingState_(is_recording)

        # Update color based on state
        if self.contentView().is_paused:
            # Yellow for paused
            self.contentView().set_rgba_color(1.0, 0.7, 0.2, 1.0)
        elif is_recording:
            # Red for recording
            self.contentView().set_rgba_color(0.8, 0.2, 0.3, 1.0)
        else:
            # Purple for ready
            self.contentView().set_rgba_color(0.6, 0.4, 0.75, 1.0)

    def setPresenter_(self, presenter):
        """Set the recording presenter"""
        self.presenter = presenter

    def close(self):
        """Close the floating ball window"""
        try:
            # Close the window properly
            self.orderOut_(None)
            print("[FloatingBall] Window closed")
        except Exception as e:
            print(f"[FloatingBall] Error closing window: {e}")

    def makeKeyAndOrderFront_(self, sender):
        """Override to ensure window stays visible"""
        # Ensure window level is set correctly
        self.setLevel_(NSWindowLevelFloating)
        return objc.super(FloatingBallWindow, self).makeKeyAndOrderFront_(sender)


def create_floating_ball(presenter=None, position=None):
    """
    Create a native macOS floating ball window.

    Args:
        presenter: RecordingPresenter instance
        position: Initial position as (x, y) tuple, defaults to top-right of screen

    Returns:
        FloatingBallWindow instance
    """
    # Get screen size
    from Cocoa import NSScreen
    screen_frame = NSScreen.mainScreen().frame()

    # Ball size
    ball_size = 80
    margin = 20

    # Default position: top-right corner
    if position is None:
        x = screen_frame.size.width - ball_size - margin
        y = screen_frame.size.height - ball_size - margin
    else:
        x, y = position

    # Create window
    content_rect = NSRect(NSPoint(x, y), NSSize(ball_size, ball_size))

    window = FloatingBallWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        content_rect,
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False
    )

    # Set presenter
    if presenter:
        window.setPresenter_(presenter)

    # Ensure window properties are set
    window.setHidesOnDeactivate_(False)  # Don't hide when app loses focus

    # Show window
    window.makeKeyAndOrderFront_(None)
    window.setLevel_(NSWindowLevelFloating)  # Ensure window level is set

    print(f"[FloatingBall] Created native floating ball at ({x}, {y})")

    return window
