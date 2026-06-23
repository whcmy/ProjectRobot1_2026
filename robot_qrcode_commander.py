#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot QR Code Commander — Visual Command Interpretation
=========================================================
The robot reads QR codes / barcodes and executes commands
encoded in them.

Supported QR command formats:
  - FWD:<speed>:<duration>   — Forward at speed for duration
  - BACK:<speed>:<duration>  — Backward
  - LEFT:<speed>:<duration>  — Turn left
  - RIGHT:<speed>:<duration> — Turn right
  - STOP                     — Stop
  - SQUARE:<speed>           — Drive a square
  - CIRCLE:<speed>           — Drive a circle
  - SPEED:<value>            — Set default speed

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class QRCommandParser:
    """Parses QR code payloads into robot commands."""

    @staticmethod
    def parse(payload):
        payload = payload.strip().upper()
        if ':' in payload:
            parts = payload.split(':')
            cmd = parts[0]
            args = parts[1:]
            if cmd == 'FWD':
                s = int(args[0]) if len(args) > 0 else 80
                d = float(args[1]) if len(args) > 1 else 1.0
                return 'forward', {'speed': s, 'duration': d}
            elif cmd == 'BACK':
                s = int(args[0]) if len(args) > 0 else 80
                d = float(args[1]) if len(args) > 1 else 1.0
                return 'backward', {'speed': s, 'duration': d}
            elif cmd == 'LEFT':
                s = int(args[0]) if len(args) > 0 else 60
                d = float(args[1]) if len(args) > 1 else 0.35
                return 'left', {'speed': s, 'duration': d}
            elif cmd == 'RIGHT':
                s = int(args[0]) if len(args) > 0 else 60
                d = float(args[1]) if len(args) > 1 else 0.35
                return 'right', {'speed': s, 'duration': d}
            elif cmd == 'SQUARE':
                s = int(args[0]) if len(args) > 0 else 100
                return 'square', {'speed': s}
            elif cmd == 'CIRCLE':
                s = int(args[0]) if len(args) > 0 else 80
                return 'circle', {'speed': s}
            elif cmd == 'ZIGZAG':
                s = int(args[0]) if len(args) > 0 else 80
                return 'zigzag', {'speed': s}
            elif cmd == 'SPEED':
                s = int(args[0]) if len(args) > 0 else 80
                return 'set_speed', {'speed': s}
        if payload == 'STOP':
            return 'stop', {}
        return 'unknown', {'raw': payload}


class QRCommandExecutor:
    """Executes commands decoded from QR codes."""

    def __init__(self, motion):
        self.motion = motion
        self.default_speed = 80
        self.command_history = []

    def execute(self, command_type, params):
        self.command_history.append((command_type, params))
        print(f"[CMD] {command_type}: {params}")

        if command_type == 'forward':
            s = params.get('speed', self.default_speed)
            d = params.get('duration', 1.0)
            self.motion.move(self.motion.FORWARD, s, d)
        elif command_type == 'backward':
            s = params.get('speed', self.default_speed)
            d = params.get('duration', 1.0)
            self.motion.move(self.motion.BACKWARD, s, d)
        elif command_type == 'left':
            s = params.get('speed', 60)
            d = params.get('duration', 0.35)
            self.motion.move(self.motion.LEFT, s, d)
        elif command_type == 'right':
            s = params.get('speed', 60)
            d = params.get('duration', 0.35)
            self.motion.move(self.motion.RIGHT, s, d)
        elif command_type == 'stop':
            self.motion.stop()
        elif command_type == 'square':
            s = params.get('speed', self.default_speed)
            self._exec_square(s)
        elif command_type == 'circle':
            s = params.get('speed', 80)
            self._exec_circle(s)
        elif command_type == 'zigzag':
            s = params.get('speed', 80)
            self._exec_zigzag(s)
        elif command_type == 'set_speed':
            self.default_speed = params.get('speed', 80)
            print(f"  Default speed set to {self.default_speed}")
        elif command_type == 'unknown':
            print(f"  [UNKNOWN] Cannot interpret: {params.get('raw', '')}")

    def _exec_square(self, speed):
        turn = 0.35
        for _ in range(4):
            self.motion.move(self.motion.FORWARD, speed, 1.5)
            self.motion.move(self.motion.RIGHT, speed, turn)

    def _exec_circle(self, speed):
        self.motion.steer(speed, 0.3)
        time.sleep(6.0)
        self.motion.stop()

    def _exec_zigzag(self, speed):
        turn = 0.35
        for i in range(3):
            self.motion.move(self.motion.FORWARD, speed, 1.2)
            if i % 2 == 0:
                self.motion.move(self.motion.RIGHT, speed, turn)
            else:
                self.motion.move(self.motion.LEFT, speed, turn)


def run_simulation_demo(motion):
    print_banner("Simulated QR Code Commander Demo")
    qr_codes = [
        "FWD:100:2.0", "STOP", "RIGHT:60:0.5", "FWD:80:1.5",
        "STOP", "LEFT:60:0.5", "SQUARE:90", "CIRCLE:70", "STOP",
    ]
    executor = QRCommandExecutor(motion)
    for i, qr_text in enumerate(qr_codes):
        print(f"\n--- Scanning QR code #{i+1} ---")
        print(f"  QR Content: \"{qr_text}\"")
        cmd_type, params = QRCommandParser.parse(qr_text)
        executor.execute(cmd_type, params)
        time.sleep(1.5)
    print("\n[DONE] All QR commands executed.")


def run_interactive_mode(motion):
    print_banner("Interactive QR Commander")
    print("Type QR code payload strings to simulate scanning.")
    print("  FWD:<speed>:<duration>   BACK:<speed>:<duration>")
    print("  LEFT:<speed>:<duration>  RIGHT:<speed>:<duration>")
    print("  STOP   SQUARE:<speed>    CIRCLE:<speed>")
    print("  'quit' to exit.\n")
    executor = QRCommandExecutor(motion)
    while True:
        try:
            qr_text = input("QR> ").strip()
            if not qr_text:
                continue
            if qr_text.lower() in ('quit', 'exit', 'q'):
                break
            cmd_type, params = QRCommandParser.parse(qr_text)
            executor.execute(cmd_type, params)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
    motion.stop()


def main():
    print_banner("Robot QR Code Commander — Visual Command Interpretation")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    menu_options = [
        ('1', 'Run simulation demo (pre-recorded QR codes)'),
        ('2', 'Interactive mode (type QR payloads manually)'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("QR Code Commander — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == '2':
            run_interactive_mode(motion)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] QR Code commander ended.")


if __name__ == "__main__":
    main()
