#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Basic Move — Fundamental Motion Control
==============================================
Implements core robot movements: forward, backward,
left turn, right turn, and stop.

Control mode:   Keyboard (real-time)
Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)

Controls:
  W / Up     — Forward
  S / Down   — Backward
  A / Left   — Turn left
  D / Right  — Turn right
  Space / X  — Stop
  Q / Esc    — Quit
  1-9        — Speed level (1 = slowest, 9 = fastest)
"""

import sys
import time
import threading
from robot_utils import RobotSerial, RobotMotion, SafetyGuard, print_banner


class KeyboardController:
    """Non-blocking keyboard input listener (Windows / Unix)."""

    def __init__(self):
        self._running = False
        self._last_key = None
        self._thread = None
        try:
            import msvcrt
            self._getch = self._getch_windows
            self._platform = 'windows'
        except ImportError:
            self._getch = self._getch_unix
            self._platform = 'unix'

    def _getch_windows(self):
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            try:
                return key.decode('utf-8').lower()
            except UnicodeDecodeError:
                return key
        return None

    def _getch_unix(self):
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1).lower()
        return None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _listen(self):
        while self._running:
            key = self._getch()
            if key is not None:
                self._last_key = key
            time.sleep(0.02)

    def get_key(self):
        key = self._last_key
        self._last_key = None
        return key


class BasicMoveController:
    """Basic motion controller — maps keys to robot movements."""

    SPEED_LEVELS = {
        '1': 30, '2': 45, '3': 60, '4': 75, '5': 90,
        '6': 105, '7': 120, '8': 135, '9': 150,
    }

    def __init__(self, motion):
        self.motion = motion
        self.current_speed = 90
        self.current_action = "Stop"
        self.running = True

    def handle_key(self, key):
        if key is None:
            return
        if key in self.SPEED_LEVELS:
            self.current_speed = self.SPEED_LEVELS[key]
            print(f"[SPEED] Level {key} (speed={self.current_speed})")
            return
        if key in ('w', 'up', b'\xe0H'):
            self.motion.forward(self.current_speed)
            self.current_action = "Forward"
        elif key in ('s', 'down', b'\xe0P'):
            self.motion.backward(self.current_speed)
            self.current_action = "Backward"
        elif key in ('a', 'left', b'\xe0K'):
            self.motion.turn_left(self.current_speed)
            self.current_action = "Turn Left"
        elif key in ('d', 'right', b'\xe0M'):
            self.motion.turn_right(self.current_speed)
            self.current_action = "Turn Right"
        elif key in (' ', 'x'):
            self.motion.stop()
            self.current_action = "Stop"
        elif key in ('q', '\x1b'):
            self.running = False
            self.current_action = "Quit"
        else:
            return
        print(f"\r[Action: {self.current_action:12s}] [Speed: {self.current_speed:3d}]  ",
              end='', flush=True)

    def run(self):
        self.running = True
        while self.running:
            key = kb.get_key()
            if key is not None:
                self.handle_key(key)
            time.sleep(0.05)


def main():
    print_banner("Robot Basic Move — Fundamental Motion Control")
    print("""
  +--------------------------------------------------+
  |          Robot Basic Motion Control              |
  +--------------------------------------------------+
  |    W / Up     —  Forward                        |
  |    S / Down   —  Backward                       |
  |    A / Left   —  Turn Left                      |
  |    D / Right  —  Turn Right                     |
  |    X / Space  —  Stop                           |
  |    1 ~ 9      —  Speed Level (slow -> fast)    |
  |    Q / Esc    —  Quit                           |
  +--------------------------------------------------+
""")
    robot_serial = RobotSerial()
    if not robot_serial.is_connected():
        print("\n[TIP] No robot detected. Options:")
        print("  1) Enter serial port manually and retry")
        print("  2) Run in simulation mode (console output only)")
        choice = input("Choose [1/2]: ").strip()
        if choice == '1':
            port = input("Enter serial port (e.g. COM3): ").strip()
            robot_serial.connect(port)
        else:
            print("[SIM] Running in simulation mode.")
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    controller = BasicMoveController(motion)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()
    global kb
    kb = KeyboardController()
    kb.start()
    print("\n[READY] Basic motion control active. Press Q to quit.\n")
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\n[INTERRUPT] User pressed Ctrl+C")
    finally:
        print("\n[CLEANUP] Stopping robot...")
        motion.stop()
        kb.stop()
        safety.stop()
        robot_serial.disconnect()
        print("[EXIT] Basic motion control ended.")


if __name__ == "__main__":
    main()
