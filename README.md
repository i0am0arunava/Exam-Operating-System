# Exam Operating System (Custom Lightweight OS for Online Examinations)

## Overview

The **Exam Operating System** is a lightweight, custom-built operating environment designed specifically for secure online examinations. It is inspired by controlled exam platforms like TCS iON but takes a more foundational approach by moving enforcement logic into the operating system layer itself.

Rather than relying on application-level restrictions, this system enforces exam integrity through a minimal Linux-based OS stack built on **Alpine Linux**, with custom components for window management, process control, and shell interaction.

The system was developed as a group project by **Arunava (you)** and **Piyush Kumar Rai**, under the guidance of **Dipta Mukherjee**.

---

## Motivation

Most existing online examination systems operate at the application layer and attempt to restrict user behavior using:

* Window focus locks
* Keyboard shortcut blocking
* Screen recording detection
* Clipboard restrictions

However, these mechanisms are inherently bypassable in modern desktop environments.

### Key Problems in Application-Level Systems

* Hidden processes can run beneath exam applications
* Window spoofing or overlay attacks using X11/Wayland APIs
* Screen capture bypass techniques (virtual displays, compositors)
* Multi-process manipulation by advanced users

For example, Linux-based environments allow:

* Xlib / XCB based overlay injection
* `_NET_WM_BYPASS_COMPOSITOR` misuse
* XComposite layer manipulation

On Windows:

* `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)` can hide content from screen recording tools while remaining visible locally

These limitations motivated a deeper system-level approach.

---

## Our Approach

Instead of building security on top of an OS, we built the OS around the security model.

We use **Alpine Linux** as a minimal and secure base and extend it with custom system components.

Inspired by minimal container OS design (like Docker environments), we retain only essential system components and build everything else from scratch.

---

## System Architecture

```
Hardware
   │
   ▼
Alpine Linux Base
   │
   ▼
X11 / Display Server
   │
   ▼
Custom Window Manager (C)
   │
   ▼
Custom Shell (C)
   │
   ▼
Custom Process Manager (C / Assembly)
   │
   ▼
Exam Application Layer (Restricted Environment)
```

### Architecture Diagram Placeholder

<img width="1220" height="591" alt="Screenshot From 2026-05-16 00-36-31" src="https://github.com/user-attachments/assets/330bba2e-335d-4e55-ba0f-b150f63f88e1" />

---

## Operating System Design

The OS is structured as a controlled execution environment where only approved processes are allowed.

### Core Design Principles

* Minimal attack surface (Alpine Linux base)
* Full control of process lifecycle
* Restricted windowing system
* No unauthorized background execution
* Controlled networking layer (local-only exam distribution)

---

### Custom Components

#### 1. Window Manager (C)

* Controls all GUI rendering
* Prevents unauthorized window creation
* Restricts switching between applications
* Manages full-screen exam mode

#### 2. Shell (C)

* Initializes system services
* Starts X server and display stack
* Launches exam runtime environment only
* Blocks unauthorized command execution

#### 3. Process Manager (C + Assembly)

* Tracks all running processes
* Kills unauthorized processes immediately
* Ensures single-purpose execution model
* Enforces exam-only runtime policy

---

## Security Model

The security model shifts enforcement from:

> Application-level detection

to

> System-level execution control

### Key Security Advantages

* No multi-tasking outside exam environment
* No background process persistence
* No shell escape outside controlled layer
* Reduced dependency on user-space security checks

---

## Features

* Auto-updates via private Git repository
* Local network-based question distribution
* Native compiler integration for coding exams
* Locked execution environment
* Minimal GUI stack

---

## Setup Requirements

| Component | Requirement         |
| --------- | ------------------- |
| CPU       | Dual-core or higher |
| RAM       | 4 GB minimum        |
| Storage   | 16 GB minimum       |

---

## Tech Stack

* C Language — Window Manager
* Assembly — Process Manager
* Shell Scripting — Boot & initialization
* Git — Auto update system
* Alpine Linux — Base OS

---

## OS Boot Flow

1. Hardware initialization
2. Alpine Linux kernel boot
3. X11 display server start
4. Custom window manager launch
5. Shell initialization
6. Process manager activation
7. Exam environment lock

---

## Reflection

This project demonstrates a shift from application-level security to OS-level enforcement design.

Future improvements:

* Wayland migration
* Kernel-level hardening
* TPM-based attestation
* Secure boot integration

---

## Image

<img width="1842" height="1046" alt="Screenshot From 2026-05-15 21-54-01" src="https://github.com/user-attachments/assets/bfec6816-98f5-4839-9172-3fb3506df07d" />


---

## Repository

[https://github.com/i0am0arunava/Exam-Operating-System](https://github.com/i0am0arunava/Exam-Operating-System)

---

## Tags

#OperatingSystem #Linux #SystemDesign #Security #OpenSource
