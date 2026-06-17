"""Compatibility entry point for the desktop application."""

from apps.desktop.app import App

__all__ = ["App"]


if __name__ == "__main__":
    App().mainloop()
