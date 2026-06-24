# -*- coding: utf-8 -*-
"""
Robot QR Code Commander — Visual QR/Barcode Command Execution
===============================================================
Receives QR code / barcode payloads from K210 and executes
the commands encoded in them.

Works with K210 source: 2.2_3.2_find_barcodes.py or 2.2_3.3_find_qrcodes.py

Protocol (from K210):
  $02<payload>,#  — Barcode payload (raw text)
  $03<payload>,#  — QR code payload (raw text)

Supported QR/Barcode text commands:
  FWD:<speed>       — Forward at speed
  BACK:<speed>      — Backward at speed
  LEFT:<speed>      — Turn left
  RIGHT:<speed>     — Turn right
  STOP              — Stop
  SQUARE            — Drive square pattern
  CIRCLE            — Drive circle pattern
  DANCE             — Wiggle dance

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 80

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

def execute_qr_command(text):
    """Parse and execute a QR/barcode text command."""
    text = text.strip().upper()
    parts = text.split(':')

    cmd = parts[0]
    speed = DEFAULT_SPEED
    if len(parts) > 1:
        try:
            speed = int(parts[1])
        except ValueError:
            speed = DEFAULT_SPEED

    if cmd == "FWD" or cmd == "FORWARD":
        tinybit.car_run(speed, speed)
        display.show(Image.ARROW_N)
        sleep(1500)

    elif cmd == "BACK" or cmd == "BACKWARD":
        tinybit.car_run(-speed, -speed)
        display.show(Image.ARROW_S)
        sleep(1500)

    elif cmd == "LEFT":
        tinybit.car_run(-speed, speed)
        display.show(Image.ARROW_W)
        sleep(600)

    elif cmd == "RIGHT":
        tinybit.car_run(speed, -speed)
        display.show(Image.ARROW_E)
        sleep(600)

    elif cmd == "STOP":
        tinybit.car_run(0, 0)
        display.show(Image.NO)

    elif cmd == "SQUARE":
        for _ in range(4):
            tinybit.car_run(speed, speed)
            sleep(1500)
            tinybit.car_run(speed, -speed)
            sleep(350)
        tinybit.car_run(0, 0)

    elif cmd == "CIRCLE":
        for _ in range(20):
            tinybit.car_run(speed, speed // 2)
            sleep(150)
        tinybit.car_run(0, 0)

    elif cmd == "DANCE":
        for _ in range(3):
            tinybit.car_run(-speed, speed)
            sleep(300)
            tinybit.car_run(speed, -speed)
            sleep(300)
        tinybit.car_run(0, 0)

    else:
        # Unknown command — scroll it on LED
        display.scroll(text[:10])
        tinybit.car_run(0, 0)

    tinybit.car_run(0, 0)


# --- Main loop ---
display.show(Image.HAPPY)
running = True

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

    if cmd == "02" or cmd == "03":
        # Barcode or QR code detected
        text = payload.strip().rstrip(',')
        if text:
            display.show(Image.YES)
            sleep(100)
            execute_qr_command(text)

    elif cmd == "#":
        tinybit.car_run(0, 0)

    sleep(20)
