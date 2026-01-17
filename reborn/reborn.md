## Reborn — Human-in-the-loop Assistive Robotics System (R&D case)

**Reborn** is a system-level R&D case exploring how to design a **safe, human-in-the-loop active elbow orthosis**, combining EMG and IMU sensing, deterministic control logic, and optional ML — without over-relying on black-box models.

### What this project demonstrates
- **Systems thinking:** clear separation of sensing, signal quality, decision logic, actuation, and safety layers  
- **Human-in-the-loop design:** the user is treated as part of the control system, not just a signal source  
- **Safety-first philosophy:** deterministic safety layer with explicit failure modes and overrides  
- **Pragmatic ML usage:** ML is optional, bounded, and used only where it improves robustness or confidence — never as a controller  
- **Real-world constraints:** signal drift, uncertainty, latency, user adaptation, and degraded conditions are first-class design inputs

### Scope (MVP)
- Active elbow orthosis, **assist flexion**
- EMG + IMU sensing (single and fused)
- Confidence-gated decision logic
- Explicit fallback and emergency behaviors
- Hypothesis-driven experiments instead of benchmark-driven ML

### What is intentionally out of scope
- Medical certification or clinical claims  
- Product-level mechanical design  
- ML-driven autonomous control  

These exclusions are deliberate to reduce risk and keep the system explainable.

### Key artifacts
- System architecture with explicit module boundaries  
- Data collection protocol focused on failure visibility, not dataset size  
- Safety specification with deterministic overrides  
- Experiment plan validating behavior under uncertainty and degradation  

### Why it matters
Reborn shows how assistive and robotic systems can be designed to **fail safely**, remain interpretable, and respect the human as an active participant — a mindset critical for MedTech, robotics R&D, and applied AI in the physical world.

> This is not a demo gadget.  
> It is a control system designed around uncertainty, safety, and human interaction.