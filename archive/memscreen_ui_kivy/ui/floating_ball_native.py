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
    NSImage,
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

        # Load logo image
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'logo.png')
        if os.path.exists(logo_path):
            self.logo_image = NSImage.alloc().initWithContentsOfFile_(logo_path)
            if self.logo_image is None:
                print(f"[FloatingBall] Failed to load logo from {logo_path}")
                self.logo_image = None
            else:
                print(f"[FloatingBall] Loaded logo from {logo_path}")
        else:
            print(f"[FloatingBall] Logo not found at {logo_path}")
            self.logo_image = None

        return self

    def drawRect_(self, rect):
        """Draw the circular ball with logo"""
        bounds = self.bounds()

        # Draw outer glow
        glow = NSBezierPath.bezierPathWithOvalInRect_(bounds)
        glow_color = self.color.colorWithAlphaComponent_(0.3)
        glow_color.set()
        glow.fill()

        # Create circular clipping path for logo
        clip_rect = NSRect(NSPoint(2, 2), NSSize(bounds.size.width - 4, bounds.size.height - 4))
        clip_path = NSBezierPath.bezierPathWithOvalInRect_(clip_rect)

        # Save graphics state
        from AppKit import NSGraphicsContext
        NSGraphicsContext.currentContext().saveGraphicsState()

        # Clip to circular path
        clip_path.addClip()

        # Draw logo image (if available)
        if self.logo_image:
            # Draw logo filling the circular area
            self.logo_image.drawInRect_(clip_rect)
        else:
            # Fallback: draw solid color if logo not available
            main = NSBezierPath.bezierPathWithOvalInRect_(clip_rect)
            self.color.set()
            main.fill()

        # Restore graphics state
        NSGraphicsContext.currentContext().restoreGraphicsState()

        # Draw border
        border_path = NSBezierPath.bezierPathWithOvalInRect_(clip_rect)
        NSColor.whiteColor().colorWithAlphaComponent_(0.2).set()
        border_path.setLineWidth_(1.5)
        border_path.stroke()

        # Draw status icon overlay
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
        print("[FloatingBallView] rightMouseDown_ called!")
        if self.right_click_callback:
            print("[FloatingBallView] Calling right_click_callback...")
            self.right_click_callback(event)
        else:
            print("[FloatingBallView] WARNING: right_click_callback is None!")

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

        # CRITICAL: Ensure this is a child window of the application, not another window
        # This allows it to move anywhere on screen, not just within parent window bounds
        self.setParentWindow_(None)  # Explicitly set no parent window

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
        self.on_select_region_callback = None  # New: select region from floating ball
        self.on_start_recording_callback = None  # New: start recording from floating ball
        # Additional feature callbacks
        self.on_show_videos_callback = None  # Show videos screen
        self.on_show_chat_callback = None  # Show chat screen
        self.on_show_process_callback = None  # Show process mining screen
        self.on_show_about_callback = None  # Show about screen
        self.on_switch_screen_callback = None  # Generic screen switch callback
        self.on_select_screen_callback = None  # Screen selection callback
        self.on_quit_callback = None  # Quit application

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
        print("[FloatingBall] Right click detected, showing menu...")
        print(f"[FloatingBall] on_select_region_callback is: {self.on_select_region_callback}")
        from AppKit import NSMenu, NSMenuItem

        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)

        # Recording info
        if self.presenter:
            try:
                status = self.presenter.get_recording_status()
                mode_info = self.presenter.get_recording_mode()
                mode_text = f"Mode: {mode_info['mode'].title()}"

                # Add screen info if in fullscreen-single mode
                if mode_info['mode'] == 'fullscreen-single' and mode_info['screen_index'] is not None:
                    try:
                        from memscreen.utils import get_screen_by_index
                        screen_info = get_screen_by_index(mode_info['screen_index'])
                        if screen_info:
                            mode_text += f" ({screen_info.name})"
                        else:
                            mode_text += f" (Screen {mode_info['screen_index'] + 1})"
                    except:
                        mode_text += f" (Screen {mode_info['screen_index'] + 1})"

                if mode_info['mode'] == 'region' and mode_info['bbox']:
                    bbox = mode_info['bbox']
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    mode_text += f" ({width}×{height})"

                info_text = f"{mode_text}\nFrames: {status['frame_count']}\nTime: {status['elapsed_time']:.1f}s"
                info_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    info_text, "", ""
                )
                info_item.setEnabled_(False)
                menu.addItem_(info_item)
            except:
                pass

        menu.addItem_(NSMenuItem.separatorItem())

        # Add "Select Region" menu item (always visible for region mode)
        select_region_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🎯 Select Region", "selectRegion:", ""
        )
        select_region_item.setTarget_(self)
        print(f"[FloatingBall] Created Select Region menu item, target={self}, action=selectRegion:")
        menu.addItem_(select_region_item)

        # Add Screen Selection submenu
        try:
            from memscreen.utils import get_screens
            screens = get_screens()

            if len(screens) > 1:
                # Create submenu for screen selection
                screen_menu = NSMenu.alloc().init()

                # "All Screens" option
                all_screens_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "🖥 All Screens", "selectScreen:", ""
                )
                all_screens_item.setTarget_(self)
                all_screens_item.setTag_(-1)  # -1 for all screens
                screen_menu.addItem_(all_screens_item)

                screen_menu.addItem_(NSMenuItem.separatorItem())

                # Individual screen options
                for idx, screen in enumerate(screens):
                    screen_name = screen.name
                    if screen.is_primary:
                        screen_name += " (Primary)"

                    screen_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                        f"🖥 {screen_name}", "selectScreen:", ""
                    )
                    screen_item.setTarget_(self)
                    screen_item.setTag_(idx)  # Store screen index
                    screen_menu.addItem_(screen_item)

                # Add submenu to main menu
                screen_submenu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    "🖥 Select Screen", "", ""
                )
                screen_submenu_item.setSubmenu_(screen_menu)
                menu.addItem_(screen_submenu_item)

        except Exception as e:
            print(f"[FloatingBall] Error getting screens for menu: {e}")

        # Add "Start Recording" menu item (visible when not recording)
        if not self.contentView().is_recording:
            start_recording_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "⏺ Start Recording", "startRecording:", ""
            )
            start_recording_item.setTarget_(self)
            menu.addItem_(start_recording_item)

        # Stop Recording
        if self.contentView().is_recording:
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

        menu.addItem_(NSMenuItem.separatorItem())

        # === Main Features Section ===

        # Main Window / Recording
        main_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🏠 Recording", "showMainWindow:", ""
        )
        main_item.setTarget_(self)
        menu.addItem_(main_item)

        # Videos
        videos_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🎬 Videos", "showVideos:", ""
        )
        videos_item.setTarget_(self)
        menu.addItem_(videos_item)

        # Chat
        chat_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "💬 AI Chat", "showChat:", ""
        )
        chat_item.setTarget_(self)
        menu.addItem_(chat_item)

        # Process Mining
        process_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚡ Process", "showProcess:", ""
        )
        process_item.setTarget_(self)
        menu.addItem_(process_item)

        # About
        about_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "ℹ️ About", "showAbout:", ""
        )
        about_item.setTarget_(self)
        menu.addItem_(about_item)

        menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🚪 Quit MemScreen", "quit:", "q"
        )
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

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
        """Show main window/recording screen"""
        # Use the generic screen switch mechanism
        if self.on_switch_screen_callback:
            self.on_switch_screen_callback('recording')
        elif self.on_show_main_window_callback:
            self.on_show_main_window_callback()

    def selectRegion_(self, sender):
        """Open region selector"""
        print("[FloatingBall] selectRegion_ called!")
        if self.on_select_region_callback:
            print("[FloatingBall] Calling on_select_region_callback...")
            self.on_select_region_callback()
        else:
            print("[FloatingBall] WARNING: on_select_region_callback is None!")

    def startRecording_(self, sender):
        """Start recording from floating ball"""
        if self.on_start_recording_callback:
            self.on_start_recording_callback()

    def selectScreen_(self, sender):
        """Select screen for recording"""
        screen_tag = sender.tag()  # Get screen index from menu item tag

        try:
            # Prefer UI callback so main window/presenter state stay in sync
            if self.on_select_screen_callback:
                selected = None if screen_tag == -1 else int(screen_tag)
                self.on_select_screen_callback(selected)
                return

            if not self.presenter:
                print("[FloatingBall] No presenter available for screen selection")
                return

            if screen_tag == -1:
                # All screens selected
                self.presenter.set_recording_mode('fullscreen')
                print("[FloatingBall] Screen selection changed to: All Screens")
            else:
                # Specific screen selected
                screen_index = int(screen_tag)
                self.presenter.set_recording_mode('fullscreen-single', screen_index=screen_index)

                # Get screen info for logging
                from memscreen.utils import get_screen_by_index
                screen_info = get_screen_by_index(screen_index)
                if screen_info:
                    print(f"[FloatingBall] Screen selection changed to: {screen_info.name}")
                else:
                    print(f"[FloatingBall] Screen selection changed to: Screen {screen_index + 1}")

        except Exception as e:
            print(f"[FloatingBall] Error selecting screen: {e}")
            import traceback
            traceback.print_exc()

    def showVideos_(self, sender):
        """Show videos screen"""
        if self.on_show_videos_callback:
            self.on_show_videos_callback()
        elif self.on_switch_screen_callback:
            self.on_switch_screen_callback('video')

    def showChat_(self, sender):
        """Show chat screen"""
        if self.on_show_chat_callback:
            self.on_show_chat_callback()
        elif self.on_switch_screen_callback:
            self.on_switch_screen_callback('chat')

    def showProcess_(self, sender):
        """Show process mining screen"""
        if self.on_show_process_callback:
            self.on_show_process_callback()
        elif self.on_switch_screen_callback:
            self.on_switch_screen_callback('process')

    def showAbout_(self, sender):
        """Show about screen"""
        if self.on_show_about_callback:
            self.on_show_about_callback()
        elif self.on_switch_screen_callback:
            self.on_switch_screen_callback('about')

    def quit_(self, sender):
        """Quit MemScreen application"""
        print("[FloatingBall] Quit requested")

        # Call quit callback first (this should close both ball and main app)
        if self.on_quit_callback:
            self.on_quit_callback()
        elif self.on_main_window_callback:
            # Fallback to old callback
            self.on_main_window_callback()
        else:
            # Default behavior: just close the ball
            self.close()

        # Terminate the NSApplication properly
        try:
            from AppKit import NSApplication
            from PyObjCTools import AppHelper
            app = NSApplication.sharedApplication()

            # Stop the event loop and terminate
            AppHelper.stopEventLoop()
            app.stop_(None)
            app.terminate_(None)

            print("[FloatingBall] Application terminated")
        except Exception as e:
            print(f"[FloatingBall] Error terminating: {e}")
            import sys
            sys.exit(0)

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
        position: Initial position as (x, y) tuple, defaults to top-right of primary screen

    Returns:
        FloatingBallWindow instance
    """
    # Get screen size - use primary screen to ensure visibility
    from Cocoa import NSScreen, NSEvent

    # Always use primary screen to ensure the ball is visible
    # This prevents the ball from being on a disconnected screen
    target_screen = NSScreen.mainScreen()

    # Optional: Try to use the screen where mouse is, but fallback to primary
    try:
        mouse_location = NSEvent.mouseLocation()
        for screen in NSScreen.screens():
            screen_frame = screen.frame()
            if (screen_frame.origin.x <= mouse_location.x <= screen_frame.origin.x + screen_frame.size.width and
                screen_frame.origin.y <= mouse_location.y <= screen_frame.origin.y + screen_frame.size.height):
                # Mouse is on this screen, check if it's the primary screen
                if screen == target_screen:
                    # Use this screen (it's the primary one)
                    break
                # If mouse is on non-primary screen, still use primary screen
                # to avoid visibility issues when screen is disconnected
                break
    except Exception as e:
        print(f"[FloatingBall] Error detecting mouse position: {e}, using primary screen")

    screen_frame = target_screen.frame()

    # Ball size
    ball_size = 80
    margin = 20

    # Default position: top-right corner of the primary screen
    # IMPORTANT: Use screen's visible frame to account for menu bar and dock
    if position is None:
        x = screen_frame.origin.x + screen_frame.size.width - ball_size - margin
        y = screen_frame.origin.y + screen_frame.size.height - ball_size - margin

        # Ensure position is within screen bounds (safety check)
        # Handle case where screen coordinates might be negative (secondary screens)
        if x < screen_frame.origin.x:
            x = screen_frame.origin.x + margin
        if y < screen_frame.origin.y:
            y = screen_frame.origin.y + margin
    else:
        x, y = position
        # Clamp to screen bounds for safety
        x = max(screen_frame.origin.x + margin, min(x, screen_frame.origin.x + screen_frame.size.width - ball_size - margin))
        y = max(screen_frame.origin.y + margin, min(y, screen_frame.origin.y + screen_frame.size.height - ball_size - margin))

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

    # Debug info
    screen_name = "Main Screen" if target_screen == NSScreen.mainScreen() else "Secondary Screen"
    print(f"[FloatingBall] Created native floating ball at ({x}, {y}) on {screen_name}")
    print(f"[FloatingBall] Screen frame: origin=({screen_frame.origin.x}, {screen_frame.origin.y}), "
          f"size=({screen_frame.size.width}, {screen_frame.size.height})")
    print(f"[FloatingBall] Mouse was at: ({mouse_location.x}, {mouse_location.y})")

    return window
