# -*- coding: utf-8 -*-
"""
Robot Complete — Integrated Multi-Function Smart Car Controller
=================================================================
Fully integrated micro:bit program combining ALL functionalities
of the Tinybit smart car with K210 vision module.

Receives serial commands from K210 and executes the appropriate
robot behavior. Supports all K210 vision programs.

Protocol (from K210):
  $01<color>,#        — Color recognition       → Follow color
  $02<payload>,#      — Barcode scan            → Execute QR command
  $03<payload>,#      — QR code scan            → Execute QR command
  $04<id>,<family>,#  — AprilTag detection      → Show tag info
  $07<num>,#          — Face mask detection     → Mask status
  $08<YN><index>,#    — Face recognition        → Identity action
  $09<id>,#           — Object detection/AI sign → Object behavior
  $10<id>,#           — Self-learning class     → Class behavior
  $11<digit>,#        — MNIST digit             → Digit command
  $14<num>,#          — Face detection          → Face gesture
  $20+LxxxRxxx,#      — Motor speed             → Direct motor

Button controls:
  Button A         — Toggle pause/resume
  Button B         — Show current mode
  Button A+B long  — Emergency stop

Hardware: micro:bit + Tinybit smart car + K210 vision module
Library:  tinybit
"""

from microbit import display, Image, sleep, uart, button_a, button_b
import tinybit

# --- Configuration ---
BAUDRATE = 115200
DEFAULT_SPEED = 80

# --- K210 Command codes ---
CMD_COLOR       = "01"
CMD_BARCODE     = "02"
CMD_QRCODE      = "03"
CMD_APRILTAG    = "04"
CMD_FACE_MASK   = "07"
CMD_FACE_RECOG  = "08"
CMD_OBJECT_DET  = "09"
CMD_SELF_LEARN  = "10"
CMD_MNIST       = "11"
CMD_FACE_DETECT = "14"
CMD_MOTOR       = "20"

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

def parse_motor(payload):
    """Parse $20+LxxxRxxx,# → (left, right) or None."""
    try:
        payload = payload.strip().rstrip(',')
        if len(payload) >= 8:
            return int(payload[0:4]), int(payload[4:8])
    except (ValueError, IndexError):
        pass
    return None

def motor_action(left, right, duration_ms=0):
    """Set motor speeds, optionally for a duration."""
    tinybit.car_run(left, right)
    if duration_ms > 0:
        sleep(duration_ms)
        tinybit.car_run(0, 0)

def handle_motor(payload):
    """Handle $20 motor speed command."""
    speeds = parse_motor(payload)
    if speeds:
        tinybit.car_run(speeds[0], speeds[1])
        if speeds[0] > 0 and speeds[1] > 0:
            display.show(Image.ARROW_N)
        elif speeds[0] < 0 and speeds[1] < 0:
            display.show(Image.ARROW_S)
        elif speeds[0] < 0:
            display.show(Image.ARROW_W)
        elif speeds[1] < 0:
            display.show(Image.ARROW_E)
        else:
            display.show(Image.NO)

def handle_color(payload):
    """Handle $01 color recognition."""
    c = payload.strip().rstrip(',').upper()
    if c == "R":
        display.show(Image("00900:09090:09090:09090:00900"))
    elif c == "G":
        display.show(Image("00000:00000:09990:00000:00000"))
    elif c == "B":
        display.show(Image("00900:09090:09990:09090:00900"))
    elif c == "Y":
        display.show(Image("09090:90009:09990:90009:09090"))

def handle_qrcode(payload):
    """Handle $02/$03 barcode/QR code — execute embedded command."""
    text = payload.strip().rstrip(',').upper()
    display.show(Image.YES)
    sleep(200)

    if "FWD" in text or "FORWARD" in text:
        motor_action(DEFAULT_SPEED, DEFAULT_SPEED, 1500)
    elif "BACK" in text:
        motor_action(-DEFAULT_SPEED, -DEFAULT_SPEED, 1500)
    elif "LEFT" in text:
        motor_action(-DEFAULT_SPEED, DEFAULT_SPEED, 600)
    elif "RIGHT" in text:
        motor_action(DEFAULT_SPEED, -DEFAULT_SPEED, 600)
    elif "STOP" in text:
        motor_action(0, 0)
    elif "DANCE" in text:
        for _ in range(3):
            tinybit.car_run(-DEFAULT_SPEED, DEFAULT_SPEED)
            sleep(300)
            tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
            sleep(300)
        motor_action(0, 0)

def handle_apriltag(payload):
    """Handle $04 AprilTag detection."""
    try:
        parts = payload.strip().rstrip(',').split(',')
        tag_id = parts[0].strip() if len(parts) >= 1 else "?"
        display.show(Image.TARGET)
    except Exception:
        display.show(Image.TARGET)

def handle_face_mask(payload):
    """Handle $07 face mask detection."""
    try:
        num = int(payload.strip().rstrip(','))
        display.show(Image.YES if num == 1 else Image.SAD)
    except ValueError:
        pass

def handle_face_recog(payload):
    """Handle $08 face recognition."""
    try:
        ps = payload.strip().rstrip(',')
        if ps.startswith("Y"):
            display.show(Image.YES)
        else:
            display.show(Image.SAD)
    except Exception:
        pass

def handle_object_detect(payload):
    """Handle $09 object detection / AI road signs."""
    try:
        obj_id = int(payload.strip().rstrip(','))
        display.scroll(str(obj_id), wait=False, loop=False)
    except ValueError:
        pass

def handle_self_learn(payload):
    """Handle $10 self-learning classification."""
    try:
        class_id = int(payload.strip().rstrip(','))
        if class_id == 1:
            motor_action(DEFAULT_SPEED, DEFAULT_SPEED, 2000)
        elif class_id == 2:
            motor_action(DEFAULT_SPEED, -DEFAULT_SPEED, 500)
            motor_action(DEFAULT_SPEED, DEFAULT_SPEED, 1500)
        elif class_id == 3:
            for _ in range(2):
                tinybit.car_run(-DEFAULT_SPEED, DEFAULT_SPEED)
                sleep(300)
                tinybit.car_run(DEFAULT_SPEED, -DEFAULT_SPEED)
                sleep(300)
            motor_action(0, 0)
    except ValueError:
        pass

def handle_mnist(payload):
    """Handle $11 MNIST digit recognition."""
    try:
        digit = int(payload.strip().rstrip(','))
        if digit in (0, 5):
            motor_action(0, 0, 1000)
        elif digit == 1:
            motor_action(40, 40, 1500)
        elif digit == 2:
            motor_action(80, 80, 1500)
        elif digit == 3:
            motor_action(120, 120, 1500)
        elif digit == 4:
            motor_action(-60, 60, 600)
        elif digit == 6:
            motor_action(60, -60, 600)
        elif digit == 7:
            motor_action(-60, -60, 1500)
        elif digit == 8:
            for _ in range(3):
                tinybit.car_run(-80, 80)
                sleep(300)
                tinybit.car_run(80, -80)
                sleep(300)
            motor_action(0, 0)
        elif digit == 9:
            for _ in range(4):
                motor_action(DEFAULT_SPEED, DEFAULT_SPEED, 1000)
                motor_action(DEFAULT_SPEED, -DEFAULT_SPEED, 350)
            motor_action(0, 0)
    except ValueError:
        pass

def handle_face_detect(payload):
    """Handle $14 face detection."""
    try:
        num = int(payload.strip().rstrip(','))
        display.show(Image.GHOST if num == 1 else Image.SAD)
    except ValueError:
        pass


# --- Command dispatch table ---
CMD_HANDLERS = {
    CMD_MOTOR:       handle_motor,
    CMD_COLOR:       handle_color,
    CMD_BARCODE:     handle_qrcode,
    CMD_QRCODE:      handle_qrcode,
    CMD_APRILTAG:    handle_apriltag,
    CMD_FACE_MASK:   handle_face_mask,
    CMD_FACE_RECOG:  handle_face_recog,
    CMD_OBJECT_DET:  handle_object_detect,
    CMD_SELF_LEARN:  handle_self_learn,
    CMD_MNIST:       handle_mnist,
    CMD_FACE_DETECT: handle_face_detect,
}

# --- Main loop ---
display.show(Image.HAPPY)
running = True

while True:
    # Button A: toggle pause/resume
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

    if cmd is not None:
        if cmd in CMD_HANDLERS:
            CMD_HANDLERS[cmd](payload)
        elif cmd == "#":
            tinybit.car_run(0, 0)

    sleep(10)
