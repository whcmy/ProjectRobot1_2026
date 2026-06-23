#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot Utilities Module — Shared Toolkit for Micro:bit Smart Car
================================================================
Provides serial communication, motor control, PID controllers,
path planning, and other common utilities.

All robot control programs import and reuse this module.

Target hardware:  micro:bit + K210 vision module smart car
Communication:    Serial (UART)
Protocol:         $<cmd_code><payload>,#
"""

import serial
import serial.tools.list_ports
import time
import math
import threading
from collections import deque


# ============================================================================
# Serial Communication
# ============================================================================

class RobotSerial:
    """Serial communication manager for the micro:bit / K210 robot.

    Handles port discovery, connection, and data transmission.
    Protocol format:
      Send:    $<command_code><payload>,#
      Receive: text lines
    """

    # Command codes (consistent with K210 source code)
    CMD_COLOR_RECOG   = "01"   # Color recognition
    CMD_BARCODE       = "02"   # Barcode detection
    CMD_QRCODE        = "03"   # QR code detection
    CMD_APRILTAG      = "04"   # AprilTag detection
    CMD_FACE_MASK     = "07"   # Face mask detection
    CMD_FACE_RECOG    = "08"   # Face recognition
    CMD_OBJECT_DETECT = "09"   # Object detection / AI road signs
    CMD_SELF_LEARN    = "10"   # Self-learning classifier
    CMD_MNIST         = "11"   # Handwritten digit recognition
    CMD_FACE_DETECT   = "14"   # Face detection (YOLO)
    CMD_MOTOR_SPEED   = "20"   # Motor speed control

    def __init__(self, port=None, baudrate=115200, timeout=0.1):
        """Initialize serial connection.

        Args:
            port:     Serial port name, e.g. 'COM3' (Windows) or
                      '/dev/ttyUSB0' (Linux). Auto-detects when None.
            baudrate: Baud rate, default 115200.
            timeout:  Read timeout in seconds.
        """
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

        if port is None:
            port = self._auto_find_port()

        if port:
            self.connect(port)
        else:
            print("[WARN] No serial port found. Please specify manually.")

    def _auto_find_port(self):
        """Auto-detect an available serial port."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Prefer ports with known keywords
            if any(kw in p.description.lower() for kw in
                   ['usb', 'serial', 'ch340', 'cp210', 'microbit', 'k210']):
                print(f"[AUTO] Found port: {p.device} - {p.description}")
                return p.device
        # Fallback: use the first available port
        if ports:
            print(f"[AUTO] Using first available port: {ports[0].device}")
            return ports[0].device
        return None

    def connect(self, port):
        """Connect to the specified serial port."""
        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
            print(f"[SERIAL] Connected to {port} @ {self.baudrate} bps")
            time.sleep(0.5)  # Wait for connection to stabilise
            return True
        except serial.SerialException as e:
            print(f"[ERROR] Cannot connect to {port}: {e}")
            return False

    def disconnect(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SERIAL] Disconnected")

    def send(self, data):
        """Send a raw string over serial."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data.encode('utf-8'))
                return True
            except serial.SerialException as e:
                print(f"[ERROR] Send failed: {e}")
                return False
        return False

    def send_command(self, cmd_code, payload=""):
        """Send a command in protocol format.

        Args:
            cmd_code: Command code (e.g. '20' for motor control).
            payload:  Data payload string.
        """
        packet = f"${cmd_code}{payload},#"
        return self.send(packet)

    def send_motor(self, left_speed, right_speed):
        """Send motor speed command.

        Args:
            left_speed:  Left wheel speed  (-999 ~ 999), positive = forward.
            right_speed: Right wheel speed (-999 ~ 999), positive = forward.
        """
        # Format left wheel speed (sign + 3 digits)
        if left_speed < 0:
            ls = f"-{abs(left_speed):03d}"
        else:
            ls = f"+{left_speed:03d}"

        # Format right wheel speed
        if right_speed < 0:
            rs = f"-{abs(right_speed):03d}"
        else:
            rs = f"+{right_speed:03d}"

        return self.send_command(self.CMD_MOTOR_SPEED, ls + rs)

    def send_stop(self):
        """Send stop command."""
        return self.send("#")

    def read_line(self):
        """Read one line from serial."""
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    return self.ser.readline().decode('utf-8', errors='ignore').strip()
            except serial.SerialException:
                pass
        return None

    def read_all(self):
        """Read all available data from serial."""
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    return self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            except serial.SerialException:
                pass
        return ""

    def is_connected(self):
        """Check whether the serial port is connected."""
        return self.ser is not None and self.ser.is_open

    @staticmethod
    def list_ports():
        """List all available serial ports."""
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("No serial devices found.")
            return []
        print("Available serial ports:")
        for i, p in enumerate(ports):
            print(f"  [{i}] {p.device} - {p.description}")
        return ports


# ============================================================================
# PID Controller
# ============================================================================

class PID:
    """Incremental PID controller.

    Used for precise robot motion control:
    line-following, object tracking, speed regulation, etc.
    """

    def __init__(self, target, P, I, D, scale=100.0):
        """
        Args:
            target: Setpoint value.
            P, I, D: PID gains.
            scale:   Scaling factor for gains.
        """
        self.Kp = P / scale
        self.Ki = I / scale
        self.Kd = D / scale
        self.setPoint = target
        self.err = 0.0
        self.err_next = 0.0
        self.err_last = 0.0
        self.last_result = 0.0

    def reset_target(self, target):
        """Update the setpoint."""
        self.setPoint = target

    def incremental(self, current_value, limit=0):
        """Compute incremental PID output.

        Args:
            current_value: Current measured value.
            limit:         Output clamping limit (>0 enables), 0 = no limit.

        Returns:
            PID output value.
        """
        self.err = current_value - self.setPoint

        result = (self.last_result
                  + self.Kp * (self.err - self.err_next)
                  + self.Ki * self.err
                  + self.Kd * (self.err - 2 * self.err_next + self.err_last))

        self.err_last = self.err_next
        self.err_next = self.err

        if limit > 0:
            result = max(-limit, min(limit, result))

        self.last_result = result
        return result

    def reset(self):
        """Reset PID internal state."""
        self.err = 0.0
        self.err_next = 0.0
        self.err_last = 0.0
        self.last_result = 0.0


class PIDController2D:
    """2D PID controller — controls X and Y axes simultaneously.

    Used for AprilTag following, colour tracking, etc.
    """

    def __init__(self, target_x, target_y,
                 Px, Ix, Dx, Py, Iy, Dy, scale=100.0):
        self.pid_x = PID(target_x, Px, Ix, Dx, scale)
        self.pid_y = PID(target_y, Py, Iy, Dy, scale)

    def compute(self, current_x, current_y, limit_x=0, limit_y=0):
        """Compute 2D PID output.

        Returns:
            (output_x, output_y) tuple.
        """
        ox = self.pid_x.incremental(current_x, limit_x)
        oy = self.pid_y.incremental(current_y, limit_y)
        return ox, oy

    def reset(self):
        self.pid_x.reset()
        self.pid_y.reset()


# ============================================================================
# Robot Motion Control
# ============================================================================

class RobotMotion:
    """High-level robot motion control interface.

    Wraps low-level serial motor commands with intuitive methods.
    """

    # Direction constants
    FORWARD  = 0
    BACKWARD = 1
    LEFT     = 2
    RIGHT    = 3

    def __init__(self, robot_serial: RobotSerial,
                 min_speed=15, max_speed=150):
        """
        Args:
            robot_serial: RobotSerial instance.
            min_speed:    Minimum effective speed (motors stall below this).
            max_speed:    Maximum speed limit.
        """
        self.serial = robot_serial
        self.min_speed = min_speed
        self.max_speed = max_speed
        self._lock = threading.Lock()

        # Current state
        self.current_left_speed = 0
        self.current_right_speed = 0

    def _clamp_speed(self, speed):
        """Clamp speed within valid range."""
        return max(-self.max_speed, min(self.max_speed, speed))

    def _apply_min_speed(self, speed):
        """Apply minimum speed threshold — boost if below stall speed."""
        if 0 < speed < self.min_speed:
            return self.min_speed
        elif -self.min_speed < speed < 0:
            return -self.min_speed
        return speed

    def _send_motor_raw(self, left, right):
        """Low-level motor command dispatch."""
        with self._lock:
            left = self._clamp_speed(left)
            right = self._clamp_speed(right)
            left = self._apply_min_speed(left)
            right = self._apply_min_speed(right)
            left = int(left)
            right = int(right)
            self.current_left_speed = left
            self.current_right_speed = right
            self.serial.send_motor(left, right)

    # ---------- Basic movements ----------

    def stop(self):
        """Stop the robot."""
        self._send_motor_raw(0, 0)
        self.serial.send_stop()

    def forward(self, speed=80):
        """Move forward.

        Args:
            speed: Speed value (0 ~ max_speed).
        """
        s = abs(speed)
        self._send_motor_raw(s, s)

    def backward(self, speed=80):
        """Move backward."""
        s = abs(speed)
        self._send_motor_raw(-s, -s)

    def turn_left(self, speed=60):
        """Spin left in place."""
        s = abs(speed)
        self._send_motor_raw(-s, s)

    def turn_right(self, speed=60):
        """Spin right in place."""
        s = abs(speed)
        self._send_motor_raw(s, -s)

    def spin_left(self, speed=80):
        """Spin left (alias for turn_left)."""
        self.turn_left(speed)

    def spin_right(self, speed=80):
        """Spin right (alias for turn_right)."""
        self.turn_right(speed)

    # ---------- Differential steering ----------

    def steer(self, speed, turn_rate):
        """Differential steering — move in an arc.

        Args:
            speed:     Base speed.
            turn_rate: Turn rate (-1.0 ~ 1.0), negative = left, positive = right.
        """
        s = abs(speed)
        if turn_rate >= 0:
            # Right turn: left wheel faster, right wheel slower
            left = s
            right = int(s * (1.0 - 2.0 * turn_rate))
        else:
            # Left turn: right wheel faster, left wheel slower
            right = s
            left = int(s * (1.0 + 2.0 * turn_rate))
        self._send_motor_raw(left, right)

    def move_with_heading(self, speed, heading_angle):
        """Move at a given heading angle.

        Args:
            speed:         Speed magnitude.
            heading_angle: Heading angle in degrees.
                           0 = forward, 90 = right, 180 = backward, -90 = left.
        """
        # Map angle to wheel speed differential
        turn_factor = heading_angle / 90.0  # -1 ~ 1
        turn_factor = max(-1.0, min(1.0, turn_factor))

        s = abs(speed)
        if turn_factor >= 0:
            left = s
            right = int(s * (1.0 - 2.0 * turn_factor))
        else:
            right = s
            left = int(s * (1.0 + 2.0 * turn_factor))
        self._send_motor_raw(left, right)

    # ---------- Compound movements ----------

    def move(self, direction, speed=80, duration=None):
        """Generic move interface.

        Args:
            direction: One of FORWARD / BACKWARD / LEFT / RIGHT.
            speed:     Speed value.
            duration:  Duration in seconds. None = continuous movement.
        """
        if direction == self.FORWARD:
            self.forward(speed)
        elif direction == self.BACKWARD:
            self.backward(speed)
        elif direction == self.LEFT:
            self.turn_left(speed)
        elif direction == self.RIGHT:
            self.turn_right(speed)

        if duration:
            time.sleep(duration)
            self.stop()

    def set_wheel_speeds(self, left_speed, right_speed):
        """Set individual wheel speeds directly.

        Args:
            left_speed:  Left wheel speed  (-max_speed ~ max_speed).
            right_speed: Right wheel speed (-max_speed ~ max_speed).
        """
        self._send_motor_raw(left_speed, right_speed)


# ============================================================================
# Path Planner
# ============================================================================

class PathPlanner:
    """Path planner — generates predefined movement sequences.

    Supported shapes:
      square, rectangle, zigzag, circle, figure-8, spiral, custom waypoints
    """

    @staticmethod
    def square(side_time=2.0, speed=100):
        """Generate a square path.

        Returns:
            List of (direction, speed, duration) movement instructions.
        """
        return [
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, 0.35),   # 90-degree right turn
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, 0.35),
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, 0.35),
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, 0.35),
        ]

    @staticmethod
    def rectangle(forward_time=3.0, side_time=1.5, speed=100):
        """Generate a rectangular path."""
        turn_time = 0.35
        return [
            (RobotMotion.FORWARD, speed, forward_time),
            (RobotMotion.RIGHT, speed, turn_time),
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, turn_time),
            (RobotMotion.FORWARD, speed, forward_time),
            (RobotMotion.RIGHT, speed, turn_time),
            (RobotMotion.FORWARD, speed, side_time),
            (RobotMotion.RIGHT, speed, turn_time),
        ]

    @staticmethod
    def zigzag(segments=4, seg_time=1.5, speed=80):
        """Generate a zigzag path."""
        path = []
        turn_time = 0.35
        for i in range(segments):
            path.append((RobotMotion.FORWARD, speed, seg_time))
            if i % 2 == 0:
                path.append((RobotMotion.RIGHT, speed, turn_time))
                path.append((RobotMotion.FORWARD, speed, seg_time))
                path.append((RobotMotion.LEFT, speed, turn_time * 2))
            else:
                path.append((RobotMotion.LEFT, speed, turn_time))
                path.append((RobotMotion.FORWARD, speed, seg_time))
                path.append((RobotMotion.RIGHT, speed, turn_time * 2))
        return path

    @staticmethod
    def circle(speed=80, turn_rate=0.3, duration=8.0):
        """Generate a circular path (continuous arc).

        Returns:
            [('circle', speed, turn_rate, duration)]
        """
        return [('circle', speed, turn_rate, duration)]

    @staticmethod
    def figure8(speed=80, turn_rate=0.3, duration=10.0):
        """Generate a figure-8 path (alternating arcs)."""
        half = duration / 2
        return [
            ('circle', speed, turn_rate, half),
            ('circle', speed, -turn_rate, half),
        ]

    @staticmethod
    def spiral(speed=100, initial_turn=0.1, increment=0.05,
               steps=10, step_time=1.0):
        """Generate a spiral path (gradually increasing turn rate)."""
        path = []
        for i in range(steps):
            turn = initial_turn + i * increment
            turn = min(turn, 0.9)
            path.append(('circle', speed, turn, step_time))
        return path

    @staticmethod
    def custom_waypoints(waypoints):
        """Accept custom waypoint sequences.

        Args:
            waypoints: [(direction, speed, duration), ...]
        Returns:
            The same waypoints unchanged.
        """
        return waypoints


# ============================================================================
# Sensor Simulator & Utility Functions
# ============================================================================

class SensorSimulator:
    """Sensor simulator — provides mock sensor data for development & testing."""

    def __init__(self):
        self._distance = 100.0       # Simulated front distance (cm)
        self._color_detected = None
        self._line_position = 160    # Simulated line position (image centre x)
        self._tag_detected = None

    def get_distance(self):
        """Get simulated distance."""
        return self._distance

    def get_line_position(self):
        """Get simulated line position."""
        return self._line_position

    def get_color(self):
        """Get simulated detected colour."""
        return self._color_detected

    def set_distance(self, d):
        self._distance = d

    def set_line_position(self, pos):
        self._line_position = pos


def wait_for_keypress(prompt="Press Enter to continue..."):
    """Wait for the user to press Enter."""
    try:
        input(prompt)
    except (EOFError, KeyboardInterrupt):
        pass


def format_speed_str(speed):
    """Format a speed value as the protocol-required 4-char string (sign + 3 digits)."""
    if speed < 0:
        return f"-{abs(speed):03d}"
    else:
        return f"+{speed:03d}"


def speed_to_pwm(speed, max_pwm=255):
    """Map speed (-100 ~ 100) to a PWM duty cycle (0 ~ 255).

    Args:
        speed:   Speed percentage (-100 ~ 100).
        max_pwm: Maximum PWM value.
    Returns:
        PWM value (0 ~ max_pwm).
    """
    pwm = int(abs(speed) / 100.0 * max_pwm)
    return min(pwm, max_pwm)


def smooth_transition(from_speed, to_speed, steps=10, delay=0.02):
    """Generate intermediate speed values for smooth acceleration / deceleration.

    Args:
        from_speed: Starting speed.
        to_speed:   Target speed.
        steps:      Number of transition steps.
        delay:      Delay per step (seconds).
    Yields:
        Intermediate speed values.
    """
    for i in range(1, steps + 1):
        t = i / steps
        # Ease in-out function
        eased = t * t * (3 - 2 * t)
        current = int(from_speed + (to_speed - from_speed) * eased)
        yield current


def print_banner(title, width=60):
    """Print a formatted banner."""
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_menu(title, options):
    """Print a selection menu.

    Args:
        title:   Menu title.
        options: List of (key, description) tuples.
    """
    print_banner(title)
    for key, desc in options:
        print(f"  [{key}]  {desc}")
    print("-" * 40)


# ============================================================================
# Logger
# ============================================================================

class RobotLogger:
    """Simple robot runtime logger."""

    def __init__(self, max_entries=500):
        self.log = deque(maxlen=max_entries)
        self.start_time = time.time()

    def info(self, msg):
        """Log an info message."""
        entry = f"[{self._timestamp()}] INFO: {msg}"
        self.log.append(entry)
        print(entry)

    def warn(self, msg):
        """Log a warning."""
        entry = f"[{self._timestamp()}] WARN: {msg}"
        self.log.append(entry)
        print(f"\033[93m{entry}\033[0m")

    def error(self, msg):
        """Log an error."""
        entry = f"[{self._timestamp()}] ERROR: {msg}"
        self.log.append(entry)
        print(f"\033[91m{entry}\033[0m")

    def _timestamp(self):
        elapsed = time.time() - self.start_time
        return f"{elapsed:7.2f}s"

    def get_recent(self, n=10):
        """Return the most recent n entries."""
        return list(self.log)[-n:]

    def save(self, filepath="robot_log.txt"):
        """Save the log to a file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.log))
        print(f"[LOG] Saved to {filepath}")


# ============================================================================
# Safety Guard
# ============================================================================

class SafetyGuard:
    """Robot safety guard — monitors runtime and auto-stops on anomaly."""

    def __init__(self, motion: RobotMotion,
                 max_run_time=120,     # Max run time (seconds)
                 check_interval=0.5):  # Check interval (seconds)
        self.motion = motion
        self.max_run_time = max_run_time
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._start_time = 0

    def start(self):
        """Start the safety monitor."""
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the safety monitor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _monitor(self):
        """Monitor thread."""
        while self._running:
            time.sleep(self.check_interval)
            elapsed = time.time() - self._start_time
            if elapsed > self.max_run_time:
                print("[SAFETY] Run time exceeded! Auto-stopping robot.")
                self.motion.stop()
                self._running = False
                break

    def emergency_stop(self):
        """Emergency stop."""
        print("[EMERGENCY STOP!]")
        self.motion.stop()
        self._running = False


# ============================================================================
# Main entry point (for testing)
# ============================================================================

if __name__ == "__main__":
    print_banner("Robot Utilities Module Test")

    # Test serial port listing
    RobotSerial.list_ports()

    # Test PID controller
    print("\n--- PID Controller Test ---")
    pid = PID(target=160, P=22, I=0, D=2, scale=100.0)
    test_values = [180, 170, 165, 162, 160, 158, 155, 150, 145]
    for v in test_values:
        out = pid.incremental(v)
        print(f"  input={v}, pid_output={out:.2f}")

    # Test path planner
    print("\n--- Path Planner Test ---")
    square_path = PathPlanner.square(side_time=2.0)
    print(f"  Square path: {len(square_path)} steps")
    for i, step in enumerate(square_path):
        print(f"    Step {i+1}: direction={step[0]}, speed={step[1]}, duration={step[2]}s")

    # Test speed formatting
    print("\n--- Speed Formatting Test ---")
    for s in [100, -50, 5, -200, 0]:
        print(f"  speed={s:4d} -> '{format_speed_str(s)}'")

    print("\n[DONE] All modules ready.")
