# Handsfree (by Apex Caliber Labs)

> **Touchless Windows 11 Computer Vision Mouse Control**  
> Inspired by the Meta Quest 2 / 3 controller-free hand tracking experience.

Handsfree turns your computer's onboard webcam into a high-precision, touchless mouse input system. It runs quietly in the Windows system tray and replaces the traditional pointer with a sleek, floating luminous neon cursor with real-time pinch depth feedback.

---

## Highlights & Features

- **Meta Quest-Style Glowing Cursor**:
  - Floating luminous neon dot (cyan/electric blue) with soft radial aura.
  - Dynamically contracts as you pinch your fingers, providing visual tactile feedback of click depth.
  - Pulses emerald green upon click and drag, and displays directional swipe cues during scroll.
  - Completely transparent, non-activating, click-through overlay window.

- **Silky Smooth 1-Euro Filtering**:
  - Dynamically adapts low-pass filter cutoff based on movement speed.
  - Heavy jitter elimination when aiming at tiny UI buttons; near-zero latency when flicking across displays.

- **Natural VR-Style Hand Gestures**:
  - **Move Pointer**: Move your index finger in the air (works seamlessly with left or right hand).
  - **Click & Drag (Pinch)**: Pinch thumb and index fingertip together. Quick pinch = left click; pinch and hold = click & drag.
  - **Scroll**: Bring index and middle finger together and swipe slowly up or down.
  - **Right Click**: Pinch thumb and middle fingertip together.

- **Initial Setup & Calibration Wizard**:
  - First launch guides you through camera alignment, comfortable physical reach bounding, pinch threshold tuning, and smoothing preferences.
  - Settings are saved to `%LOCALAPPDATA%\Handsfree\config.json` and can be recalibrated anytime.

- **System Tray Background Service**:
  - Runs in the background with minimal CPU footprint.
  - Tray menu options to Pause/Resume, open Calibration, toggle Live Vision HUD, or set Launch at Windows Startup.

- **Packaging & Distribution**:
  - Standalone executable (`Handsfree.exe`) bundling MediaPipe models and OpenCV dependencies.
  - Dedicated graphical Windows 11 installer (`Handsfree_Setup.exe`) with desktop/Start Menu shortcuts, uninstaller, and auto-start integration.

---

## Gestures Reference

| Gesture | Pose | Action |
| :--- | :--- | :--- |
| **Move Pointer** | Point with index finger | Moves cursor across screen |
| **Left Click** | Quick pinch (Thumb + Index tip) | Standard left click |
| **Click & Drag** | Pinch & hold > 320ms | Window dragging, text highlighting |
| **Scroll** | Index + Middle fingers together + vertical swipe | Smooth vertical document/web scroll |
| **Right Click** | Pinch (Thumb + Middle tip) | Opens context menu |

---

## Quick Start (Pre-Built Executables)

### Option 1: Installer Setup
Run `dist/Handsfree_Setup.exe`. Follow the wizard to choose your destination, create shortcuts, and launch Handsfree.

### Option 2: Portable Folder
Extract `dist/Handsfree_v1.0.0_Portable.zip` and run `Handsfree.exe`. The app will appear in your Windows system tray.

---

## Building from Source

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10+ (Tested on Python 3.13 and 3.14)
- Webcam (onboard or USB)

### Installation
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Running Handsfree
```powershell
python -m handsfree.main
```

### Running Test Suite
```powershell
python -m unittest discover tests
```

### Packaging Executable & Installer
```powershell
python installer/build_installer.py
```

---

## Git & Repository

- **Repository**: [https://github.com/apexcaliberlabs/Handsfree](https://github.com/apexcaliberlabs/Handsfree)
- **Organization / Author**: `apexcaliberlabs` (`apexcaliberlabs@gmail.com`)
- **License**: MIT License (c) 2026 Apex Caliber Labs
