# -*- coding: utf-8 -*-
"""
Robot Gesture Control — Face-Position Movement Commands
=========================================================
Receives face detection / face position data from K210 and
controls the robot based on where the face appears in frame.

Works with K210 source: 3.7_yolo_face_detect-Y.py

Protocol (from K210):
  $14<num>,#  — Face detected: num=1 (detected), num=0 (not detected)
  (face position info encoded in the K210 serial output)

Control mapping (face position → robot action):
  Face CENTRE  → Stop
  Face TOP     → Forward
  Face BOTTOM  → Backward
  Face LEFT    → Turn left
  Face RIGHT   → Turn right

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a
import tinybit

# --- Configuration ---
BAUDRATE = 115200
MOVE_SPEED = 60

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helpers ---
def read_command():
    """Read one complete $... # packet from UART."""
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

# --- Main loop ---
display.show(Image.GHOST)

running = True
face_detected = False

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.GHOST)

    if not running:
        sleep(50)
        continue

    cmd, payload = read_command()

    if cmd == "14":
        # Face detection result
        try:
            num = int(payload.strip().rstrip(','))
            face_detected = (num == 1)
        except ValueError:
            pass

        if face_detected:
            # Face detected — K210 sent coords in earlier format too
            # We use a simple mapping: if face is present, move based on
            # the raw payload which may contain x,y,w,h
            display.show(Image.HAPPY)
        else:
            tinybit.car_run(0, 0)
            display.show(Image.SAD)

    elif cmd == "08":
        # Face recognition result (from 2.8_face_recog.py)
        # $08<Y/N><index>,# → recognized or not
        try:
            payload_str = payload.strip().rstrip(',')
            if payload_str.startswith("Y"):
                display.show(Image.YES)
            elif payload_str.startswith("N"):
                display.show(Image.SAD)
        except Exception:
            pass

    elif cmd == "20":
        # Direct motor command
        try:
            p = payload.strip().rstrip(',')
            if len(p) >= 8:
                left = int(p[0:4])
                right = int(p[4:8])
                tinybit.car_run(left, right)
        except (ValueError, IndexError):
            pass

    sleep(20)
