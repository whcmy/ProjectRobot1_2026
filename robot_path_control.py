# -*- coding: utf-8 -*-
"""
Robot Path Control — Predefined Path Execution
================================================
Executes pre-programmed geometric movement paths.
Select a path using micro:bit buttons, then watch
the robot drive it.

Paths:
  Button A (tap): cycle through paths
  Button B (tap): execute selected path
  Button A+B:     emergency stop

Available paths:
  1. Square       — 4 sides, 90° turns
  2. Triangle     — 3 sides, 120° turns
  3. Circle       — Continuous arc
  4. Figure-8     — Two connected arcs
  5. Zigzag       — Serpentine pattern
  6. Spiral       — Expanding spiral (multiple arcs)

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, button_a, button_b, accelerometer
import tinybit

# --- Configuration ---
DEFAULT_SPEED = 80

# Path → LED icon
PATH_ICONS = [
    ("SQUARE", Image.SQUARE),
    ("TRIANGLE", Image("00900:09090:90009:99999:90009")),
    ("CIRCLE", Image("00900:09090:09090:09090:00900")),
    ("FIG-8", Image("09090:90009:99999:90009:09090")),
    ("ZIGZAG", Image("09090:00900:09090:00900:09090")),
    ("SPIRAL", Image("99999:90000:90000:90000:99999")),
]


def execute_path(index):
    """Execute the selected path."""
    if index == 0:  # Square
        for _ in range(4):
            tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
            sleep(1500)
            tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
            sleep(350)
        tinybit.car_run(0, 0)

    elif index == 1:  # Triangle (120° turns)
        for _ in range(3):
            tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
            sleep(1500)
            tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
            sleep(480)  # ~120°
        tinybit.car_run(0, 0)

    elif index == 2:  # Circle
        for _ in range(40):
            tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED // 3)
            sleep(100)
        tinybit.car_run(0, 0)

    elif index == 3:  # Figure-8
        for _ in range(20):
            tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED // 3)
            sleep(100)
        for _ in range(20):
            tinybit.car_run(DEFAULT_SPEED // 3, DEFAULT_SPEED)
            sleep(100)
        tinybit.car_run(0, 0)

    elif index == 4:  # Zigzag
        for i in range(4):
            tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
            sleep(1000)
            if i % 2 == 0:
                tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
            else:
                tinybit.car_run(-DEFAULT_SPEED, DEFAULT_SPEED)
            sleep(350)
        tinybit.car_run(0, 0)

    elif index == 5:  # Spiral
        speed = DEFAULT_SPEED
        for i in range(30):
            turn = max(10, speed // (3 + i // 5))
            tinybit.car_run(speed, turn)
            sleep(120)
        tinybit.car_run(0, 0)


# --- Main loop ---
current_path = 0
num_paths = len(PATH_ICONS)

# Show initial path
name, icon = PATH_ICONS[current_path]
display.show(icon)

while True:
    # Button A: next path
    if button_a.was_pressed():
        current_path = (current_path + 1) % num_paths
        name, icon = PATH_ICONS[current_path]
        display.show(icon)

    # Button B: execute current path
    if button_b.was_pressed():
        name, icon = PATH_ICONS[current_path]
        display.scroll(name[:6])
        sleep(500)
        display.show(icon)
        execute_path(current_path)
        tinybit.car_run(0, 0)
        display.show(icon)

    # Shake: emergency stop
    if accelerometer.was_gesture("shake"):
        tinybit.car_run(0, 0)
        display.show(Image.NO)

    sleep(50)
