#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Speed Control — User-Defined Speed Regulation
=====================================================
Implements precise speed control with multiple modes:
  - Fixed-speed movement
  - Gradual acceleration / deceleration (smooth ramping)
  - Speed profile execution (time-speed sequences)
  - Real-time speed adjustment via keyboard

Features:
  - Set absolute speed (0-200)
  - Smooth acceleration curves (ease-in, ease-out)
  - Speed profiles: ramp-up, ramp-down, S-curve, trapezoidal, sine
  - Independent left/right wheel speed control

Control mode:   Menu-driven + keyboard
Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
from robot_utils import (RobotSerial, RobotMotion, SafetyGuard,
                         print_banner, print_menu, wait_for_keypress)


class SpeedProfile:
    """Generates speed-time profiles for controlled movements."""

    @staticmethod
    def ramp(start_speed, end_speed, duration=2.0, sample_rate=20):
        steps = int(duration * sample_rate)
        for i in range(steps + 1):
            t = i / sample_rate
            fraction = t / duration
            speed = start_speed + (end_speed - start_speed) * fraction
            yield t, int(speed)

    @staticmethod
    def trapezoidal(target_speed, duration=4.0,
                    ramp_up_ratio=0.25, ramp_down_ratio=0.25, sample_rate=20):
        ramp_up_time = duration * ramp_up_ratio
        ramp_down_time = duration * ramp_down_ratio
        cruise_time = duration - ramp_up_time - ramp_down_time
        current_time = 0.0
        steps = int(ramp_up_time * sample_rate)
        for i in range(steps + 1):
            t = current_time + i / sample_rate
            fraction = (i / max(steps, 1))
            speed = int(target_speed * fraction)
            yield t, speed
        current_time += ramp_up_time
        steps = int(cruise_time * sample_rate)
        for i in range(1, steps + 1):
            t = current_time + i / sample_rate
            yield t, target_speed
        current_time += cruise_time
        steps = int(ramp_down_time * sample_rate)
        for i in range(steps + 1):
            t = current_time + i / sample_rate
            fraction = 1.0 - (i / max(steps, 1))
            speed = int(target_speed * fraction)
            yield t, speed

    @staticmethod
    def s_curve(target_speed, duration=3.0, sample_rate=20):
        steps = int(duration * sample_rate)
        for i in range(steps + 1):
            t = i / sample_rate
            fraction = t / duration
            eased = fraction ** 2 * (3 - 2 * fraction)
            speed = int(target_speed * eased)
            yield t, speed

    @staticmethod
    def sine_wave(min_speed, max_speed, duration=5.0, frequency=0.5, sample_rate=20):
        amplitude = (max_speed - min_speed) / 2
        offset = (max_speed + min_speed) / 2
        steps = int(duration * sample_rate)
        for i in range(steps + 1):
            t = i / sample_rate
            speed = int(offset + amplitude * math.sin(2 * math.pi * frequency * t))
            yield t, speed

    @staticmethod
    def custom(points, sample_rate=20):
        if len(points) < 2:
            if points:
                yield points[0]
            return
        total_time = points[-1][0]
        steps = int(total_time * sample_rate)
        for i in range(steps + 1):
            t = i / sample_rate
            for j in range(len(points) - 1):
                t0, s0 = points[j]
                t1, s1 = points[j + 1]
                if t0 <= t <= t1:
                    fraction = (t - t0) / (t1 - t0) if t1 > t0 else 0
                    speed = int(s0 + (s1 - s0) * fraction)
                    yield t, speed
                    break
            else:
                if t >= points[-1][0]:
                    yield t, points[-1][1]


class SpeedController:
    """High-level speed controller with profile execution."""

    def __init__(self, motion):
        self.motion = motion
        self.current_speed = 0

    def set_speed(self, speed):
        self.current_speed = speed
        self.motion.forward(speed)

    def stop(self):
        self.current_speed = 0
        self.motion.stop()

    def execute_profile(self, profile_generator):
        print("[PROFILE] Starting speed profile...")
        start = time.time()
        for elapsed, speed in profile_generator:
            target_time = start + elapsed
            now = time.time()
            if target_time > now:
                time.sleep(target_time - now)
            self.motion.forward(abs(speed))
            self.current_speed = speed
            bar_len = int(abs(speed) / 150 * 40)
            bar = '#' * bar_len + '-' * (40 - bar_len)
            print(f"\r  t={elapsed:5.1f}s  speed={speed:+4d}  [{bar}]",
                  end='', flush=True)
        print("\n[PROFILE] Complete.")
        self.motion.stop()


def interactive_speed_mode(sc):
    print("""
  +--------------------------------------------------+
  |       Interactive Speed Control Mode              |
  +--------------------------------------------------+
  |  Enter a speed value (0-200) to set it directly.  |
  |    ramp <target> <sec>   — linear ramp           |
  |    s-curve <target> <sec>— smooth S-curve        |
  |    sine <min> <max> <sec>— sine wave             |
  |    stop / quit                                   |
  +--------------------------------------------------+
""")
    while True:
        try:
            cmd = input("\nSpeed> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('quit', 'exit', 'q'):
                break
            if cmd.lower() == 'stop':
                sc.stop()
                print("[STOP]")
                continue
            parts = cmd.split()
            action = parts[0].lower()
            if action == 'ramp' and len(parts) >= 3:
                target = int(parts[1])
                dur = float(parts[2])
                sc.execute_profile(SpeedProfile.ramp(0, target, dur))
            elif action == 's-curve' and len(parts) >= 3:
                target = int(parts[1])
                dur = float(parts[2])
                sc.execute_profile(SpeedProfile.s_curve(target, dur))
            elif action == 'sine' and len(parts) >= 4:
                lo, hi, dur = int(parts[1]), int(parts[2]), float(parts[3])
                sc.execute_profile(SpeedProfile.sine_wave(lo, hi, dur))
            else:
                speed = int(parts[0])
                sc.set_speed(speed)
                print(f"[SPEED] Set to {speed}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
    sc.stop()


def main():
    print_banner("Robot Speed Control — User-Defined Speed Regulation")
    robot_serial = RobotSerial()
    if not robot_serial.is_connected():
        print("[SIM] Running in simulation mode.\n")
    motion = RobotMotion(robot_serial, min_speed=15, max_speed=200)
    sc = SpeedController(motion)
    safety = SafetyGuard(motion, max_run_time=600)
    safety.start()

    menu_options = [
        ('1', 'Interactive speed control'),
        ('2', 'Demo — Ramp Up (0 -> 150)'),
        ('3', 'Demo — Ramp Down (150 -> 0)'),
        ('4', 'Demo — Trapezoidal Profile'),
        ('5', 'Demo — S-Curve Profile'),
        ('6', 'Demo — Sine Wave Speed'),
        ('7', 'Demo — Custom Waypoint Profile'),
        ('8', 'Demo — Speed Level Steps (1-9)'),
        ('q', 'Quit'),
    ]

    while True:
        print_menu("Speed Control — Main Menu", menu_options)
        choice = input("Select: ").strip().lower()
        if choice == '1':
            interactive_speed_mode(sc)
        elif choice == '2':
            sc.execute_profile(SpeedProfile.ramp(0, 150, 3.0))
        elif choice == '3':
            sc.execute_profile(SpeedProfile.ramp(150, 0, 3.0))
        elif choice == '4':
            sc.execute_profile(SpeedProfile.trapezoidal(120, 6.0, 0.2, 0.3))
        elif choice == '5':
            sc.execute_profile(SpeedProfile.s_curve(130, 4.0))
        elif choice == '6':
            sc.execute_profile(SpeedProfile.sine_wave(20, 150, 8.0, 0.3))
        elif choice == '7':
            pts = [(0, 0), (0.5, 100), (2.0, 100), (4.0, 50), (6.0, 0)]
            sc.execute_profile(SpeedProfile.custom(pts))
        elif choice == '8':
            for i, speed in enumerate([30, 45, 60, 75, 90, 105, 120, 135, 150]):
                print(f"  Level {i+1}: speed = {speed}")
                sc.set_speed(speed)
                time.sleep(1.0)
            sc.stop()
        elif choice == 'q':
            break
        else:
            print("Invalid choice.")
        wait_for_keypress()

    sc.stop()
    safety.stop()
    robot_serial.disconnect()
    print("[EXIT] Speed control ended.")


if __name__ == "__main__":
    main()
