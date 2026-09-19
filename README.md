# Driver Drowsiness Monitoring System

![Python 3](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/Computer_Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![Mediapipe](https://img.shields.io/badge/Machine_Learning-Mediapipe-00599C?style=for-the-badge)
![ESP32](https://img.shields.io/badge/Hardware-ESP32-00979D?style=for-the-badge)
![MQTT](https://img.shields.io/badge/IoT-MQTT-660066?style=for-the-badge)

## Executive Overview
Driver fatigue is a leading cause of severe traffic accidents worldwide. This project implements a real-time computer vision and embedded IoT safety system to mitigate this risk. By leveraging **Mediapipe** for facial landmark tracking and calculating the Eye Aspect Ratio (EAR), the AI pipeline running on a PC detects drowsiness onset. Critical state changes are broadcast via **MQTT** to an **ESP32** microcontroller, which acts as the physical vehicle interface—triggering acoustic alarms and ultimately disabling the vehicle's motor controller if the driver becomes unresponsive.

> [!WARNING]
> **Automotive Safety & Liability Callout**
> Implementing a physical ignition/motor cutoff via an ESP32 GPIO relay introduces severe safety hazards if deployed in a moving vehicle. Sudden loss of motive power at highway speeds disables power steering and power braking assistance. This system is designed as an academic prototype for bench-testing and controlled low-speed demonstrations only.

## Feature Highlights
- **Real-Time Facial Landmark Tracking**: 468-point spatial mapping utilizing Google Mediapipe.
- **Deterministic Fatigue Calculus**: Eye Aspect Ratio (EAR) thresholding combined with a 3-second consecutive frame debouncing algorithm to prevent false positives from standard blinking.
- **Decoupled IoT Architecture**: High-computational vision tasks are handled on a PC, while low-latency physical actuation is handled by an ESP32 via an MQTT broker.
- **Progressive Intervention**: The system escalates from visual UI warnings to remote MQTT-driven acoustic alarms, culminating in an automated motor shutdown if the driver fails to acknowledge the alert within 10 seconds.

## System Architecture

```mermaid
flowchart TD
    subgraph Vision Node (PC/Raspberry Pi)
        CAM[USB Webcam] -->|Video Stream| CV[OpenCV + Mediapipe]
        CV -->|Facial Landmarks| EAR[EAR Calculation Logic]
        EAR -->|State Evaluator| PUB[MQTT Publisher]
    end

    subgraph Network
        PUB <-->|Wi-Fi / TCP| BROKER[MQTT Broker 192.168.0.160]
    end

    subgraph Actuation Node (ESP32)
        BROKER <-->|Wi-Fi / TCP| SUB[MQTT Subscriber]
        SUB -->|GPIO High/Low| RELAY[Motor Relay Contactor]
        SUB -->|PWM| BUZZER[Acoustic Alarm]
    end
```

## Theoretical & Mathematical Models

### Eye Aspect Ratio (EAR)
The EAR formula maps 2D facial landmarks corresponding to the ocular boundaries to calculate the degree of eye closure. Let $p_1, \dots, p_6$ denote the Cartesian coordinates of the 6 key eye landmarks. The ratio is defined as:
$$ \text{EAR} = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 ||p_1 - p_4||} $$
Where:
- The numerator computes the distance between the vertical eye landmarks.
- The denominator computes the distance between the horizontal eye landmarks.
- A sudden drop in EAR indicates a blink, while a sustained drop (e.g., $EAR < 0.25$ for $t > 3\text{s}$) confirms severe drowsiness.

## Hardware Bill of Materials (BOM)
| Component | Specification | Quantity |
| :--- | :--- | :--- |
| Compute Node | PC / Laptop (or Raspberry Pi 4) | 1 |
| Vision Sensor | Standard USB Webcam (720p 30fps) | 1 |
| Microcontroller | ESP32 Development Board | 1 |
| Actuator Control | 5V DC Relay Module | 1 |
| Acoustic Alert | Active 5V Buzzer | 1 |
| Motor Prototype | 5V/12V DC Motor (Bench testing) | 1 |

## Complete Pinout & Wiring Matrix Table (ESP32)

| Component | Terminal / Type | ESP32 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **Buzzer** | Positive (+) | GPIO 12 | Digital Out for Acoustic Alert |
| | Negative (-) | GND | System Ground |
| **Motor Relay** | IN / Signal | GPIO 14 | Digital Out for Ignition Cutoff |
| | VCC | 5V | Relay coil power (Vin) |
| | GND | GND | System Ground |
| **Driver Reset Button** | Signal | GPIO 27 | Input Pullup (Overrides warning) |

## Repository Layout Tree
```text
.
├── assets/                # Captured system dashboard and hardware photos
├── diagrams/              # Additional UML and flow diagrams
├── docs/                  # Original architecture maps
├── esp32/                 # MicroPython / C++ MQTT controller scripts for ESP32
├── pc_ai/                 # Computer vision tracking and MQTT publishing logic
└── requirements.txt       # Python dependencies (OpenCV, Mediapipe, Paho-MQTT)
```

## Step-by-Step Setup & Prerequisites

### 1. MQTT Broker Setup
Ensure a local MQTT broker (e.g., Mosquitto) is running on your network. Update the `broker` IP address in both `pc_ai/driver_monitor.py` and the ESP32 code to match the broker's IP.

### 2. PC Vision Node
```bash
pip install -r requirements.txt
python pc_ai/driver_monitor.py
```

### 3. ESP32 Actuation Node
Flash `esp32/esp32_controller.py` to the ESP32 using Thonny IDE or ampy. Ensure the ESP32 is connected to the same Wi-Fi network as the MQTT broker.

## Authentic Documentation & Asset Links
- **Original Dashboard Mockup**: [`assets/dashboard_mockup.png`](assets/dashboard_mockup.png)
- **Legacy Architecture Diagram**: [`docs/system_architecture.png`](docs/system_architecture.png)

## Engineering Audit & Defensibility Limitations
- **Lighting Dependency**: Standard RGB webcams fail entirely in low-light automotive environments. A production system must utilize an IR-cut absent camera combined with active Near-Infrared (NIR 850nm/940nm) illumination to track pupils at night.
- **Ocular Occlusion**: The EAR algorithm struggles if the driver wears heavily tinted polarized sunglasses. Modern implementations often augment EAR with Head Pose Estimation (Pitch/Yaw/Roll) to detect the driver's head nodding or drooping even when the eyes are occluded.

---

**Hassan Moqbel Morshed Ghaleb**
Mechatronics Engineer | Mechanical Design & CAD (SolidWorks & AutoCAD) | Preventive Maintenance & Electromechanical Systems | Industrial Automation, Control Systems, Robotics & Intelligent Machines | CAD/FEA, Embedded Systems, Python & C++
[GitHub](https://github.com/Hassan-Moqbel) · [Facebook](https://www.facebook.com/share/1BqxAgVjHi/) · [LinkedIn](https://www.linkedin.com/in/hassan-moqbel)

## License
This project is licensed under the [MIT License](LICENSE).
