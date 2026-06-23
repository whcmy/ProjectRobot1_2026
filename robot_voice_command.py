#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Voice Command — Natural Language Interface
==================================================
Provides a natural-language command interface for robot control.
Type commands in plain English and the robot executes them.

Supported Commands:
  - "go forward" / "move ahead" / "forward"
  - "go back" / "backward" / "reverse"
  - "turn left" / "go left" / "left"
  - "turn right" / "go right" / "right"
  - "stop" / "halt" / "freeze"
  - "faster" / "speed up"
  - "slower" / "slow down"
  - "dance" / "celebrate"
  - "square" / "circle" / "zigzag"
  - "patrol" / "autonomous"

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import random
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class CommandVocabulary:
    """Natural-language command vocabulary with fuzzy matching."""

    VOCABULARY = {
        "forward": ("forward", {"speed": 80, "duration": 2.0}),
        "go forward": ("forward", {"speed": 80, "duration": 2.0}),
        "move ahead": ("forward", {"speed": 80, "duration": 2.0}),
        "go straight": ("forward", {"speed": 80, "duration": 2.0}),
        "backward": ("backward", {"speed": 60, "duration": 1.5}),
        "go back": ("backward", {"speed": 60, "duration": 1.5}),
        "reverse": ("backward", {"speed": 60, "duration": 1.5}),
        "left": ("turn_left", {"speed": 60, "duration": 0.35}),
        "turn left": ("turn_left", {"speed": 60, "duration": 0.5}),
        "go left": ("turn_left", {"speed": 60, "duration": 0.35}),
        "right": ("turn_right", {"speed": 60, "duration": 0.35}),
        "turn right": ("turn_right", {"speed": 60, "duration": 0.5}),
        "go right": ("turn_right", {"speed": 60, "duration": 0.35}),
        "stop": ("stop", {}),
        "halt": ("stop", {}),
        "freeze": ("stop", {}),
        "faster": ("speed_up", {}),
        "speed up": ("speed_up", {}),
        "slower": ("speed_down", {}),
        "slow down": ("speed_down", {}),
        "slow": ("set_speed", {"speed": 40}),
        "medium": ("set_speed", {"speed": 80}),
        "fast": ("set_speed", {"speed": 120}),
        "square": ("square", {}),
        "circle": ("circle", {}),
        "zigzag": ("zigzag", {}),
        "dance": ("dance", {}),
        "celebrate": ("dance", {}),
        "patrol": ("patrol", {}),
        "autonomous": ("autonomous", {}),
        "status": ("status", {}),
        "help": ("help", {}),
    }

    @classmethod
    def match(cls, text):
        text = text.strip().lower()
        if text in cls.VOCABULARY:
            return cls.VOCABULARY[text]
        for keyword, action in cls.VOCABULARY.items():
            if keyword in text:
                return action
        return ('unknown', {"raw": text})

    @classmethod
    def list_commands(cls):
        print("\nAvailable Voice Commands:")
        cats = {
            "Movement": ["forward", "backward", "left", "right", "stop"],
            "Speed": ["faster", "slower", "slow", "medium", "fast"],
            "Paths": ["square", "circle", "zigzag"],
            "Special": ["dance", "patrol", "autonomous"],
        }
        for cat, keywords in cats.items():
            print(f"\n  {cat}:")
            for kw in keywords:
                action, _ = cls.VOCABULARY[kw]
                print(f'    "{kw}" -> {action}')


class VoiceCommandExecutor:
    """Executes parsed voice commands on the robot."""

    def __init__(self, motion):
        self.motion = motion
        self.default_speed = 80

    def execute(self, action_type, params):
        print(f"[VOICE] -> {action_type} {params}")
        if action_type == 'forward':
            s = params.get('speed', self.default_speed)
            d = params.get('duration', 2.0)
            self.motion.move(self.motion.FORWARD, s, d)
        elif action_type == 'backward':
            s = params.get('speed', 60)
            d = params.get('duration', 1.5)
            self.motion.move(self.motion.BACKWARD, s, d)
        elif action_type == 'turn_left':
            s = params.get('speed', 60)
            d = params.get('duration', 0.5)
            self.motion.move(self.motion.LEFT, s, d)
        elif action_type == 'turn_right':
            s = params.get('speed', 60)
            d = params.get('duration', 0.5)
            self.motion.move(self.motion.RIGHT, s, d)
        elif action_type == 'stop':
            self.motion.stop()
        elif action_type == 'speed_up':
            self.default_speed = min(150, self.default_speed + 20)
            print(f"  Speed: {self.default_speed}")
        elif action_type == 'speed_down':
            self.default_speed = max(20, self.default_speed - 20)
            print(f"  Speed: {self.default_speed}")
        elif action_type == 'set_speed':
            self.default_speed = params.get('speed', 80)
            print(f"  Speed set to: {self.default_speed}")
        elif action_type == 'dance':
            print("  Dancing!")
            for _ in range(3):
                self.motion.turn_left(80)
                time.sleep(0.3)
                self.motion.turn_right(80)
                time.sleep(0.3)
            self.motion.stop()
        elif action_type == 'square':
            turn = 0.35
            for _ in range(4):
                self.motion.move(self.motion.FORWARD, self.default_speed, 1.5)
                self.motion.move(self.motion.RIGHT, 60, turn)
        elif action_type == 'circle':
            self.motion.steer(self.default_speed, 0.3)
            time.sleep(6.0)
            self.motion.stop()
        elif action_type == 'zigzag':
            turn = 0.35
            for i in range(4):
                self.motion.move(self.motion.FORWARD, self.default_speed, 1.0)
                if i % 2 == 0:
                    self.motion.move(self.motion.RIGHT, 60, turn)
                else:
                    self.motion.move(self.motion.LEFT, 60, turn)
        elif action_type == 'patrol':
            for i in range(6):
                self.motion.move(self.motion.FORWARD, 80, 1.5)
                if i % 2 == 0:
                    self.motion.move(self.motion.RIGHT, 60, 0.35)
                else:
                    self.motion.move(self.motion.LEFT, 60, 0.35)
            self.motion.stop()
        elif action_type == 'autonomous':
            print("  Auto mode: moving randomly for 8 seconds")
            for _ in range(8):
                r = random.random()
                if r < 0.5:
                    self.motion.forward(60)
                elif r < 0.75:
                    self.motion.turn_left(60)
                else:
                    self.motion.turn_right(60)
                time.sleep(1.0)
            self.motion.stop()
        elif action_type == 'status':
            print(f"  Speed: {self.default_speed}")
        elif action_type == 'help':
            CommandVocabulary.list_commands()
        elif action_type == 'unknown':
            print(f'  [UNKNOWN] Command not recognised: "{params.get("raw", "")}"')
            print("  Say 'help' to see available commands.")


def main():
    print_banner("Robot Voice Command — Natural Language Interface")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()
    executor = VoiceCommandExecutor(motion)

    print("""
  +--------------------------------------------------+
  |        Voice Command Interface (Text Mode)       |
  +--------------------------------------------------+
  |  Type a command and press Enter.                 |
  |  Type 'help' to see all available commands.      |
  |  Type 'quit' to exit.                            |
  +--------------------------------------------------+
""")
    while True:
        try:
            cmd = input("Voice> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('quit', 'exit', 'q'):
                break
            action_type, params = CommandVocabulary.match(cmd)
            executor.execute(action_type, params)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")

    motion.stop()
    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Voice command interface ended.")


if __name__ == "__main__":
    main()
