# Synesthetic Machine - Contextual Documentation

## Project Overview

The Synesthetic Machine is an interactive art installation that transforms circular canvases into visual and sound scores. This work creates a bridge between different sensory modalities (vision, hearing), embodying the neurological phenomenon of synesthesia where a sensory stimulus automatically triggers an experience in another sensory modality.

## Artistic Concept

The installation allows visitors to "see sound" and "hear colors." Each circular canvas becomes a unique score that, when placed on the device and set in rotation, simultaneously generates:
- A light response that reflects the colors of the canvas
- An algorithmically generated musical composition based on the chromatic data

The boundary between visual arts and music fades to create an immersive multi-sensory experience where the senses respond to and amplify each other.

## Technical Architecture

### Overview

The system is based on a distributed modular architecture, communicating primarily via the OSC (Open Sound Control) protocol. This approach allows for great flexibility and a clear separation of responsibilities between the different components.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│   Vision    │───►│   Logic     │───►│     LED     │
│  (Camera)   │    │ (Processing)│    │  (Display)  │
│             │    │             │    │             │
└─────────────┘    └──────┬──────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │             │
                   │  Pure Data  │
                   │   (Audio)   │
                   │             │
                   └─────────────┘
```

### Hardware Components

- **Raspberry Pi 5**: Central unit hosting the main services
- **Camera Module**: Real-time capture of rotating canvases
- **LED Strip**: Reproduces analyzed colors in light form
- **Audio System**: Plays back the generated sound composition
- **Rotation Mechanism**: Enables constant rotation of circular canvases

### Software Components

The system consists of several independent modules, each with a specific responsibility:

#### 1. Vision Module (`vision.py`)
- Image capture via camera
- Real-time color analysis
- Extraction of RGB and HSV values
- Transmission of chromatic data via OSC

#### 2. Logic Module (`logic.py`)
- Central system coordination
- Reception and processing of color data
- Smoothing techniques (circular buffers, exponential moving average)
- Routing information to other modules

#### 3. LED Module (`led_controller.py`)
- LED strip control
- Faithful reproduction of analyzed colors
- Management of transitions and light effects

#### 4. Audio Module (Pure Data)
- Algorithmic sound generation
- Mapping RGB/HSV values to musical parameters
- Creation of a sound atmosphere corresponding to colors

### Data Flow

1. The camera captures the image of the rotating canvas
2. Color data is extracted and sent to the logic module
3. The logic module applies smoothing algorithms to stabilize transitions
4. The stabilized values are simultaneously sent to:
   - The LED controller for light reproduction
   - Pure Data for sound generation

## Technical Details

### Communication Protocol

The entire system uses OSC (Open Sound Control) for communication between components. The different services communicate via UDP on specific ports defined in the `network.json` file.

### Color Processing

The system uses several techniques to ensure a smooth and stable experience:

- **Circular Buffers**: Temporary storage of the last N RGB values
- **Exponential Moving Average (EMA)**: Smoothing algorithm with a very low alpha factor (0.0005) for ultra-smooth transitions
- **Dual Color Representation**: Simultaneous use of RGB and HSV color spaces to enrich expressive possibilities

### Systemd Services

The installation functions as a set of systemd services on the Raspberry Pi, ensuring:
- Automatic startup at boot
- Restart in case of crash
- Management of dependencies between services

## Deployment and Maintenance

### Installation

Deployment is automated via scripts located in the `tools/deployment/` folder:
- `setup_raspberry_complete.sh`: Initial Raspberry Pi configuration
- `deploy.sh`: Deployment of code updates

### Dependencies

Project dependencies are managed via pip and documented in requirements files:
- `src/raspberry/requirements.txt`: Main dependencies for the Raspberry Pi
- `requirements/mac-requirements.txt`: Specific dependencies for macOS (development)


*Documentation updated on May 7, 2025*