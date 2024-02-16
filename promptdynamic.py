import asyncio
import datetime
import json
import time

from prompt_toolkit import Application, widgets
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style

json_file_path = "tomato.json"
with open(json_file_path, "r") as json_file:
    char_matrix = json.load(json_file)

framelist = []
for frame in char_matrix:
    textframe = []
    for row in frame:
        textframe.append(("class:hello", "".join(row)))
        textframe.append(("", "\n"))
    framelist.append(textframe)

style = Style.from_dict(
    {"hello": "#ff0066", "world": "#44ff44 italic", "hello": "font-size: 5"}
)

static_text = FormattedTextControl(
    text=[
        ("class:hello", f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"),
        ("", "\n"),  # Add a newline
        ("class:hello", f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"),
    ]
)
static_text2 = FormattedTextControl(
    text=[
        ("class:hello", framelist[datetime.datetime.now().second % len(framelist)][0]),
    ]
)
# static_window = Window(content=static_text, height=6)

telemetry_window = Window(content=static_text2, height=50)
# telemetry_window = Window(content=FormattedTextControl(text="Some fixed text"))

root_container = HSplit(
    # [widgets.Frame(body=static_window),
    [widgets.Frame(body=telemetry_window)]
)

layout = Layout(root_container)

kb = KeyBindings()


@kb.add("c-q")
@kb.add("c-c")
def exit_(event):
    event.app.exit()


ctr = 0


def refresh(app):
    global ctr
    # print(app)
    # static_text.text = [
    #     ("class:hello", f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"),
    #     ("", str(ctr)),
    #     ("", "\n"),  # Add a newline
    #     ("class:hello", f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"),
    #     ("class:hello", f"Time: {datetime.datetime.now().microsecond}"),
    # ]
    # frames = []
    # for row in framelist[datetime.datetime.now().microsecond % len(framelist)]:
    #     frames.append(("class:hello", row))
    #     frames.append(("", "\n"))
    static_text2.text = framelist[ctr % len(framelist)]
    ctr += 1
    # static_text2.text = [
    #     ("class:hello", row)
    #     for row in framelist[datetime.datetime.now().second % len(framelist)]
    # ]


app = Application(
    layout=layout,
    style=style,
    full_screen=True,
    key_bindings=kb,
    refresh_interval=0.05,
    before_render=refresh,
)

app.run()
