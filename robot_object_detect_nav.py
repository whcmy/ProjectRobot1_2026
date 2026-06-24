# -*- coding: utf-8 -*-
"""
Robot Object Detection Navigation — Vision-Based Scene Response
=================================================================
Receives VOC20 object detection results from K210 and navigates
based on identified objects.

Works with K210 source: 2.5_3.4_voc20_object_detect.py

Protocol (from K210): $09<id>,#
  id = 0-19  (VOC20 class index)

VOC20 Classes & Robot Behaviors:
  0: aeroplane    → Ignore
  1: bicycle      → Follow slowly
  2: bird         → Stop & wait
  3: boat         → Ignore
  4: bottle       → Push forward
  5: bus          → Avoid (turn right)
  6: car          → Avoid (turn left)
  7: cat          → Approach slowly
  8: chair        → Avoid (turn right)
  9: cow          → Stop & wait
  10: diningtable → Avoid (turn right)
  11: dog         → Approach slowly
  12: horse       → Stop & wait
  13: motorbike   → Follow
  14: person      → Stop & wait
  15: pottedplant → Avoid
  16: sheep       → Stop & wait
  17: sofa        → Avoid
  18: train       → Stop & wait
  19: tvmonitor   → Ignore

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 60

# VOC20 class index → (label, behavior)
VOC_BEHAVIORS = {
    0:  ("aeroplane", "ignore"),
    1:  ("bicycle", "follow"),
    2:  ("bird", "stop_wait"),
    3:  ("boat", "ignore"),
    4:  ("bottle", "push"),
    5:  ("bus", "avoid_right"),
    6:  ("car", "avoid_left"),
    7:  ("cat", "approach_slow"),
    8:  ("chair", "avoid_right"),
    9:  ("cow", "stop_wait"),
    10: ("diningtable", "avoid_right"),
    11: ("dog", "approach_slow"),
    12: ("horse", "stop_wait"),
    13: ("motorbike", "follow"),
    14: ("person", "stop_wait"),
    15: ("pottedplant", "avoid_right"),
    16: ("sheep", "stop_wait"),
    17: ("sofa", "avoid_left"),
    18: ("train", "stop_wait"),
    19: ("tvmonitor", "ignore"),
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

def execute_behavior(behavior):
    """Execute robot behavior based on detected object."""
    if behavior == "ignore":
        pass  # keep current state

    elif behavior == "stop_wait":
        tinybit.car_run(0, 0)
        display.show(Image.NO)
        sleep(1500)

    elif behavior == "follow":
        tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
        display.show(Image.ARROW_N)

    elif behavior == "approach_slow":
        tinybit.car_run(DEFAULT_SPEED // 2, DEFAULT_SPEED // 2)
        display.show(Image.ARROW_N)
        sleep(2000)
        tinybit.car_run(0, 0)

    elif behavior == "avoid_right":
        tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
        display.show(Image.ARROW_E)
        sleep(500)
        tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
        sleep(1000)
        tinybit.car_run(-DEFAULT_SPEED, DEFAULT_SPEED)
        sleep(500)

    elif behavior == "avoid_left":
        tinybit.car_run(-DEFAULT_SPEED, DEFAULT_SPEED)
        display.show(Image.ARROW_W)
        sleep(500)
        tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
        sleep(1000)
        tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
        sleep(500)

    elif behavior == "push":
        tinybit.car_run(DEFAULT_SPEED, DEFAULT_SPEED)
        display.show(Image.ARROW_N)
        sleep(1000)
        tinybit.car_run(0, 0)

# --- Main loop ---
display.show(Image.HAPPY)
running = True
last_object = None

while True:
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.HAPPY)

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "09":
        try:
            obj_id = int(payload.strip().rstrip(','))
            if obj_id in VOC_BEHAVIORS:
                label, behavior = VOC_BEHAVIORS[obj_id]
                if obj_id != last_object:
                    last_object = obj_id
                    display.scroll(label[:5])
                execute_behavior(behavior)
        except ValueError:
            pass

    elif cmd == "#":
        tinybit.car_run(0, 0)

    sleep(20)
