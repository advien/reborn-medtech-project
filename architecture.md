# Reborn — System Architecture

## Purpose of this document
This document describes the **system architecture** of the Reborn MVP:
an active elbow orthosis with human-in-the-loop control, based on EMG and IMU signals.

The goal is not to define a final product, but to:
- fix **system intent**
- define **clear module boundaries**
- make assumptions, constraints, and failure handling explicit

This architecture is designed to be:
- modular
- safety-first
- explainable to engineers, not only ML specialists

---

## High-level system view

```text
Human (user)
  │
  │ muscle activation / motion
  ▼
[Sensing Layer]
  │  EMG, IMU
  ▼
[Signal Quality & Preprocessing]
  │
  ▼
[State Estimation / Features]
  │
  ├── (optional) ML inference
  │
  ▼
[Decision Logic]
  │
  ▼
[Actuation]
  │
  ▼
[Safety Layer]  ← always-on
  │
  ▼
Physical interaction + feedback