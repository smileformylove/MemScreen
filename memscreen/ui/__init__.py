### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""MemScreen UI module"""

# Lazy imports to avoid Kivy initialization for floating-ball-only mode
# Import these only when needed to keep floating_ball_native standalone

__all__ = ["MemScreenApp", "FloatingBallWindow", "FloatingBallWindow"]

def __getattr__(name):
    """Lazy import for Kivy-dependent modules"""
    if name == "MemScreenApp":
        from .kivy_app import MemScreenApp
        return MemScreenApp
    elif name == "FloatingBallWindow":
        from .floating_ball import FloatingBallWindow
        return FloatingBallWindow
    elif name == "create_floating_ball":
        from .floating_ball_native import create_floating_ball
        return create_floating_ball
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
