# -*- coding: utf-8 -*-
"""
Robot Voice Command — Serial Text Command Interface
=====================================================
Receives text commands via serial (from K210 or another
module with speech recognition) and executes them.

The K210 sends recognized speech as text over serial.
micro:bit parses the command and controls the robot.

Protocol (from K210 — voice recognition module):
  Raw text strings over serial (no $ prefix for voice data)

Command vocabulary:
  forward / go          — Forward
  backward / back       — Backward
  left / turn left      — Turn left
  right / turn right    — Turn right
  stop / halt           — Stop
  faster                — Increase speed
  slower                — Decrease speed
  dance                 — Wiggle dance
  square                — Drive square path
  circle                — Drive circle path

Also accepts standard protocol: $20+LxxxRxxx,#

Hardware: micro:bit + Tinybit smart car
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 80

# --- Voice command vocabulary ---
VOICE_COMMANDS = {
    "forward":  "forward",
    "go":       "forward",
    "ahead":    "forward",
    "backward": "backward",
    "back":     "backward",
    "reverse":  "backward",
    "left":     "turn_left",
    "right":    "turn_right",
    "stop":     "stop",
    "halt":     "stop",
    "faster":   "faster",
    "speed up": "faster",
    "slower":   "slower",
    "slow down":"slower",
    "dance":    "dance",
    "square":   "square",
    "circle":   "circle",
}

# --- Initialize UART ---
uart.init(baudrate=BAUDRATE)

# --- Helpers ---
def read_all_serial():
    """Read all available serial data as string."""
    data = ""
    while uart.any():
        b = uart.read(1)
        if b:
            try:
                data += chr(b[0])
            except Exception:
                pass
    return data

def parse_protocol(data):
    """Try to parse $<cmd><payload>,# protocol from data.
    Returns list of (cmd, payload) tuples."""
    results = []
    i = 0
    while i < len(data):
        if data[i] == '$':
            end = data.find('#', i)
            if end != -1:
                inner = data[i+1:end]
                if len(inner) >= 2:
                    results.append((inner[0:2], inner[2:]))
                i = end + 1
                continue
        i += 1
    return results

def match_voice_command(text):
    """Match text against voice command vocabulary."""
    text = text.lower().strip()
    # Direct match
    if text in VOICE_COMMANDS:
        return VOICE_COMMANDS[text]
    # Substring match
    for keyword, cmd in VOICE_COMMANDS.items():
        if keyword in text:
            return cmd
    return None

def execute_command(cmd, speed=DEFAULT_SPEED):
    """Execute a parsed command on the robot."""
    if cmd == "forward":
        tinybit.car_run(speed, speed)
        display.show(Image.ARROW_N)
        sleep(1500)

    elif cmd == "backward":
        tinybit.car_run(-speed, -speed)
        display.show(Image.ARROW_S)
        sleep(1500)

    elif cmd == "turn_left":
        tinybit.car_run(-speed, speed)
        display.show(Image.ARROW_W)
        sleep(500)

    elif cmd == "turn_right":
        tinybit.car_run(speed, -speed)
        display.show(Image.ARROW_E)
        sleep(500)

    elif cmd == "stop":
        tinybit.car_run(0, 0)
        display.show(Image.NO)

    elif cmd == "faster":
        # Speed handled in main loop via current_speed variable
        pass

    elif cmd == "slower":
        # Speed handled in main loop via current_speed variable
        pass

    elif cmd == "dance":
        for _ in range(3):
            tinybit.car_run(-speed, speed)
            sleep(300)
            tinybit.car_run(speed, -speed)
            sleep(300)

    elif cmd == "square":
        for _ in range(4):
            tinybit.car_run(speed, speed)
            sleep(1500)
            tinybit.car_run(speed, -speed)
            sleep(350)

    elif cmd == "circle":
        for _ in range(30):
            tinybit.car_run(speed, speed // 3)
            sleep(150)

    tinybit.car_run(0, 0)


# --- Main loop ---
display.show(Image.HEART)
running = True
current_speed = DEFAULT_SPEED

while True:
    # Button A: toggle pause
    if button_a.was_pressed():
        running = not running
        if not running:
            tinybit.car_run(0, 0)
            display.show(Image.NO)
        else:
            display.show(Image.HEART)

    if not running:
        sleep(50)
        continue

    # Read all serial data
    ser_data = read_all_serial()

    if ser_data:
        # Try protocol parsing first ($20+LxxxRxxx,#)
        commands = parse_protocol(ser_data)

        if commands:
            for cmd, payload in commands:
                if cmd == "20":
                    try:
                        p = payload.strip().rstrip(',')
                        if len(p) >= 8:
                            tinybit.car_run(int(p[0:4]), int(p[4:8]))
                    except (ValueError, IndexError):
                        pass
                elif cmd == "#":
                    tinybit.car_run(0, 0)
        else:
            # Try voice command matching
            voice_cmd = match_voice_command(ser_data)
            if voice_cmd:
                if voice_cmd == "faster":
                    current_speed = min(200, current_speed + 20)
                    display.scroll("S" + str(current_speed // 10))
                elif voice_cmd == "slower":
                    current_speed = max(20, current_speed - 20)
                    display.scroll("S" + str(current_speed // 10))
                else:
                    execute_command(voice_cmd, current_speed)

    sleep(30)
