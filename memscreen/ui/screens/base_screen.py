### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Base Screen class for all MemScreen Kivy screens"""

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock


class BaseScreen(Screen):
    """
    Base class for all screens in MemScreen.

    Provides common functionality:
    - Presenter access
    - Navigation methods
    - Common UI patterns
    """

    # Presenter property (will be set by app)
    presenter = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        """Initialize the screen"""
        super().__init__(**kwargs)
        self.screen_name = kwargs.get('name', 'screen')

    def on_enter(self):
        """Called when screen is displayed"""
        print(f"[{self.screen_name}] Screen entered")

    def on_pre_enter(self):
        """Called just before screen is displayed"""
        pass

    def on_leave(self):
        """Called when screen is exited"""
        print(f"[{self.screen_name}] Screen left")

    def on_pre_leave(self):
        """Called just before screen is exited"""
        pass

    def set_presenter(self, presenter):
        """Set the presenter for this screen"""
        self.presenter = presenter
        # Wire presenter callbacks to screen methods
        self._wire_presenter_callbacks()

    def _wire_presenter_callbacks(self):
        """
        Wire presenter callbacks to screen methods.
        Override in subclasses to add specific callbacks.
        """
        pass

    def show_error(self, message):
        """Show error message to user"""
        # Use Kivy popup or toast
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        content = Label(
            text=f"⚠️ {message}",
            font_size=16,
            color=[1, 0, 0, 1]
        )

        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.4, 0.2),
            auto_dismiss=True
        )
        popup.open()

    def show_info(self, message):
        """Show info message to user"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        content = Label(
            text=f"ℹ️ {message}",
            font_size=16
        )

        popup = Popup(
            title='Info',
            content=content,
            size_hint=(0.4, 0.2),
            auto_dismiss=True
        )
        popup.open()

    def show_success(self, message):
        """Show success message to user"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        content = Label(
            text=f"✅ {message}",
            font_size=16,
            color=[0, 0.5, 0, 1]
        )

        popup = Popup(
            title='Success',
            content=content,
            size_hint=(0.4, 0.2),
            auto_dismiss=True
        )
        popup.open()
