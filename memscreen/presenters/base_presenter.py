### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Base Presenter class for MVP architecture"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List


class BasePresenter(ABC):
    """
    Base class for all Presenters in MVP architecture.

    The Presenter is responsible for:
    - Containing all business logic
    - Communicating between View and Model
    - Processing data before passing to View
    - Handling errors and displaying messages through View

    The View should only:
    - Display data
    - Capture user input
    - Delegate all logic to Presenter
    """

    def __init__(self, view=None, model=None):
        """
        Initialize presenter with optional view and model

        Args:
            view: The View instance (UI component)
            model: The Model instance (business logic/data)
        """
        self.view = view
        self.model = model
        self._is_initialized = False

    @abstractmethod
    def initialize(self):
        """
        Initialize the presenter and its dependencies.
        Called when the view is ready.
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Clean up resources when the view is destroyed.
        """
        pass

    def set_view(self, view):
        """
        Set or update the view reference.

        Args:
            view: The View instance
        """
        self.view = view

    def set_model(self, model):
        """
        Set or update the model reference.

        Args:
            model: The Model instance
        """
        self.model = model

    def show_error(self, message: str, title: str = "Error"):
        """
        Display an error message through the view.

        Args:
            message: Error message to display
            title: Optional title for error dialog
        """
        if self.view and hasattr(self.view, 'show_error'):
            self.view.show_error(message, title)
        else:
            print(f"[ERROR] {title}: {message}")

    def show_info(self, message: str, title: str = "Info"):
        """
        Display an info message through the view.

        Args:
            message: Info message to display
            title: Optional title for info dialog
        """
        if self.view and hasattr(self.view, 'show_info'):
            self.view.show_info(message, title)
        else:
            print(f"[INFO] {title}: {message}")

    def show_success(self, message: str, title: str = "Success"):
        """
        Display a success message through the view.

        Args:
            message: Success message to display
            title: Optional title for success dialog
        """
        if self.view and hasattr(self.view, 'show_success'):
            self.view.show_success(message, title)
        else:
            print(f"[SUCCESS] {title}: {message}")

    def update_view(self, data: Dict[str, Any]):
        """
        Update the view with new data.

        Args:
            data: Dictionary containing data to update in view
        """
        if self.view and hasattr(self.view, 'update_data'):
            self.view.update_data(data)

    def handle_error(self, error: Exception, context: str = ""):
        """
        Central error handling for presenter operations.

        Args:
            error: The exception that occurred
            context: Optional context about where error occurred
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)

        # Log the error
        import traceback
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()

        # Show error to user through view
        self.show_error(error_msg)

    def is_ready(self) -> bool:
        """
        Check if presenter is ready for operations.

        Returns:
            True if presenter and its dependencies are initialized
        """
        return self._is_initialized and self.view is not None
