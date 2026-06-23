#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Path Control — User-Defined Path Following
==================================================
Implements predefined and custom path execution.
The robot follows geometric paths and user-defined
waypoint sequences.

Supported paths:
  - Square, Rectangle, Triangle, Pentagon, Hexagon
  - Circle, Oval, Figure-8
  - Zigzag, Spiral, Snake
  - Custom waypoint sequences (programmable)

Control mode:   Menu-driven
Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class PathExecutor:
    """Executes robot movement along predefined or custom paths."""

    def __init__(self, motion):
        self.motion = motion
        self._running = False

    def stop(self):
        self._running = False
        self.motion.stop()

    def execute_path(self, path, loop=1, pause_between=0.1):
        self._running = True
        total_steps = len(path) * loop
        step_count = 0
        for lap in range(loop):
            if not self._running:
                break
            print(f"\n--- Lap {lap + 1}/{loop} ---")
            for item in path:
                if not self._running:
                    break
                step_count += 1
                cmd = item[0]
                speed = item[1] if len(item) > 1 else 80
                param = item[2] if len(item) > 2 else 1.0
                if cmd == 'circle':
                    print(f"  [{step_count}/{total_steps}] Arc: speed={speed}, turn_rate={param:.2f}")
                    self.motion.steer(speed, param)
                    time.sleep(param)
                elif cmd == 'pause':
                    print(f"  [{step_count}/{total_steps}] Pause: {param:.1f}s")
                    self.motion.stop()
                    time.sleep(param)
                else:
                    dir_names = {0: 'Forward', 1: 'Backward', 2: 'Left', 3: 'Right'}
                    name = dir_names.get(cmd, str(cmd))
                    print(f"  [{step_count}/{total_steps}] {name}: speed={speed}")
                    self.motion.move(cmd, speed, param)
                if pause_between > 0:
                    time.sleep(pause_between)
        self.motion.stop()
        print(f"\n[PATH] Complete — {step_count} steps executed.")

    def draw_polygon(self, sides, side_time=1.5, speed=90):
        turn_angle = 360.0 / sides
        turn_time = 0.35 * (turn_angle / 90.0)
        path = []
        for _ in range(sides):
            path.append((RobotMotion.FORWARD, speed, side_time))
            path.append((RobotMotion.RIGHT, speed, turn_time))
        print_banner(f"Drawing {sides}-sided Polygon")
        self.execute_path(path)


class PathLibrary:
    """Collection of pre-built robot paths."""

    @staticmethod
    def square(side=2.0, speed=100):
        turn = 0.35
        return [
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
        ]

    @staticmethod
    def rectangle(long_side=3.0, short_side=1.5, speed=100):
        turn = 0.35
        return [
            (RobotMotion.FORWARD, speed, long_side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, short_side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, long_side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, short_side), (RobotMotion.RIGHT, speed, turn),
        ]

    @staticmethod
    def triangle(side=2.0, speed=100):
        turn = 0.35 * (120 / 90.0)
        return [
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
            (RobotMotion.FORWARD, speed, side), (RobotMotion.RIGHT, speed, turn),
        ]

    @staticmethod
    def circle(speed=80, turn_rate=0.3, duration=8.0):
        return [('circle', speed, turn_rate, duration)]

    @staticmethod
    def figure8(speed=80, turn_rate=0.3, duration=10.0):
        half = duration / 2
        return [('circle', speed, turn_rate, half), ('circle', speed, -turn_rate, half)]

    @staticmethod
    def zigzag(segments=4, seg_time=1.5, speed=80):
        path = []
        turn = 0.35
        for i in range(segments):
            path.append((RobotMotion.FORWARD, speed, seg_time))
            if i % 2 == 0:
                path.append((RobotMotion.RIGHT, speed, turn))
                path.append((RobotMotion.FORWARD, speed, seg_time))
                path.append((RobotMotion.LEFT, speed, turn * 2))
            else:
                path.append((RobotMotion.LEFT, speed, turn))
                path.append((RobotMotion.FORWARD, speed, seg_time))
                path.append((RobotMotion.RIGHT, speed, turn * 2))
        return path

    @staticmethod
    def spiral(speed=100, initial_turn=0.1, step_time=1.0, steps=10, increment=0.05):
        path = []
        for i in range(steps):
            turn = min(0.9, initial_turn + i * increment)
            path.append(('circle', speed, turn, step_time))
        return path

    @staticmethod
    def snake(speed=80, amplitude=1.5, periods=3):
        path = []
        for _ in range(periods):
            path.append(('circle', speed, 0.4, amplitude))
            path.append(('circle', speed, -0.4, amplitude))
        return path

    @staticmethod
    def lawn_mower(speed=100, forward_time=2.0, turns=4):
        path = []
        turn = 0.35
        for i in range(turns):
            path.append((RobotMotion.FORWARD, speed, forward_time))
            if i % 2 == 0:
                path.append((RobotMotion.RIGHT, speed, turn))
                path.append((RobotMotion.FORWARD, speed, 0.8))
                path.append((RobotMotion.RIGHT, speed, turn))
            else:
                path.append((RobotMotion.LEFT, speed, turn))
                path.append((RobotMotion.FORWARD, speed, 0.8))
                path.append((RobotMotion.LEFT, speed, turn))
        path.append((RobotMotion.FORWARD, speed, forward_time))
        return path


def build_custom_path():
    print_banner("Custom Path Builder")
    print("  Commands: f=Forward, b=Backward, l=Left, r=Right, c=Circle, p=Pause")
    print("  Format: <command> <speed> <duration>")
    print("  Enter 'done' to finish, 'show' to see current path.\n")
    path = []
    dmap = {'f': 0, 'forward': 0, 'b': 1, 'backward': 1,
            'l': 2, 'left': 2, 'r': 3, 'right': 3,
            'c': 'circle', 'circle': 'circle', 'p': 'pause', 'pause': 'pause'}
    while True:
        cmd = input(f"  Step {len(path)+1}> ").strip().lower()
        if cmd in ('done', 'd', ''):
            break
        if cmd == 'show':
            print(f"  Current path: {len(path)} steps")
            for i, step in enumerate(path):
                print(f"    {i+1}: {step}")
            continue
        parts = cmd.split()
        if len(parts) >= 3 and parts[0] in dmap:
            try:
                path.append((dmap[parts[0]], int(parts[1]), float(parts[2])))
                print(f"    Added: {parts[0]} speed={parts[1]} dur={parts[2]}")
            except ValueError:
                print("    Invalid number format.")
        else:
            print("    Format: <cmd> <speed> <duration>")
    return path


def main():
    print_banner("Robot Path Control — User-Defined Path Following")
    robot_serial = RobotSerial()
    if not robot_serial.is_connected():
        print("[SIM] Running in simulation mode.\n")
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    executor = PathExecutor(motion)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()

    try:
        s = input("Enter speed (30-150, default 90): ").strip()
        speed = int(s) if s else 90
    except ValueError:
        speed = 90

    menu_options = [
        ('1', 'Square Path'), ('2', 'Rectangle Path'), ('3', 'Triangle Path'),
        ('4', 'Circle Path'), ('5', 'Figure-8 Path'), ('6', 'Zigzag Path'),
        ('7', 'Spiral Path'), ('8', 'Snake (S-wave) Path'),
        ('9', 'Lawn Mower Pattern'), ('10', 'Polygon (choose N sides)'),
        ('11', 'Run ALL path demos'), ('12', 'Build & run a custom path'),
        ('q', 'Quit'),
    ]

    while True:
        print_menu("Path Control — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            executor.execute_path(PathLibrary.square(speed=speed))
        elif choice == '2':
            executor.execute_path(PathLibrary.rectangle(speed=speed))
        elif choice == '3':
            executor.execute_path(PathLibrary.triangle(speed=speed))
        elif choice == '4':
            executor.execute_path(PathLibrary.circle(speed=speed, duration=6.0))
        elif choice == '5':
            executor.execute_path(PathLibrary.figure8(speed=speed, duration=8.0))
        elif choice == '6':
            executor.execute_path(PathLibrary.zigzag(speed=speed))
        elif choice == '7':
            executor.execute_path(PathLibrary.spiral(speed=speed))
        elif choice == '8':
            executor.execute_path(PathLibrary.snake(speed=speed))
        elif choice == '9':
            executor.execute_path(PathLibrary.lawn_mower(speed=speed))
        elif choice == '10':
            try:
                sides = int(input("Number of sides (3-12): ").strip())
                executor.draw_polygon(sides, side_time=1.5, speed=speed)
            except ValueError:
                print("Invalid input.")
        elif choice == '11':
            for name, path in [
                ("Square", PathLibrary.square(1.5, speed)),
                ("Triangle", PathLibrary.triangle(1.5, speed)),
                ("Circle", PathLibrary.circle(speed, 0.3, 5.0)),
                ("Figure-8", PathLibrary.figure8(speed, 0.3, 8.0)),
                ("Zigzag", PathLibrary.zigzag(3, 1.2, speed)),
                ("Snake", PathLibrary.snake(speed, 1.5, 3)),
            ]:
                print_banner(f"Path: {name}")
                executor.execute_path(path)
                time.sleep(0.5)
        elif choice == '12':
            custom = build_custom_path()
            if custom:
                loops = input("How many loops? [1]: ").strip()
                loop_count = int(loops) if loops else 1
                executor.execute_path(custom, loop=loop_count)
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    executor.stop()
    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Path control ended.")


if __name__ == "__main__":
    main()
