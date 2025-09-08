# Python Scripts

## vision.py
Real-time video capture and analysis script.

### Features
- Video capture via libcamera (Raspberry Pi)
- Dominant color detection via OpenCV
- RGB and HSV data transmission via OSC

## led_controller.py
LED strip control based on detected colors.

### Features
- Direct reception of raw color data via OSC (/color/raw/rgb)
- Reception of processed color data (if needed) via OSC (/color/rgb)
- LED strip control via GPIO

## logic.py
Coordination between color detection and outputs (mainly Pure Data).

### Features
- Reception of RGB/HSV data from vision.py
- Distribution of HSV data to Pure Data

## osc_router.py
Central router for OSC communication between different components.

### Features
- Listens on port 5005
- Redistribution of messages to all configured recipients
- Central point for all inter-module communication

## Communication OSC

### Network architecture
All communications pass through the central OSC router:

```
 ┌──────────┐         ┌─────────────────┐
 │          │ ----→   │                 │
 │ vision.py│  OSC    │  osc_router.py  │
 │          │ ----→   │    (port 5005)  │
 └──────────┘         │                 │
                      └─────┬─────┬─────┘
                            │     │
                            │     │
                            │     └───────────────┐
                            │                     │
                            ↓                     ↓
                      ┌───────────┐         ┌──────────┐
                      │           │         │          │
                      │ logic.py  │         │led_ctrl.py│
                      │           │         │          │
                      └─────┬─────┘         └──────────┘
                            │
                            ↓
                      ┌───────────┐
                      │           │
                      │ PureData  │
                      │           │
                      └───────────┘
```

### Data flow by message type
- Raw color data: `vision.py → osc_router.py → led_controller.py` (direct flow)
- HSV data for audio: `vision.py → osc_router.py → logic.py → PureData`
- All messages transit through the central OSC router

