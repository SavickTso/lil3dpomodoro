import curses
import json
import time

json_file_path = "tomato.json"
with open(json_file_path, "r") as json_file:
    char_matrix = json.load(json_file)

framelist = []
for frame in char_matrix:
    textframe = []
    for row in frame:
        textframe.append("".join(row))
    framelist.append(textframe)
print(framelist[0])
sentences = [
    "Welcome to the Text User Interface!",
    "This is a simple example of a TUI.",
    "Press any key to see the next sentence.",
    "Enjoy exploring the world of text-based interfaces!",
]


def main(stdscr):
    # Clear the screen
    stdscr.clear()
    stdscr.resize(500, 500)
    # Initialize index for cycling through sentences
    sentence_index = 0

    json_file_path = "tomato.json"
    with open(json_file_path, "r") as json_file:
        char_matrix = json.load(json_file)

    framelist = []
    for frame in char_matrix:
        textframe = []
        for row in frame:
            textframe.append("".join(row))
        framelist.append(textframe)

    # Infinite loop to cycle through sentences
    while True:
        # Add each line to the screen
        for i, line in enumerate(framelist[sentence_index]):
            stdscr.addstr(i, 0, line)

        # Refresh the screen
        stdscr.refresh()

        # Wait for a few seconds before displaying the next sentence
        time.sleep(0.1)

        # Clear the screen for the next sentence
        stdscr.clear()

        # Increment the index for the next sentence
        sentence_index = (sentence_index + 1) % len(framelist)


# Run the TUI
curses.wrapper(main)

# import curses
# import json
# import random


# def main(stdscr):
#     stdscr.clear()
#     curses.curs_set(0)  # Hide the cursor

#     # Define color pairs
#     curses.start_color()
#     curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
#     curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
#     curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
#     curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
#     curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
#     curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
#     curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

#     # Define characters and their corresponding colors
#     characters = ["H", "e", "l", "l", "o", ",", " ", "W", "o", "r", "l", "d", "!"]
#     colors = [curses.color_pair(random.randint(1, 7)) for _ in characters]

#     # Print characters with their respective colors
#     for i, (char, color) in enumerate(zip(characters, colors)):
#         stdscr.addstr(0, i, char, color)

#     stdscr.refresh()
#     stdscr.getch()


# curses.wrapper(main)
