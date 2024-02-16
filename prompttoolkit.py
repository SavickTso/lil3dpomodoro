import argparse
import asyncio
import datetime
import threading
import time

from prompt_toolkit import Application
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.dimension import to_dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame


def make_app(current_time):
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        event.app.exit()

    def _vsplit(padding, m):
        return VSplit(
            [
                Window(width=padding, always_hide_cursor=True),
                m,
                Window(width=padding, always_hide_cursor=True),
            ]
        )

    padding = to_dimension(D(preferred=0))
    body = Window(
        content=FormattedTextControl(text=str(current_time.second)),
        width=20,
        height=5,
        always_hide_cursor=True,
    )
    body = Frame(body)

    # make container app

    under_text = Window(height=padding, always_hide_cursor=True)
    root_container = HSplit(
        [
            Window(height=padding, always_hide_cursor=True),
            _vsplit(padding, body),
            _vsplit(padding, under_text),
        ],
        key_bindings=None,
    )
    layout = Layout(container=root_container)
    return Application(
        layout=layout, key_bindings=kb, full_screen=True, refresh_interval=0.1
    )


def create_layout():
    # Define a FormattedTextControl with initial text
    text_control = FormattedTextControl(text="")

    # Create a Window with the text control
    window = Window(content=text_control)

    # Create a Layout with the window
    layout = Layout(container=window)

    return layout


def main():
    # Define style
    style = Style.from_dict({"": "fg:#ffffff bg:#000000"})

    # Create initial layout

    # Create an Application with the layout

    current_time = datetime.datetime.now()
    application = make_app(current_time)

    application.run()


if __name__ == "__main__":
    main()
