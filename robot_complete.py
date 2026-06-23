#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Complete — Integrated Multi-Function Smart Car Controller
=================================================================
Fully integrated robot controller combining ALL functionalities:

  [1]  Basic Movement       — Keyboard-driven forward/backward/turn/stop
  [2]  Direction Control    — Precise angle & compass navigation
  [3]  Speed Control        — Speed profiles, ramps, and curves
  [4]  Path Control         — Predefined & custom geometric paths
  [5]  Colour Tracking      — Vision-based object following (PID)
  [6]  Line Following       — Colour-based path tracking (PID)
  [7]  AprilTag Navigation  — Fiducial marker guidance
  [8]  QR Code Commander    — Visual QR/barcode command interpretation
  [9]  Face Recognition     — Identity-based access & behaviour
  [10] Object Detection Nav — VOC20 object-based navigation
  [11] Gesture Control      — Face-position gesture interface
  [12] MNIST Digit Control  — Handwritten digit commands
  [13] Obstacle Avoidance   — Autonomous collision prevention
  [14] Voice Command        — Natural-language command interface
  [15] Autonomous Explore   — Environment mapping & exploration
  [16] Self-Learning Nav    — Trainable visual classifier navigation

Target hardware: micro:bit + K210 smart car
Communication:  Serial (UART)
"""

import sys
import time
import math
import random
import os
from robot_utils import (RobotSerial, RobotMotion, PID, PIDController2D,
                         PathPlanner, SafetyGuard, RobotLogger,
                         print_banner, print_menu, wait_for_keypress)


class CompleteRobotController:
    """Master controller that integrates all robot functionalities."""

    def __init__(self):
        self.robot_serial = None
        self.motion = None
        self.safety = None
        self.logger = RobotLogger()
        self.current_mode = None
        self.running = True
        self.speed = 80

    def initialise(self, port=None):
        print_banner("Robot Complete — Initialising")
        self.robot_serial = RobotSerial(port=port)
        self.motion = RobotMotion(self.robot_serial, min_speed=15, max_speed=200)
        self.safety = SafetyGuard(self.motion, max_run_time=1200)
        self.safety.start()
        if self.robot_serial.is_connected():
            self.logger.info("Robot connected and ready.")
        else:
            self.logger.warn("No robot detected — running in simulation mode.")
        self.logger.info("Initialisation complete.")

    def shutdown(self):
        print_banner("Robot Complete — Shutting Down")
        self.running = False
        if self.motion:
            self.motion.stop()
        if self.safety:
            self.safety.stop()
        if self.robot_serial:
            self.robot_serial.disconnect()
        self.logger.info("All systems stopped. Goodbye!")

    # ======================================================================
    # Mode 1: Basic Movement
    # ======================================================================
    def mode_basic_move(self):
        print_banner("Mode 1: Basic Movement")
        print("  W=Forward  S=Backward  A=Left  D=Right  X=Stop  1-9=Speed  Q=Back")
        try:
            import msvcrt
            while self.running:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    if key == 'w':
                        self.motion.forward(self.speed)
                    elif key == 's':
                        self.motion.backward(self.speed)
                    elif key == 'a':
                        self.motion.turn_left(self.speed)
                    elif key == 'd':
                        self.motion.turn_right(self.speed)
                    elif key in ('x', ' '):
                        self.motion.stop()
                    elif key in '123456789':
                        self.speed = int(key) * 15 + 15
                        print(f"\r  Speed: {self.speed}  ", end='', flush=True)
                    elif key == 'q':
                        break
                time.sleep(0.05)
        except ImportError:
            for _ in range(4):
                self.motion.forward(self.speed)
                time.sleep(1.0)
                self.motion.turn_right(60)
                time.sleep(0.35)
        self.motion.stop()
        print("\n  Exited basic movement mode.")

    # ======================================================================
    # Mode 2: Direction Control
    # ======================================================================
    def mode_direction_control(self):
        print_banner("Mode 2: Direction Control")
        print("  Enter angle (0-360) or compass (N/NE/E/SE/S/SW/W/NW)")
        print("  Format: <angle|compass> [speed] [duration]")
        print("  'stop' / 'quit' to exit.\n")
        compass = {'n': 0, 'ne': 45, 'e': 90, 'se': 135,
                   's': 180, 'sw': 225, 'w': 270, 'nw': 315}
        while self.running:
            try:
                cmd = input("Direction> ").strip().lower()
                if not cmd:
                    continue
                if cmd in ('quit', 'q'):
                    break
                if cmd == 'stop':
                    self.motion.stop()
                    continue
                parts = cmd.split()
                direction = parts[0]
                sp = int(parts[1]) if len(parts) > 1 else self.speed
                dur = float(parts[2]) if len(parts) > 2 else 1.0
                if direction in compass:
                    angle = compass[direction]
                else:
                    angle = float(direction)
                rad = math.radians(angle % 360)
                turn = math.sin(rad)
                fwd = math.cos(rad)
                left = int(sp * fwd + sp * turn)
                right = int(sp * fwd - sp * turn)
                left = max(-200, min(200, left))
                right = max(-200, min(200, right))
                self.motion.set_wheel_speeds(left, right)
                print(f"  angle={angle:6.1f} deg -> L={left:+4d} R={right:+4d}")
                if dur > 0:
                    time.sleep(dur)
                    self.motion.stop()
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"  Error: {e}")
        self.motion.stop()

    # ======================================================================
    # Mode 3: Speed Control
    # ======================================================================
    def mode_speed_control(self):
        print_banner("Mode 3: Speed Control")
        print("  Enter speed (0-200). 'ramp <t> <s>' / 's-curve <t> <s>' / 'stop' / 'quit'\n")
        while self.running:
            try:
                cmd = input("Speed> ").strip().lower()
                if not cmd:
                    continue
                if cmd in ('quit', 'q'):
                    break
                if cmd == 'stop':
                    self.motion.stop()
                    continue
                parts = cmd.split()
                if parts[0] == 'ramp' and len(parts) >= 3:
                    target = int(parts[1])
                    dur = float(parts[2])
                    steps = int(dur * 20)
                    for i in range(steps + 1):
                        s = int(target * (i / steps))
                        self.motion.forward(s)
                        print(f"\r  Ramping: {s:3d}  ", end='', flush=True)
                        time.sleep(0.05)
                    print()
                    self.motion.stop()
                elif parts[0] == 's-curve' and len(parts) >= 3:
                    target = int(parts[1])
                    dur = float(parts[2])
                    steps = int(dur * 20)
                    for i in range(steps + 1):
                        t = i / steps
                        s = int(target * (t ** 2 * (3 - 2 * t)))
                        self.motion.forward(s)
                        print(f"\r  S-curve: {s:3d}  ", end='', flush=True)
                        time.sleep(0.05)
                    print()
                    self.motion.stop()
                else:
                    speed = int(parts[0])
                    self.speed = speed
                    self.motion.forward(speed)
                    print(f"  Speed set to {speed}")
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"  Error: {e}")
        self.motion.stop()

    # ======================================================================
    # Mode 4: Path Control
    # ======================================================================
    def mode_path_control(self):
        print_banner("Mode 4: Path Control")
        paths = {
            '1': ('Square', PathPlanner.square(side_time=1.5, speed=self.speed)),
            '2': ('Circle', PathPlanner.circle(speed=self.speed, duration=6.0)),
            '3': ('Figure-8', PathPlanner.figure8(speed=self.speed, duration=8.0)),
            '4': ('Zigzag', PathPlanner.zigzag(segments=4, speed=self.speed)),
            '5': ('Spiral', PathPlanner.spiral(speed=self.speed, steps=8)),
        }
        print("  Select a path:")
        for key, (name, _) in paths.items():
            print(f"    [{key}] {name}")
        print("    [q] Back\n")
        choice = input("Path> ").strip().lower()
        if choice in paths:
            name, path = paths[choice]
            print(f"\n  Executing: {name}")
            self._execute_path(path)
        elif choice == 'q':
            return

    def _execute_path(self, path):
        for i, item in enumerate(path):
            if not self.running:
                break
            cmd = item[0]
            speed = item[1] if len(item) > 1 else self.speed
            param = item[2] if len(item) > 2 else 1.0
            if cmd == 'circle':
                print(f"  Step {i+1}: arc turn_rate={param:.2f}")
                self.motion.steer(speed, param)
                time.sleep(param)
            else:
                dir_names = {0: 'Fwd', 1: 'Back', 2: 'Left', 3: 'Right'}
                print(f"  Step {i+1}: {dir_names.get(cmd, str(cmd))}")
                self.motion.move(cmd, speed, param)
            time.sleep(0.1)
        self.motion.stop()
        print("  Path complete.")

    # ======================================================================
    # Mode 5: Colour Tracking (simulation)
    # ======================================================================
    def mode_color_tracking(self):
        print_banner("Mode 5: Colour Tracking")
        print("  [SIM] Virtual target moving in a circle — PID tracking.")
        print("  Press Ctrl+C to stop.\n")
        pid = PIDController2D(160, 120, 5, 0, 1, 20, 1, 3, 100.0)
        sim_time = 0.0
        try:
            while self.running:
                sim_time += 0.05
                tx = 160 + int(80 * math.sin(sim_time * 0.5))
                ty = 120 + int(60 * math.cos(sim_time * 0.5))
                ox, oy = pid.compute(tx, ty, 80, 60)
                left = int(40 + oy + ox)
                right = int(40 + oy - ox)
                self.motion.set_wheel_speeds(left, right)
                print(f"\r  Target:({tx:3d},{ty:3d}) PID:({ox:+5.1f},{oy:+5.1f}) "
                      f"L={left:+4d} R={right:+4d}  ", end='', flush=True)
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        self.motion.stop()
        print("\n  Tracking ended.")

    # ======================================================================
    # Mode 6: Line Following (simulation)
    # ======================================================================
    def mode_line_following(self):
        print_banner("Mode 6: Line Following")
        print("  [SIM] Virtual line meandering — PID following it.")
        print("  Press Ctrl+C to stop.\n")
        pid = PID(target=160, P=30, I=0, D=2, scale=100.0)
        sim_time = 0.0
        try:
            while self.running:
                sim_time += 0.05
                line_x = 160 + int(60 * math.sin(sim_time * 0.5) +
                                   15 * math.sin(sim_time * 1.3))
                correction = pid.incremental(line_x, limit=50)
                left = int(40 + correction)
                right = int(40 - correction)
                self.motion.set_wheel_speeds(left, right)
                print(f"\r  Line X={line_x:3d} Err={line_x-160:+3d} "
                      f"PID={correction:+5.1f} L={left:+4d} R={right:+4d}  ",
                      end='', flush=True)
                time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        self.motion.stop()
        print("\n  Line following ended.")

    # ======================================================================
    # Mode 7: AprilTag Navigation (simulation)
    # ======================================================================
    def mode_apriltag_navigation(self):
        print_banner("Mode 7: AprilTag Navigation")
        print("  [SIM] Navigating between virtual tags.\n")
        for tag in ['T0', 'T1', 'T2']:
            print(f"  -> Navigating to {tag}...")
            for _ in range(5):
                self.motion.forward(50)
                time.sleep(0.3)
            self.motion.stop()
            print(f"  [ARRIVED] At {tag}")
            time.sleep(1.0)
        self.motion.stop()
        print("  Mission complete.")

    # ======================================================================
    # Mode 8: QR Code Commander
    # ======================================================================
    def mode_qrcode_commander(self):
        print_banner("Mode 8: QR Code Commander")
        print("  Type QR payloads: FWD:<speed>:<dur>  BACK:<s>:<d>")
        print("    LEFT:<s>:<d>  RIGHT:<s>:<d>  STOP  SQUARE:<s>  CIRCLE:<s>")
        print("  'quit' to exit.\n")
        while self.running:
            try:
                qr = input("QR> ").strip()
                if not qr:
                    continue
                if qr.lower() in ('quit', 'q'):
                    break
                parts = qr.upper().split(':')
                cmd = parts[0]
                if cmd == 'FWD':
                    s = int(parts[1]) if len(parts) > 1 else self.speed
                    d = float(parts[2]) if len(parts) > 2 else 1.0
                    self.motion.move(self.motion.FORWARD, s, d)
                elif cmd == 'BACK':
                    s = int(parts[1]) if len(parts) > 1 else 60
                    d = float(parts[2]) if len(parts) > 2 else 1.0
                    self.motion.move(self.motion.BACKWARD, s, d)
                elif cmd == 'LEFT':
                    s = int(parts[1]) if len(parts) > 1 else 60
                    d = float(parts[2]) if len(parts) > 2 else 0.35
                    self.motion.move(self.motion.LEFT, s, d)
                elif cmd == 'RIGHT':
                    s = int(parts[1]) if len(parts) > 1 else 60
                    d = float(parts[2]) if len(parts) > 2 else 0.35
                    self.motion.move(self.motion.RIGHT, s, d)
                elif cmd == 'STOP':
                    self.motion.stop()
                elif cmd == 'SQUARE':
                    s = int(parts[1]) if len(parts) > 1 else self.speed
                    self._execute_path(PathPlanner.square(side_time=1.5, speed=s))
                elif cmd == 'CIRCLE':
                    s = int(parts[1]) if len(parts) > 1 else self.speed
                    self._execute_path(PathPlanner.circle(speed=s, duration=5.0))
                else:
                    print(f"  Unknown: {qr}")
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"  Error: {e}")
        self.motion.stop()

    # ======================================================================
    # Mode 9: Face Recognition (simulation)
    # ======================================================================
    def mode_face_recognition(self):
        print_banner("Mode 9: Face Recognition Control")
        users = {"00": ("Alice", "follow"), "01": ("Bob", "greet"), "02": ("Charlie", "dance")}
        for uid, (name, beh) in users.items():
            print(f"    ID={uid}: {name} ({beh})")
        print("\n  [SIM] Simulating face detections...\n")
        scens = [(True, "00", "Alice"), (True, "01", "Bob"),
                 (False, None, "Unknown"), (True, "02", "Charlie")]
        for rec, uid, desc in scens:
            print(f"  -> {desc}")
            if rec and uid in users:
                name, beh = users[uid]
                print(f"    Recognised: {name} -> {beh}")
                if beh == 'greet':
                    self.motion.forward(60)
                    time.sleep(0.3)
                    self.motion.backward(60)
                    time.sleep(0.3)
                elif beh == 'follow':
                    self.motion.forward(50)
                    time.sleep(0.5)
                elif beh == 'dance':
                    for _ in range(2):
                        self.motion.turn_left(80)
                        time.sleep(0.3)
                        self.motion.turn_right(80)
                        time.sleep(0.3)
            else:
                print("    Unknown face — ignoring")
            self.motion.stop()
            time.sleep(1.5)
        print("  Demo complete.")

    # ======================================================================
    # Mode 10: Object Detection Nav (simulation)
    # ======================================================================
    def mode_object_detection(self):
        print_banner("Mode 10: Object Detection Navigation")
        beh = {"person": "Stop & wait", "bicycle": "Follow",
               "car": "Avoid right", "chair": "Go around", "dog": "Approach slowly"}
        for obj, b in beh.items():
            print(f"    {obj:>12s} -> {b}")
        print("\n  [SIM] Simulating detections...\n")
        for obj, b in beh.items():
            print(f"  -> Detected: {obj} -> {b}")
            if "avoid" in b.lower():
                self.motion.turn_right(60)
                time.sleep(0.5)
                self.motion.forward(60)
                time.sleep(1.0)
            elif "follow" in b.lower():
                self.motion.forward(60)
                time.sleep(1.0)
            elif "stop" in b.lower():
                self.motion.stop()
                time.sleep(1.0)
            else:
                self.motion.forward(40)
                time.sleep(1.0)
            self.motion.stop()
            time.sleep(1.0)
        print("  Demo complete.")

    # ======================================================================
    # Mode 11: Gesture Control (simulation)
    # ======================================================================
    def mode_gesture_control(self):
        print_banner("Mode 11: Gesture Control")
        print("  Face position -> command. Press Ctrl+C to stop.\n")
        sim_time = 0.0
        try:
            while self.running:
                sim_time += 0.05
                fx = 160 + int(100 * math.sin(sim_time * 0.3))
                fy = 120 + int(70 * math.cos(sim_time * 0.3))
                hz = 'LEFT' if fx < 107 else ('RIGHT' if fx > 213 else 'CENTRE')
                vz = 'TOP' if fy < 80 else ('BOTTOM' if fy > 160 else 'MID')
                if hz == 'CENTRE' and vz == 'MID':
                    self.motion.stop()
                elif vz == 'TOP':
                    self.motion.forward(60)
                elif hz == 'LEFT':
                    self.motion.turn_left(50)
                elif hz == 'RIGHT':
                    self.motion.turn_right(50)
                elif vz == 'BOTTOM':
                    self.motion.backward(50)
                print(f"\r  Face @ ({fx:3d},{fy:3d}) -> {hz:6s}-{vz:6s}  ",
                      end='', flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        self.motion.stop()
        print("\n  Gesture control ended.")

    # ======================================================================
    # Mode 12: MNIST Digit Control
    # ======================================================================
    def mode_mnist_control(self):
        print_banner("Mode 12: MNIST Digit Control")
        print("  Digit -> Command:")
        for d, desc in [(0,'Stop'),(1,'Fwd Slow'),(2,'Fwd Med'),(3,'Fwd Fast'),
                         (4,'Turn L'),(5,'Stop'),(6,'Turn R'),(7,'Back'),(8,'Dance'),(9,'Auto')]:
            print(f"    {d} -> {desc}")
        print("  Type a digit 0-9. 'quit' to exit.\n")
        while self.running:
            try:
                d = input("Digit> ").strip()
                if d.lower() in ('quit', 'q'):
                    break
                digit = int(d)
                if 0 <= digit <= 9:
                    if digit in (0, 5):
                        self.motion.stop()
                    elif digit == 1:
                        self.motion.forward(40)
                    elif digit == 2:
                        self.motion.forward(80)
                    elif digit == 3:
                        self.motion.forward(120)
                    elif digit == 4:
                        self.motion.turn_left(60)
                    elif digit == 6:
                        self.motion.turn_right(60)
                    elif digit == 7:
                        self.motion.backward(60)
                    elif digit == 8:
                        for _ in range(3):
                            self.motion.turn_left(80)
                            time.sleep(0.3)
                            self.motion.turn_right(80)
                            time.sleep(0.3)
                    elif digit == 9:
                        print("  Auto mode.")
                        self.motion.forward(60)
                        time.sleep(2.0)
                    time.sleep(1.0)
                    self.motion.stop()
            except (KeyboardInterrupt, EOFError):
                break
            except ValueError:
                print("  Enter a single digit 0-9.")
        self.motion.stop()

    # ======================================================================
    # Mode 13: Obstacle Avoidance (simulation)
    # ======================================================================
    def mode_obstacle_avoidance(self):
        print_banner("Mode 13: Obstacle Avoidance")
        print("  [SIM] Random obstacles. Press Ctrl+C to stop.\n")
        try:
            while self.running:
                if random.random() < 0.15:
                    dirn = random.choice(['left', 'right'])
                    print(f"  [OBSTACLE] Avoiding -> {dirn}")
                    self.motion.stop()
                    time.sleep(0.2)
                    if dirn == 'left':
                        self.motion.turn_left(60)
                    else:
                        self.motion.turn_right(60)
                    time.sleep(0.5)
                    self.motion.forward(60)
                else:
                    self.motion.forward(60)
                    print(f"\r  Cruising...  ", end='', flush=True)
                time.sleep(0.3)
        except KeyboardInterrupt:
            pass
        self.motion.stop()
        print("\n  Obstacle avoidance ended.")

    # ======================================================================
    # Mode 14: Voice Command
    # ======================================================================
    def mode_voice_command(self):
        print_banner("Mode 14: Voice Command (Text)")
        print("  Available: forward, backward, left, right, stop")
        print("            faster, slower, slow, medium, fast")
        print("            square, circle, zigzag, dance, patrol")
        print("            help, status, quit\n")
        vocab = {
            'forward': ('fwd', 80), 'go forward': ('fwd', 80),
            'backward': ('back', 60), 'go back': ('back', 60),
            'left': ('left', 60), 'turn left': ('left', 60),
            'right': ('right', 60), 'turn right': ('right', 60),
            'stop': ('stop', 0), 'halt': ('stop', 0),
            'faster': ('speed_up', 0), 'slower': ('speed_down', 0),
            'dance': ('dance', 0), 'square': ('square', 0),
            'circle': ('circle', 0), 'zigzag': ('zigzag', 0),
            'patrol': ('patrol', 0),
        }
        while self.running:
            try:
                cmd = input("Voice> ").strip().lower()
                if not cmd:
                    continue
                if cmd in ('quit', 'q'):
                    break
                if cmd == 'help':
                    print("  Say: forward, backward, left, right, stop, faster, slower, dance, square, circle, zigzag, patrol, status")
                    continue
                if cmd == 'status':
                    print(f"  Speed: {self.speed}")
                    continue
                matched = None
                for keyword, action in vocab.items():
                    if keyword in cmd:
                        matched = action
                        break
                if matched:
                    act, val = matched
                    print(f"  -> {act}")
                    if act == 'fwd':
                        self.motion.forward(val)
                        time.sleep(1.5)
                    elif act == 'back':
                        self.motion.backward(val)
                        time.sleep(1.0)
                    elif act == 'left':
                        self.motion.turn_left(val)
                        time.sleep(0.5)
                    elif act == 'right':
                        self.motion.turn_right(val)
                        time.sleep(0.5)
                    elif act == 'stop':
                        self.motion.stop()
                    elif act == 'speed_up':
                        self.speed = min(150, self.speed + 20)
                        print(f"    Speed: {self.speed}")
                    elif act == 'speed_down':
                        self.speed = max(20, self.speed - 20)
                        print(f"    Speed: {self.speed}")
                    elif act == 'dance':
                        for _ in range(3):
                            self.motion.turn_left(80)
                            time.sleep(0.3)
                            self.motion.turn_right(80)
                            time.sleep(0.3)
                    elif act == 'square':
                        self._execute_path(PathPlanner.square(1.5, self.speed))
                    elif act == 'circle':
                        self._execute_path(PathPlanner.circle(self.speed, 5.0))
                    elif act == 'zigzag':
                        self._execute_path(PathPlanner.zigzag(4, 1.0, self.speed))
                    elif act == 'patrol':
                        for _ in range(6):
                            self.motion.forward(80)
                            time.sleep(1.5)
                            self.motion.turn_right(60)
                            time.sleep(0.35)
                    self.motion.stop()
                else:
                    print(f"  Unknown: '{cmd}'. Say 'help'.")
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"  Error: {e}")
        self.motion.stop()

    # ======================================================================
    # Mode 15: Autonomous Exploration (simulation)
    # ======================================================================
    def mode_autonomous_explore(self):
        print_banner("Mode 15: Autonomous Exploration")
        print("  [SIM] Curiosity-driven exploration.")
        print("  Press Ctrl+C to stop.\n")
        steps = 0
        try:
            while self.running and steps < 50:
                r = random.random()
                if r < 0.6:
                    self.motion.forward(60)
                elif r < 0.8:
                    self.motion.turn_right(50)
                    time.sleep(0.4)
                else:
                    self.motion.turn_left(50)
                    time.sleep(0.4)
                steps += 1
                if steps % 10 == 0:
                    print(f"\r  Steps: {steps}  Coverage: {min(100, steps*2):.0f}%  ",
                          end='', flush=True)
                time.sleep(0.3)
        except KeyboardInterrupt:
            pass
        self.motion.stop()
        print(f"\n  Exploration ended. {steps} steps taken.")

    # ======================================================================
    # Mode 16: Self-Learning Nav (simulation)
    # ======================================================================
    def mode_self_learning_nav(self):
        print_banner("Mode 16: Self-Learning Navigation")
        print("  Class 1: Clear Path -> Forward")
        print("  Class 2: Obstacle -> Avoid")
        print("  Class 3: Destination -> Stop & Celebrate\n")
        print("  [SIM] Simulating classifications...\n")
        for cls in [1, 1, 1, 2, 2, 1, 1, 3]:
            if cls == 1:
                print("  Class 1 (Clear Path) -> Forward")
                self.motion.forward(60)
            elif cls == 2:
                print("  Class 2 (Obstacle) -> Avoid")
                self.motion.turn_right(60)
                time.sleep(0.5)
                self.motion.forward(50)
                time.sleep(1.0)
            elif cls == 3:
                print("  Class 3 (Destination) -> Stop & Celebrate!")
                for _ in range(2):
                    self.motion.turn_left(80)
                    time.sleep(0.3)
                    self.motion.turn_right(80)
                    time.sleep(0.3)
                self.motion.stop()
            time.sleep(1.5)
        self.motion.stop()
        print("  Demo complete.")


# ============================================================================
# Main Menu
# ============================================================================

def main():
    controller = CompleteRobotController()
    controller.initialise()

    MODES = [
        ("1",  "Basic Movement",       controller.mode_basic_move,
         "Keyboard-driven forward/backward/turn/stop"),
        ("2",  "Direction Control",    controller.mode_direction_control,
         "Precise angle & compass navigation"),
        ("3",  "Speed Control",        controller.mode_speed_control,
         "Speed profiles, ramps, and curves"),
        ("4",  "Path Control",         controller.mode_path_control,
         "Predefined & custom geometric paths"),
        ("5",  "Colour Tracking",      controller.mode_color_tracking,
         "Vision-based object following (PID)"),
        ("6",  "Line Following",       controller.mode_line_following,
         "Colour-based path tracking (PID)"),
        ("7",  "AprilTag Navigation",  controller.mode_apriltag_navigation,
         "Fiducial marker guidance"),
        ("8",  "QR Code Commander",    controller.mode_qrcode_commander,
         "Visual QR/barcode command interpretation"),
        ("9",  "Face Recognition",     controller.mode_face_recognition,
         "Identity-based access & behaviour"),
        ("10", "Object Detection Nav", controller.mode_object_detection,
         "VOC20 object-based navigation"),
        ("11", "Gesture Control",      controller.mode_gesture_control,
         "Face-position gesture interface"),
        ("12", "MNIST Digit Control",  controller.mode_mnist_control,
         "Handwritten digit commands"),
        ("13", "Obstacle Avoidance",   controller.mode_obstacle_avoidance,
         "Autonomous collision prevention"),
        ("14", "Voice Command",        controller.mode_voice_command,
         "Natural-language command interface"),
        ("15", "Autonomous Explore",   controller.mode_autonomous_explore,
         "Environment mapping & exploration"),
        ("16", "Self-Learning Nav",    controller.mode_self_learning_nav,
         "Trainable visual classifier navigation"),
    ]

    mode_lookup = {}
    menu_opts = []
    for key, name, method, desc in MODES:
        mode_lookup[key] = (name, method, desc)
        menu_opts.append((key, f"{name:<22s} — {desc}"))
    menu_opts.append(('s', 'Set default speed'))
    menu_opts.append(('q', 'Quit'))

    while controller.running:
        print_menu("Robot Complete — Integrated Controller (16 Modes)", menu_opts)
        print(f"  Current speed: {controller.speed}")
        choice = input("\nSelect mode: ").strip().lower()

        if choice in mode_lookup:
            name, method, desc = mode_lookup[choice]
            print(f"\n  Entering: {name}")
            print(f"  {desc}\n")
            method()
        elif choice == 's':
            try:
                s = input("  Enter speed (20-200): ").strip()
                controller.speed = max(20, min(200, int(s)))
                print(f"  Speed set to {controller.speed}")
            except ValueError:
                print("  Invalid speed.")
        elif choice == 'q':
            break
        else:
            print(f"  Invalid choice: '{choice}'")
        if controller.running:
            wait_for_keypress()

    controller.shutdown()


if __name__ == "__main__":
    main()
