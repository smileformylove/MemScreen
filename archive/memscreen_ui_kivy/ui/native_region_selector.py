#!/usr/bin/env python3
"""
Native macOS Region Selector

Uses PyObjC to create a native macOS overlay window for region selection.
This provides a smooth, native experience compared to Kivy-based selection.
"""

import sys
import os
from typing import Optional, Callable, Tuple

# Check if running on macOS
if sys.platform != 'darwin':
    raise NotImplementedError("Native region selector is only supported on macOS")

import objc
from Cocoa import (
    NSApplication,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSEvent,
    NSEventMaskLeftMouseDown,
    NSEventMaskLeftMouseDragged,
    NSEventMaskLeftMouseUp,
    NSEventMaskKeyDown,
    NSEventTypeLeftMouseDown,
    NSEventTypeLeftMouseDragged,
    NSEventTypeLeftMouseUp,
    NSEventTypeKeyDown,
    NSPanel,
    NSPoint,
    NSRect,
    NSSize,
    NSView,
    NSWindow,
    NSWindowStyleMaskBorderless,
)

# Floating window level
try:
    from AppKit import NSFloatingWindowLevel
    NSWindowLevelFloating = NSFloatingWindowLevel
except:
    NSWindowLevelFloating = 3  # Fallback


class RegionSelectionView(NSView):
    """View that handles region selection with visual feedback"""

    def initWithCallback_(self, callback):
        """Initialize with callback function"""
        self = objc.super(RegionSelectionView, self).init()
        if self is None:
            return None

        self.callback = callback
        self.start_point = None
        self.current_point = None
        self.is_dragging = False

        # Semi-transparent dark background
        self.bg_color = NSColor.colorWithRed_green_blue_alpha_(0.1, 0.1, 0.1, 0.5)

        # Selection box color (bright purple)
        self.selection_color = NSColor.colorWithRed_green_blue_alpha_(0.6, 0.4, 0.75, 0.8)
        self.border_color = NSColor.colorWithRed_green_blue_alpha_(0.8, 0.6, 0.9, 1.0)

        # IMPORTANT: Make view accept first responder to receive mouse events
        # This is critical for mouse event handling
        self.setAcceptsTouchEvents_(True)

        print("[RegionSelectionView] Initialized with callback")

        return self

    def acceptsFirstResponder(self):
        """Allow view to become first responder - critical for receiving events"""
        return True

    def acceptsFirstMouse(self):
        """Allow view to receive mouse events even if not in focus"""
        return True

    def drawRect_(self, rect):
        """Draw the background and selection rectangle"""
        bounds = self.bounds()

        # Draw semi-transparent background
        self.bg_color.set()
        NSBezierPath.bezierPathWithRect_(bounds).fill()

        # Draw selection rectangle if dragging
        if self.start_point and self.current_point:
            # Calculate selection rectangle
            x = min(self.start_point.x, self.current_point.x)
            y = min(self.start_point.y, self.current_point.y)
            width = abs(self.current_point.x - self.start_point.x)
            height = abs(self.current_point.y - self.start_point.y)

            selection_rect = NSRect(NSPoint(x, y), NSSize(width, height))

            # Draw selection box background
            self.selection_color.set()
            NSBezierPath.bezierPathWithRect_(selection_rect).fill()

            # Draw border
            self.border_color.set()
            path = NSBezierPath.bezierPathWithRect_(selection_rect)
            path.setLineWidth_(2.0)
            path.stroke()

            # Draw dimensions text
            try:
                from Cocoa import NSFont, NSAttributedString
                text = f"{int(width)}×{int(height)}"
                text_attrs = {
                    'NSFont': NSFont.fontWithName_size_("Menlo", 14),
                    'NSForegroundColorAttributeName': self.border_color,
                }
                text_string = NSAttributedString.alloc().initWithString_attributes_(text, text_attrs)
                text_string.drawAtPoint_(NSPoint(x, y - 20))
            except:
                pass

    def mouseDown_(self, event):
        """Handle mouse down event - start selection"""
        print("[RegionSelectionView] mouseDown_ called!")
        self.start_point = event.locationInWindow()
        self.current_point = self.start_point
        self.is_dragging = True
        print(f"[RegionSelectionView] Start point: {self.start_point}")
        self.setNeedsDisplay_(True)

    def mouseDragged_(self, event):
        """Handle mouse dragged event - update selection"""
        if self.is_dragging:
            self.current_point = event.locationInWindow()
            print(f"[RegionSelectionView] Dragging to: {self.current_point}")
            self.setNeedsDisplay_(True)

    def mouseUp_(self, event):
        """Handle mouse up event - complete selection"""
        print("[RegionSelectionView] mouseUp_ called!")
        if not self.is_dragging:
            print("[RegionSelectionView] Not dragging, ignoring")
            return

        self.is_dragging = False
        end_point = event.locationInWindow()
        self.current_point = end_point
        print(f"[RegionSelectionView] End point: {end_point}")

        # Calculate selection bbox
        if self.start_point and end_point:
            # Get window and screen info
            window = self.window()
            screen = window.screen()
            screen_frame = screen.frame()

            # Get window position in screen coordinates
            window_frame = window.frame()

            # Selection coordinates in window (relative to window's bottom-left)
            x1_rel = min(self.start_point.x, end_point.x)
            x2_rel = max(self.start_point.x, end_point.x)
            y1_rel = min(self.start_point.y, end_point.y)
            y2_rel = max(self.start_point.y, end_point.y)

            # Convert to screen coordinates (Cocoa: bottom-left origin)
            # Window frame origin is in screen coordinates
            x1_screen = window_frame.origin.x + x1_rel
            x2_screen = window_frame.origin.x + x2_rel
            y1_screen = window_frame.origin.y + y1_rel
            y2_screen = window_frame.origin.y + y2_rel

            # Convert from Cocoa (bottom-left) to PIL (top-left) coordinates
            # Need to get the screen's position in PIL coordinate system
            from Cocoa import NSScreen
            main_screen = NSScreen.mainScreen()
            main_frame = main_screen.frame()
            main_height = int(main_frame.size.height)

            # Global PIL coordinates
            # x stays the same
            # y needs conversion: PIL_y = main_height - cocoa_y - height
            # But for a point: PIL_y = main_height - cocoa_y
            # For the bbox, we need to convert both y coordinates
            # The bbox is in PIL coords: (left, top, right, bottom)
            # where top < bottom in PIL coords

            # For each screen coordinate (cocoa_y):
            # PIL_y = main_height - cocoa_y
            x1_pil = int(x1_screen)
            x2_pil = int(x2_screen)
            y2_pil = main_height - int(y1_screen)  # Top in PIL (lower y1 in Cocoa)
            y1_pil = main_height - int(y2_screen)  # Bottom in PIL (higher y2 in Cocoa)

            # Minimum selection size (10x10 pixels)
            if x2_pil - x1_pil < 10 or y2_pil - y1_pil < 10:
                print("[RegionSelector] Selection too small, cancelling")
                self.window().close_()
                print(f"[RegionSelector] Calling callback with None")
                if hasattr(self, 'callback') and self.callback:
                    self.callback(None)
                return

            bbox = (x1_pil, y1_pil, x2_pil, y2_pil)
            print(f"[RegionSelector] Selection complete: {bbox}")
            print(f"[RegionSelector] Window frame: {window_frame}")
            print(f"[RegionSelector] Screen frame: {screen_frame}")

            # Close window first
            self.window().close_()
            print(f"[RegionSelector] Window closed, calling callback...")

            # Call callback with result
            if hasattr(self, 'callback') and self.callback:
                self.callback(bbox)

        self.setNeedsDisplay_(True)

    def keyDown_(self, event):
        """Handle key press events - ESC to cancel"""
        from Cocoa import NSCharacterSet
        chars = event.characters()
        if chars and len(chars) > 0:
            char = chars[0]
            print(f"[RegionSelectionView] Key pressed: {ord(char)}")
            # ESC key (character code 27)
            if ord(char) == 27:
                print("[RegionSelectionView] ESC pressed, cancelling selection")
                self.window().close_()
                print(f"[RegionSelector] Calling callback with None")
                if hasattr(self, 'callback') and self.callback:
                    self.callback(None)
        else:
            objc.super(RegionSelectionView, self).keyDown_(event)


class RegionSelectionWindow(NSPanel):
    """Native macOS window for region selection"""

    def initWithScreen_callback_(self, screen, callback):
        """Initialize with screen and callback"""
        screen_frame = screen.frame()
        content_rect = NSRect(
            NSPoint(screen_frame.origin.x, screen_frame.origin.y),
            NSSize(screen_frame.size.width, screen_frame.size.height)
        )

        self = objc.super(RegionSelectionWindow, self).initWithContentRect_styleMask_backing_defer_(
            content_rect,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )

        if self is None:
            return None

        # Configure window properties
        self.setLevel_(NSWindowLevelFloating)
        self.setOpaque_(False)
        self.setBackgroundColor_(NSColor.clearColor())

        # IMPORTANT: Configure window to receive mouse events
        self.setAcceptsMouseMovedEvents_(True)
        self.setIgnoresMouseEvents_(False)  # Don't ignore mouse events

        # Create view
        view = RegionSelectionView.alloc().initWithCallback_(callback)
        self.setContentView_(view)

        # Make window key and visible
        self.makeKeyAndOrderFront_(None)

        # CRITICAL: Activate the application to ensure it receives events
        from AppKit import NSApplication
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)

        # Set window as key window to ensure it receives keyboard events (ESC)
        self.makeKeyWindow()

        # Get the view for event monitoring
        content_view = self.contentView()

        # Add local event monitor to track mouse events specifically for this window
        self.event_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskLeftMouseDown | NSEventMaskLeftMouseDragged | NSEventMaskLeftMouseUp | NSEventMaskKeyDown,
            lambda event: self._handle_event(event, content_view)
        )

        print(f"[RegionSelector] Window created and activated at screen {screen}")
        print(f"[RegionSelector] Window frame: {self.frame()}")
        print(f"[RegionSelector] Event monitor installed")

        return self

    def _handle_event(self, event, view):
        """Handle monitored events"""
        event_type = event.type()
        print(f"[RegionSelector] Event captured: type={event_type}")

        # Pass the event to the view for processing
        if event_type == NSEventTypeLeftMouseDown:
            view.mouseDown_(event)
        elif event_type == NSEventTypeLeftMouseDragged:
            view.mouseDragged_(event)
        elif event_type == NSEventTypeLeftMouseUp:
            view.mouseUp_(event)
        elif event_type == NSEventTypeKeyDown:
            view.keyDown_(event)

        return event

    def close_(self, sender=None):
        """Clean up event monitor when closing"""
        if hasattr(self, 'event_monitor') and self.event_monitor:
            NSEvent.removeMonitor_(self.event_monitor)
            print("[RegionSelector] Event monitor removed")
        # Call parent's close method using NSWindow's close
        NSPanel.close(self)


def select_region(callback: Callable[[Optional[Tuple[int, int, int, int]]], None],
                 screen_index: int = 0) -> RegionSelectionWindow:
    """
    Show native region selector overlay.

    Args:
        callback: Function to call when selection is complete.
                  Called with bbox tuple (left, top, right, bottom) or None if cancelled.
        screen_index: Index of screen to select on (0 = main screen)

    Returns:
        RegionSelectionWindow instance
    """
    print(f"[RegionSelector] select_region called with screen_index={screen_index}")

    from Cocoa import NSScreen

    # Get target screen
    screens = NSScreen.screens()
    print(f"[RegionSelector] Available screens: {len(screens)}")
    if screen_index >= len(screens):
        screen_index = 0

    target_screen = screens[screen_index]
    print(f"[RegionSelector] Target screen: {target_screen}")

    # Create and show selection window
    print(f"[RegionSelector] Creating RegionSelectionWindow...")
    window = RegionSelectionWindow.alloc().initWithScreen_callback_(target_screen, callback)

    print(f"[RegionSelector] Native region selector opened on screen {screen_index + 1}")

    return window


# For testing
if __name__ == "__main__":
    def test_callback(bbox):
        if bbox:
            print(f"Selected region: {bbox}")
        else:
            print("Selection cancelled")

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    print("Opening region selector... (Press ESC to cancel, drag to select)")
    print("Press Ctrl+C to exit")

    selector = select_region(test_callback)

    # Keep running
    from AppKit import NSApplication
    app = NSApplication.sharedApplication()
    app.run()
