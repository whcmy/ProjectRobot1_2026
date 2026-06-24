<p align="center">
  <h1 align="center">🤖 ProjectRobot1 — Tinybit AI Smart Car</h1>
  <p align="center">
    <em>K210 Vision + micro:bit + Tinybit — an intelligent, programmable robot car</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Hardware-micro%3Abit%20%2B%20K210-blue?style=flat-square" alt="Hardware">
  <img src="https://img.shields.io/badge/Language-MicroPython%20%2F%20MaixPy-orange?style=flat-square" alt="Language">
  <img src="https://img.shields.io/badge/Library-tinybit-brightgreen?style=flat-square" alt="Library">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="License">
</p>

---

## 📖 Overview

**ProjectRobot1** is a dual-processor intelligent robot car built on the **YahBoom Tinybit** platform. It combines:

- 🧠 **K210 (MaixPy)** — AI vision coprocessor: real‑time camera input, neural‑network inference, object detection, face recognition, color tracking, and more
- 🎮 **micro:bit (MicroPython)** — motion controller: receives vision results over UART, drives motors via `tinybit`, and handles user interaction through buttons & LED display

The two boards communicate over serial (115200 bps) using a simple text protocol: `$<cmd><payload>,#`

---

## 🧱 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     K210 (MaixPy)                        │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐     │
│  │  Camera  │  │   KPU    │  │  Serial (ybserial)  │     │
│  │  (OV2640)│──│ (AI/NPU) │──│  → UART TX →        │     │
│  └──────────┘  └──────────┘  └────────────────────┘     │
│       ↓                          │                       │
│  sensor.snapshot()         $01… $04… $09… $20…          │
│  AI inference              (protocol packets)            │
└──────────────────────────────────────────────────────────┘
                           │  UART (115200 bps)
                           ↓
┌──────────────────────────────────────────────────────────┐
│                   micro:bit (MicroPython)                │
│  ┌────────────────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Serial (UART RX)  │  │  tinybit  │  │  Motors  │     │
│  │  ← parse protocol  │──│ .car_run()│──│  L + R   │     │
│  └────────────────────┘  └──────────┘  └──────────┘     │
│    Button A/B: pause / mode    LED display: status       │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Flash the K210

Copy the desired program from [`source code/k210/`](source%20code/k210/) to the K210's SD card (usually `/sd/`). Make sure the corresponding `.kmodel` files are also present on the SD in the correct paths.

### 2. Flash the micro:bit

Open any `robot_*.py` file in [Mu Editor](https://codewith.mu/) and flash it to the micro:bit. All programs are standalone — pick the one that matches your K210 program.

### 3. Power on

1. Power the Tinybit car
2. The K210 boots and starts vision processing
3. The micro:bit starts receiving commands and driving motors
4. Press **Button A** to pause/resume · **Button B** for status info

---

## 📡 Serial Protocol

| Code | Source (K210) | Payload | Description |
|:---:|---|---|---|
| `$01` | Color recognition | `<R\|G\|B\|Y>` | Detected color |
| `$02` | Barcode scan | `<payload>` | Barcode text |
| `$03` | QR code scan | `<payload>` | QR code text |
| `$04` | AprilTag | `<id>,<family>` | Tag ID & family |
| `$07` | Face mask detect | `<0\|1>` | 1 = with mask |
| `$08` | Face recognition | `<Y\|N><index>` | Recognized identity |
| `$09` | Object / AI sign | `<class_id>` | VOC20 object or road sign |
| `$10` | Self-learning | `<1\|2\|3>` | Trained class |
| `$11` | MNIST digit | `<0–9>` | Handwritten digit |
| `$14` | Face detection | `<0\|1>` | 1 = face found |
| **`$20`** | **Motor speed** | **`+LxxRxx`** | **Direct wheel speeds** |

> Motor format: each speed is sign + 3 digits (e.g. `+080‑030` = left 80, right −30)

---

## 📁 Repository Structure

```
ProjectRobot1_2026/
│
├── robot_basic_move.py          ← Button-controlled movement
├── robot_speed_control.py       ← Speed calibration utility
├── robot_direction_control.py   ← Compass / serial direction nav
├── robot_path_control.py        ← Predefined geometric paths
│
├── robot_line_following.py      ← PID line tracking
├── robot_color_tracking.py      ← Color-based object following
├── robot_apriltag_navigation.py ← AprilTag marker guidance
│
├── robot_gesture_control.py     ← Face-position gesture interface
├── robot_face_recog_control.py  ← Identity-based actions
├── robot_mnist_control.py       ← Handwritten digit commands
├── robot_object_detect_nav.py   ← VOC20 object-based navigation
├── robot_qrcode_commander.py    ← QR / barcode command execution
├── robot_self_learning_nav.py   ← Few-shot visual classifier nav
│
├── robot_obstacle_avoidance.py  ← Ultrasonic autonomous avoidance
├── robot_voice_command.py       ← Serial text command interface
├── robot_autonomous_explore.py  ← Curiosity-driven exploration
│
├── robot_complete.py            ← 🧩 Integrated all-in-one controller
│
└── source code/
    ├── k210/                    ← K210 MaixPy vision programs (15 files)
    │   ├── 2.1_color_recognition.py
    │   ├── 2.2_3.2_find_barcodes.py
    │   ├── 2.2_3.3_find_qrcodes.py
    │   ├── 2.4_find_apriltags.py
    │   ├── 2.5_3.4_voc20_object_detect.py
    │   ├── 2.6_3.5_self_learning.py
    │   ├── 2.7_3.6_face_mask_detect.py
    │   ├── 2.8_face_recog.py
    │   ├── 2.9_3.8_mnist.py
    │   ├── 3.1_color_rgb.py
    │   ├── 3.7_yolo_face_detect-Y.py
    │   ├── 3.9_color_follow_line.py
    │   ├── 3.10_follow_apriltag.py
    │   ├── 3.11_follow_color.py
    │   └── 3.12_tinybit_AI_sport.py
    │
    ├── KPU/                     ← K210 neural network models (.kmodel)
    │   ├── face_detect_with_68landmark/
    │   ├── face_mask_detect/
    │   ├── face_recognization/
    │   ├── mnist/
    │   ├── self_learn_classifier/
    │   ├── voc20_object_detect/
    │   └── yolo_face_detect/
    │
    └── microbit/                ← Pre-compiled micro:bit hex files
```

---

## 🎮 Button Controls (micro:bit side)

| Button | Function |
|:---:|---|
| **A** (tap) | Pause / Resume |
| **B** (tap) | Show status / Cycle mode |
| **A + B** | Emergency stop or execute action |
| **Shake** | Emergency stop |

---

## 🔧 Hardware

| Component | Model |
|---|---|
| Main board | BBC micro:bit v2 |
| Vision module | Sipeed M1/M1w (K210) |
| Camera | OV2640 (200 W pixel) |
| Car chassis | YahBoom Tinybit |
| Motors | 2× N20 DC motor (TT motor) |
| Sensors | Ultrasonic, IR line‑tracking, RGB LEDs |
| Battery | 2× 18650 (7.4 V) |

---

## 🧠 AI Capabilities (K210 KPU)

| Model | Task | Classes |
|---|---|---|
| `yolo_face_detect` | Face detection | 1 (face) |
| `face_detect_68landmark` | 68-point facial landmarks | — |
| `feature_extraction` + `ld5` | Face recognition | User‑enrolled |
| `detect_5` | Face mask detection | 2 (with / without) |
| `voc20_detect` | Object detection | 20 (VOC classes) |
| `uint8_mnist_cnn_model` | Handwritten digits | 10 (0–9) |
| `mb-0.25` | Self‑learning classifier | 3 (user‑trained) |
| `tinybit_AI_01` / `02` | Road sign recognition | 9–11 traffic signs |
| `color_recognition` | Color detection | RGBY (threshold‑based) |

---

## 📝 License

MIT © 2026 — [whcmy](https://github.com/whcmy)
