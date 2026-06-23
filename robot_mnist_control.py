#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot MNIST Control — Handwritten Digit Command Interface
===========================================================
Uses handwritten digit recognition to control the robot.
Show a digit to the camera and the robot executes the
corresponding command.

Digit -> Command mapping:
  0 — Stop          5 — Stop
  1 — Forward Slow  6 — Turn Right
  2 — Forward Med   7 — Backward
  3 — Forward Fast  8 — Dance
  4 — Turn Left     9 — Autonomous mode

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class MNISTController:
    """Controls the robot based on recognised handwritten digits."""

    DIGIT_COMMANDS = {
        0: ('stop', 0, "Stop"),
        1: ('forward', 40, "Forward — Slow"),
        2: ('forward', 80, "Forward — Medium"),
        3: ('forward', 120, "Forward — Fast"),
        4: ('turn_left', 60, "Turn Left"),
        5: ('stop', 0, "Stop"),
        6: ('turn_right', 60, "Turn Right"),
        7: ('backward', 60, "Backward"),
        8: ('dance', 80, "Dance!"),
        9: ('auto', 80, "Autonomous Mode"),
    }

    def __init__(self, motion):
        self.motion = motion
        self.last_digit = None
        self.command_count = {}
        self.autonomous_mode = False

    def execute_digit(self, digit):
        if digit not in self.DIGIT_COMMANDS:
            return
        cmd, speed, description = self.DIGIT_COMMANDS[digit]
        self.command_count[digit] = self.command_count.get(digit, 0) + 1
        print(f"\n[DIGIT] {digit} -> {description}")

        if cmd == 'stop':
            self.motion.stop()
        elif cmd == 'forward':
            self.motion.forward(speed)
            time.sleep(1.0)
            self.motion.stop()
        elif cmd == 'backward':
            self.motion.backward(speed)
            time.sleep(1.0)
            self.motion.stop()
        elif cmd == 'turn_left':
            self.motion.turn_left(speed)
            time.sleep(0.5)
            self.motion.stop()
        elif cmd == 'turn_right':
            self.motion.turn_right(speed)
            time.sleep(0.5)
            self.motion.stop()
        elif cmd == 'dance':
            for _ in range(3):
                self.motion.turn_left(80)
                time.sleep(0.3)
                self.motion.turn_right(80)
                time.sleep(0.3)
            self.motion.stop()
        elif cmd == 'auto':
            self.autonomous_mode = not self.autonomous_mode
            status = "ON" if self.autonomous_mode else "OFF"
            print(f"  Autonomous mode: {status}")

    def show_stats(self):
        if not self.command_count:
            print("No digits recognised yet.")
            return
        print("\nDigit Recognition Stats:")
        for d in range(10):
            count = self.command_count.get(d, 0)
            desc = self.DIGIT_COMMANDS[d][2]
            bar = '#' * min(count, 30)
            print(f"  {d}: {count:3d} {bar} -> {desc}")


def run_simulation_demo(motion):
    print_banner("Simulated MNIST Digit Control Demo")
    controller = MNISTController(motion)
    digits = [1, 2, 3, 4, 6, 7, 5, 8, 0]
    for digit in digits:
        controller.execute_digit(digit)
        time.sleep(2.0)
    motion.stop()
    print("\n[DONE] MNIST control demo complete.")


def run_interactive_mode(motion):
    print_banner("Interactive MNIST Control")
    print("Type a digit (0-9) to simulate handwritten digit recognition.")
    print("  stats / quit\n")
    controller = MNISTController(motion)
    while True:
        try:
            cmd = input("Digit> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('quit', 'exit', 'q'):
                break
            if cmd.lower() == 'stats':
                controller.show_stats()
                continue
            digit = int(cmd)
            if 0 <= digit <= 9:
                controller.execute_digit(digit)
            else:
                print("  Enter a digit 0-9.")
        except (KeyboardInterrupt, EOFError):
            break
        except ValueError:
            print("  Invalid input.")
    motion.stop()


def main():
    print_banner("Robot MNIST Control — Handwritten Digit Command Interface")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()
    controller = MNISTController(motion)

    menu_options = [
        ('1', 'Simulation demo (digit sequence)'),
        ('2', 'Interactive mode (type digits)'),
        ('3', 'Show digit statistics'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("MNIST Control — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == '2':
            run_interactive_mode(motion)
        elif choice == '3':
            controller.show_stats()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] MNIST control ended.")


if __name__ == "__main__":
    main()
