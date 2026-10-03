# Gesture Slide Demo

A small Windows/VS Code demo that uses your laptop webcam to control presentation slides with hand gestures.

## Gestures

- Index finger only: NEXT slide
- Index + middle fingers: PREVIOUS slide
- Q: quit

The demo sends the normal Left/Right arrow keyboard keys, so it can work with PowerPoint and other presentation software that responds to those keys.

## Recommended Python

Use Python 3.11 for easiest MediaPipe compatibility.

## Setup in VS Code

Open this folder in VS Code.

Create a virtual environment:

    py -3.11 -m venv .venv

Activate it in PowerShell:

    .\.venv\Scripts\Activate.ps1

Install packages:

    pip install -r requirements.txt

Run:

    python main.py

## Test

1. Start main.py.
2. Allow camera access if Windows asks.
3. Open a PowerPoint presentation.
4. Start Slide Show mode.
5. Show one index finger to go forward.
6. Show index + middle fingers to go backward.

There is a 1-second cooldown to prevent one gesture from changing many slides instantly.

## Camera does not open?

In main.py change:

    CAMERA_INDEX = 0

to:

    CAMERA_INDEX = 1

## Stop

Focus the camera preview and press Q, or stop the Python process in VS Code.
