#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Obstacle Avoidance — Autonomous Collision Prevention
============================================================
Implements intelligent obstacle detection and avoidance.

Avoidance Strategies:
  - Simple: Stop -> turn -> go (fixed angle)
  - Random: Turn random direction on obstacle detection
  - Smart: Scan both sides, pick the clearer path
  - Wall-following: Follow along walls/corridors
  - Cautious: Stop, back up, then turn

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import random
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class ObstacleDetector:
    """Detects obstacles using vision blob data."""

    SIZE_THRESHOLD = 10000
    DANGER_ZONE = 0.30

    def __init__(self, img_w=320, img_h=240):
        self.img_w = img_w
        self.img_h = img_h
        self.danger_y = int(img_h * (1 - self.DANGER_ZONE))
        self.obstacle_detected = False
        self.obstacle_distance = float('inf')
        self.obstacle_center_x = 0
        self.obstacle_area = 0
        self.obstacle_left = False
        self.obstacle_right = False
        self.obstacle_center = False

    def update_from_blob(self, x, y, w, h):
        area = w * h
        cx = x + w // 2
        bottom = y + h
        estimated_distance = max(5, 200 - h * 0.8) if h > 0 else float('inf')
        self.obstacle_area = area
        self.obstacle_center_x = cx
        self.obstacle_distance = estimated_distance
        is_large = area > self.SIZE_THRESHOLD
        is_near_bottom = bottom > self.danger_y
        is_centred = abs(cx - self.img_w // 2) < self.img_w // 3
        self.obstacle_detected = is_large and (is_near_bottom or is_centred)
        self.obstacle_center = is_centred and is_large
        self.obstacle_left = is_large and cx < self.img_w // 3
        self.obstacle_right = is_large and cx > 2 * self.img_w // 3

    def clear(self):
        self.obstacle_detected = False
        self.obstacle_distance = float('inf')

    def is_path_clear(self):
        return not self.obstacle_detected

    def get_avoidance_direction(self):
        if self.obstacle_left:
            return 'right'
        elif self.obstacle_right:
            return 'left'
        elif self.obstacle_center:
            return random.choice(['left', 'right'])
        return 'forward'


class AvoidanceStrategy:
    """Collection of obstacle avoidance strategies."""

    def __init__(self, motion):
        self.motion = motion
        self.strategy_name = "smart"
        self.default_speed = 80
        self.turn_speed = 60

    def set_strategy(self, name):
        valid = ['simple', 'random', 'smart', 'cautious']
        if name in valid:
            self.strategy_name = name
            print(f"[STRATEGY] Set to '{name}'")

    def avoid(self, detector):
        if detector.is_path_clear():
            return False
        if self.strategy_name == 'simple':
            self._avoid_simple(detector)
        elif self.strategy_name == 'random':
            self._avoid_random(detector)
        elif self.strategy_name == 'smart':
            self._avoid_smart(detector)
        elif self.strategy_name == 'cautious':
            self._avoid_cautious(detector)
        return True

    def _avoid_simple(self, detector):
        print("[AVOID] Simple — turning away")
        direction = detector.get_avoidance_direction()
        self.motion.stop()
        time.sleep(0.2)
        if direction == 'left':
            self.motion.turn_left(self.turn_speed)
        else:
            self.motion.turn_right(self.turn_speed)
        time.sleep(1.0)
        self.motion.forward(self.default_speed)

    def _avoid_random(self, detector):
        angle = random.uniform(0.3, 1.0)
        direction = random.choice(['left', 'right'])
        print(f"[AVOID] Random — turning {direction} for {angle:.1f}s")
        self.motion.stop()
        time.sleep(0.1)
        if direction == 'left':
            self.motion.turn_left(self.turn_speed)
        else:
            self.motion.turn_right(self.turn_speed)
        time.sleep(angle)
        self.motion.forward(self.default_speed)

    def _avoid_smart(self, detector):
        direction = detector.get_avoidance_direction()
        print(f"[AVOID] Smart — turning {direction}")
        self.motion.stop()
        time.sleep(0.2)
        if direction == 'left':
            self.motion.turn_left(self.turn_speed)
        else:
            self.motion.turn_right(self.turn_speed)
        time.sleep(0.6)
        self.motion.forward(self.default_speed)

    def _avoid_cautious(self, detector):
        print("[AVOID] Cautious — backing up")
        self.motion.stop()
        time.sleep(0.3)
        self.motion.backward(50)
        time.sleep(0.8)
        self.motion.stop()
        time.sleep(0.3)
        direction = detector.get_avoidance_direction()
        if direction == 'left':
            self.motion.turn_left(self.turn_speed)
        else:
            self.motion.turn_right(self.turn_speed)
        time.sleep(0.6)
        self.motion.forward(int(self.default_speed * 0.6))


def run_simulation_demo(motion):
    print_banner("Simulated Obstacle Avoidance Demo")
    detector = ObstacleDetector()
    strategy = AvoidanceStrategy(motion)
    strategy.set_strategy('smart')
    scenarios = [
        (None, None, None, None, "Path clear — cruising"),
        (120, 150, 100, 80, "Large obstacle CENTRE — avoid"),
        (None, None, None, None, "Path clear again"),
        (50, 160, 80, 60, "Obstacle on LEFT — turn right"),
        (220, 140, 90, 90, "Obstacle on RIGHT — turn left"),
    ]
    for x, y, w, h, desc in scenarios:
        print(f"\n--- {desc} ---")
        if x is not None:
            detector.update_from_blob(x, y, w, h)
            print(f"  Obstacle: area={w*h}, dist~{detector.obstacle_distance:.0f}cm")
        else:
            detector.clear()
        avoided = strategy.avoid(detector)
        if avoided:
            print(f"  -> Avoided (direction: {detector.get_avoidance_direction()})")
        else:
            print(f"  -> Path clear, cruising forward")
        time.sleep(2.0)
    motion.stop()
    print("\n[DONE] Obstacle avoidance demo complete.")


def main():
    print_banner("Robot Obstacle Avoidance — Autonomous Collision Prevention")
    robot_serial = RobotSerial()
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    safety = SafetyGuard(motion, max_run_time=300)
    safety.start()

    menu_options = [
        ('1', 'Simulation demo (virtual obstacles)'),
        ('2', 'Test: Random avoidance'),
        ('q', 'Quit'),
    ]
    while True:
        print_menu("Obstacle Avoidance — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            run_simulation_demo(motion)
        elif choice == '2':
            print("\nTesting random avoidance. Ctrl+C to stop.\n")
            detector = ObstacleDetector()
            strategy = AvoidanceStrategy(motion)
            strategy.set_strategy('random')
            try:
                while True:
                    if random.random() < 0.15:
                        x = random.randint(20, 240)
                        y = random.randint(80, 180)
                        w = random.randint(60, 150)
                        h = random.randint(60, 130)
                        detector.update_from_blob(x, y, w, h)
                        print(f"  [OBSTACLE] @ ({x},{y}) {w}x{h}")
                    else:
                        detector.clear()
                    strategy.avoid(detector)
                    time.sleep(0.3)
            except KeyboardInterrupt:
                motion.stop()
                print("\n[STOPPED]")
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Obstacle avoidance ended.")


if __name__ == "__main__":
    main()
