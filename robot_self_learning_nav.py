# -*- coding: utf-8 -*-
"""
Robot Self-Learning Navigation — Trainable Visual Classifier
==============================================================
Receives self-learning classification results from K210 and
executes corresponding navigation behaviors.

Works with K210 source: 2.6_3.5_self_learning.py

Protocol (from K210): $10<class_id>,#
  class_id = 1, 2, or 3

Default class mappings:
  Class 1 → Clear Path → Forward
  Class 2 → Obstacle  → Avoid (turn right)
  Class 3 → Destination → Stop & celebrate

User can retrain these mappings on the K210 by:
  1. Long-press BOOT to enter INIT
  2. Train Class 1-3 with examples
  3. Enter CLASSIFY mode

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 80

# Class → (label, action, speed)
CLASS_MAPPINGS = {
    1: ("Clear Path", "forward", DEFAULT_SPEED),
    2: ("Obstacle", "avoid", DEFAULT_SPEED),
    3: ("Destination", "stop_celebrate", DEFAULT_SPEED),
}

# Class → LED display
CLASS_ICONS = {
    1: Image.ARROW_N,
    2: Image.ARROW_E,
    3: Image.HAPPY,
}

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helpers ---
def read_command():
    buf = ""
    while uart.any():
        b = uart.read(1)
        if b is None:
            continue
        ch = chr(b[0])
        if ch == '$':
            buf = '$'
        elif buf.startswith('$'):
            if ch == '#':
                inner = buf[1:]
                if len(inner) >= 2:
                    return inner[0:2], inner[2:]
                return None, None
            else:
                buf += ch
    return None, None

def execute_class(class_id):
    """Execute the behavior mapped to a self-learned class."""
    if class_id not in CLASS_MAPPINGS:
        return

    label, action, speed = CLASS_MAPPINGS[class_id]

    # Show class icon
    display.show(CLASS_ICONS.get(class_id, Image.HAPPY))

    if action == "forward":
        tinybit.car_run(speed, speed)
        sleep(1500)

    elif action == "avoid":
        # Turn right, go forward, turn left back
        tinybit.car_run(speed, -speed)
        sleep(500)
        tinybit.car_run(speed, speed)
        sleep(1500)
        tinybit.car_run(-speed, speed)
        sleep(500)
        tinybit.car_run(speed, speed)

    elif action == "stop_celebrate":
        tinybit.car_run(0, 0)
        # Celebration wiggle
        for _ in range(2):
            tinybit.car_run(-speed, speed)
            sleep(300)
            tinybit.car_run(speed, -speed)
            sleep(300)

    elif action == "turn_left":
        tinybit.car_run(-speed, speed)
        sleep(500)

    elif action == "turn_right":
        tinybit.car_run(speed, -speed)
        sleep(500)

    elif action == "backward":
        tinybit.car_run(-speed, -speed)
        sleep(1500)

    tinybit.car_run(0, 0)


# --- Main loop ---
display.show(Image.HEART)
running = True
last_class = None

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.HEART)

    # Button B: show last class
    if button_b.was_pressed() and last_class is not None:
        label, _, _ = CLASS_MAPPINGS.get(last_class, ("?", "", 0))
        display.scroll(label)

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "10":
        try:
            class_id = int(payload.strip().rstrip(','))
            if class_id in CLASS_MAPPINGS and class_id != last_class:
                last_class = class_id
                execute_class(class_id)
        except ValueError:
            pass

    elif cmd == "#":
        tinybit.car_run(0, 0)

    sleep(20)
