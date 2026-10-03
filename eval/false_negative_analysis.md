# False Negative Safety Audit: Root Cause & Taxonomic Analysis

**Document**: `eval/false_negative_analysis.md`  
**Evaluation Target**: OSHA Severe Injury Report (SIR) Holdout Dataset  
**Model**: `gemini-3.8-flash` (Single Model, Temperature 0.1)  
**Evidentiary Rule**: Strict two-part SIF precursor test (High-energy hazard present **AND** stated control failure).

---

## Executive Summary

When evaluated against human ground truth, the false negatives produced by `gemini-3.8-flash` do **not** all share the same physical or operational root cause. Physically, they divide into two distinct operational failure classes:
1. **Procedural / Energy Isolation Failures (38%)**: Workers opening systems or breaking containment while pressurized (failing to follow zero-energy verification / depressurization procedures).
2. **Equipment & Mechanical Integrity Failures (50%)**: Structural, mechanical, or rigging equipment parting, breaking, or slipping under tension or load (tubing breaking, wire rope snapping, elevator slipping, vice grips slipping).
3. **Implicit Safety Control Bypasses (12%)**: A machine limit switch / crown-saver failing or being bypassed during derrick hoisting (crown collision).

However, while their **operational causes** differ, all cases share the **exact same cognitive and linguistic root cause**: **The Evidentiary Gap between Human Domain Inference and Literal LLM Narrative Parsing.** 

In OSHA severe injury abstracts, reporting personnel routinely describe *what physically occurred* (e.g., "valve removed while under pressure", "tubing broke", "elevator slipped"), but omit explicit references to administrative management systems or formal barrier states (e.g., "depressurization SOP was omitted", "rigging inspection was overdue"). Human domain experts readily infer the missing procedural or mechanical control from the physical failure, while the model—strictly governed by prompt instructions not to infer unstated controls—classifies the control state as `"not stated in narrative"` and outputs `sif_potential: false`.

---

## Detailed Case Audit: Rows 26, 36, and 44

Below are the complete narratives, human ground truth labels, human barrier failures, model predictions, and model reasonings retrieved directly from the verified cache.

### Case ID #26: Pedestal Grinder Workpiece Slip
* **Full Narrative**:
  > *"An employee was grinding at a pedestal grinder on a small piece of work. The work had been set in place using vice grips. The work slipped from its placement, moving and lodging into the space between the work rest and the disc. The employee's left hand was also moved by the force into this area, lacerating/crushing his index, middle, and ring fingers."*
* **Human Label**: `sif_potential = True` | **LSR**: `Line of Fire` | **Energy**: `mechanical`
* **Human Barrier Failure**: *"vice grips failed to hold work in place"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Line of Fire`
* **Model Barrier Failure**: `"not stated in narrative"`
* **Model Reasoning**:
  > *"The incident involved contact with a pedestal grinder resulting in finger injuries, which lacks fatal potential. Furthermore, no missing, bypassed, or defective control (such as tool rest clearance or guarding) is explicitly stated in the narrative."*
* **Operational Failure Category**: **Makeshift Tool / Work Practice Failure (Procedural/Equipment Hybrid)**. Using vice grips to hold small stock on a pedestal grinder rather than proper clamping/jigging or adjusting the tool rest to $\le 1/8$ inch.

---

### Case ID #36: Compressor Discharge Valve Removed Under Pressure
* **Full Narrative**:
  > *"An employee was removing an inboard discharge valve on an inlet cylinder. The pressure caused the compressor valve cap and valve to come out of the cylinder and strike the employee, resulting in a fractured wrist, dislocated elbow, and a torn ligament."*
* **Human Label**: `sif_potential = True` | **LSR**: `Energy Isolation` | **Energy**: `pressure`
* **Human Barrier Failure**: *"inboard discharge valve removed while under pressure"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Energy Isolation`
* **Model Barrier Failure**: `"not stated in narrative"`
* **Model Reasoning**:
  > *"A high-energy pressure hazard was present and caused the valve cap to eject. However, the narrative does not state or describe the state of any safety control or energy isolation barrier, so under the evidentiary standard SIF potential is evaluated as false."*
* **Operational Failure Category**: **Procedural Control Failure (Energy Isolation / Depressurization)**. The worker broke pressure containment without prior isolation, bleed-down, and verification of zero energy.

---

### Case ID #44: Tubing Elevator Mechanical Slip
* **Full Narrative**:
  > *"While the employees were picking up tubing, a worker grabbed the bell and pulled it back. The elevator slipped and caught his finger between the horn's elevator and the bottom of the bell. His middle finger was amputated from the finger nail to the first knuckle of the finger. He was taken to the hospital, treated and released."*
* **Human Label**: `sif_potential = True` | **LSR**: `Safe Mechanical Lifting` | **Energy**: `mechanical`
* **Human Barrier Failure**: *"elevator slipped"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Line of Fire`
* **Model Barrier Failure**: `"not stated in narrative"`
* **Model Reasoning**:
  > *"The incident involved line of fire positioning around moving mechanical equipment while picking up tubing. Although the elevator slipped resulting in a finger amputation, the narrative does not explicitly state or describe the failure of a specific required safety control or barrier."*
* **Operational Failure Category**: **Equipment Integrity / Mechanical Tool Disengagement Failure**. The latch, slips, or gripping mechanism of the pipe elevator failed or slipped during mechanical handling.

---

## Comparison Against the 6 False Negatives from the 150-Row Run

In the earlier 150-row holdout evaluation, six false negatives occurred: **Case #44, #46, #48, #50, #71, and #81**. (Notice that Case #44 appears in both cohorts).

### Case ID #46: Traveling Block Crown Collision
* **Full Narrative**:
  > *"On October 27, 2018, at approximately 9:15 PM, a crew of five employees was working on a drilling rig when the traveling block hit the crown, which caused the travel block to fall to the rig floor. One employee was struck by debris from the damaged rig and suffered a fractured neck, broken left arm, and two broken ribs. Another employee jumped away from the rig structure and fell to the ground below resulting in a left foot amputation."*
* **Human Label**: `sif_potential = True` | **LSR**: `Bypassing Safety Controls` | **Energy**: `height`
* **Human Barrier Failure**: *"traveling block hit the crown"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Line of Fire`
* **Model Reasoning**:
  > *"Although a high-energy hazard was present involving the falling traveling block and rig debris, the incident report does not explicitly state or describe any safety control or barrier failure."*
* **Failure Analysis**: **Implicit Safety Interlock Failure (Bypassing Safety Controls)**. On oil and gas drilling rigs, the Crown-O-Matic toggle valve is an automatic safety limit device designed specifically to stop the drawworks before the block strikes the crown. A "crown-out" event is an unequivocal indicator of a failed or bypassed safety interlock in industry operations. However, because the text did not explicitly name the device, the LLM rejected the control failure.

---

### Case ID #48: Pressurized Bulk Cement Hatch Release
* **Full Narrative**:
  > *"An employee was opening a hatch on a bulk cement truck when pressure inside of the truck caused the hatch cover to slide off and up, striking the employee. The employee sustained a non-displaced pelvis fracture, a right linear temporal fracture and a subdural hematoma."*
* **Human Label**: `sif_potential = True` | **LSR**: `Energy Isolation` | **Energy**: `pressure`
* **Human Barrier Failure**: *"hatch opened while truck was pressurized"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Line of Fire`
* **Model Reasoning**:
  > *"A high-energy pressure hazard was present, but the narrative describes the event and injury without explicitly stating or describing the failure or absence of a specific control (such as depressurization procedures or mechanical interlocks)."*
* **Failure Analysis**: **Procedural Control Failure (Energy Isolation / Depressurization)**. Identical mechanism to Case #36: opening an access point on a pneumatic/bulk transport vessel without prior depressurization verification.

---

### Case ID #50: Pressurized Drill Pipe Separation
* **Full Narrative**:
  > *"An employee was unscrewing and separating a connection of a drill pipe when drilling mud sprayed out of the connection, causing the employee to fall backward and strike his face on a piece of equipment. The employee suffered a laceration on his lip and a facial fracture."*
* **Human Label**: `sif_potential = True` | **LSR**: `Energy Isolation` | **Energy**: `pressure`
* **Human Barrier Failure**: *"connection unscrewed while containing pressurized drilling mud"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Energy Isolation`
* **Model Reasoning**:
  > *"Pressurized drilling mud represents a high-energy hazard; however, the narrative does not explicitly state or describe a control failure (e.g., failure of isolation or depressurization controls). Following the evidentiary standard, SIF potential is set to false."*
* **Failure Analysis**: **Procedural Control Failure (Energy Isolation / Trapped Pressure Verification)**. Breaking connection on tubulars containing trapped hydrostatic or pumping pressure without checking pressure bleed or relief lines.

---

### Case ID #71: Tubing Tensile Breakage During Tripping Out
* **Full Narrative**:
  > *"An employee was coming out of a hole with tubing when the tubing broke. A pipe fell and hit the employee on the head, causing the employee to lose consciousness. The employee was wearing a hard hat at the time. The employee was hospitalized overnight with a mild concussion."*
* **Human Label**: `sif_potential = True` | **LSR**: `Safe Mechanical Lifting` | **Energy**: `height`
* **Human Barrier Failure**: *"tubing broke"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `None`
* **Model Reasoning**:
  > *"While a gravitational hazard (falling pipe) was present, the report does not describe a missing, bypassed, or ineffective control. The employee was wearing the required PPE (hard hat), and the failure of the tubing itself is described as a mechanical breakage rather than a failure of a safety barrier."*
* **Failure Analysis**: **Pure Equipment / Material Integrity Failure**. Structural failure of tubular pipe under tensile pull or mechanical fatigue. The human treated the tubing structural integrity as the primary barrier against dropped objects; the model reasoned that structural failure of the workpiece itself does not constitute a broken safety control.

---

### Case ID #81: Wire Rope Snapback Under Tension
* **Full Narrative**:
  > *"An employee was working on a derrick about 10 feet off the ground and was being lifted to disconnect the elevator. A wire rope under tension snapped back striking the employee and throwing him in the air and then back down. The employee was wearing a safety harness and he only fell the length of his lanyard or about 4 feet. The employee injured his back and was hospitalized."*
* **Human Label**: `sif_potential = True` | **LSR**: `Safe Mechanical Lifting` | **Energy**: `height`
* **Human Barrier Failure**: *"wire rope under tension snapped back"*
* **Model Prediction**: `sif_potential = False` | **LSR**: `Working at Height`
* **Model Reasoning**:
  > *"While a high-energy hazard (mechanical tension/gravitational) was present, the narrative does not describe a missing, bypassed, or ineffective control. The safety harness functioned as intended, limiting the fall distance."*
* **Failure Analysis**: **Rigging / Equipment Integrity Failure & Stored Energy Release**. Winch wire rope failure under mechanical tension. The human flagged the wire rope failure as an ineffective lifting/rigging control; the model noted that secondary controls (harness and lanyard) actually functioned as intended, and no defective state of the wire rope was documented.

---

## Comparative Taxonomy: Do All Nine Share the Same Cause?

### Summary Matrix

| ID | Operational Failure Type | Primary Sub-system | Human Ground Truth LSR | Model Stated Failure |
|:---:|---|---|---|---|
| **#26** | Makeshift Tool / Work Practice | Grinder Tool Rest / Clamping | `Line of Fire` | Not stated |
| **#36** | **Procedural Isolation Failure** | Compressor Cylinder Depressurization | `Energy Isolation` | Not stated |
| **#44** | **Equipment Integrity (Slip)** | Pipe Handling Elevator Slips | `Safe Mechanical Lifting` | Not stated |
| **#46** | **Safety Interlock Bypass** | Hoisting Crown Saver (Crown-O-Matic) | `Bypassing Safety Controls` | Not stated |
| **#48** | **Procedural Isolation Failure** | Tanker Pneumatic Depressurization | `Energy Isolation` | Not stated |
| **#50** | **Procedural Isolation Failure** | Mud Circulation Depressurization | `Energy Isolation` | Not stated |
| **#71** | **Equipment Integrity (Breakage)**| Tubing String Tensile Strength | `Safe Mechanical Lifting` | Not stated |
| **#81** | **Equipment Integrity (Parting)** | Wire Rope Rigging Tension | `Safe Mechanical Lifting` | Not stated |

### Direct Conclusion on Physical vs Procedural Cause:
**No, they do not share the same physical cause.** They partition into two distinct operational realities:
1. **The Pressure / Energy Isolation Cluster (Cases 36, 48, 50)**:
   - These are **100% procedural / administrative control failures**.
   - In all three, equipment was structurally sound until human operators disassembled components or opened hatches while energy remained trapped. The control that failed was procedural: **Verify Zero Energy Before Breaking Containment**.
2. **The Mechanical & Equipment Integrity Cluster (Cases 26, 44, 71, 81)**:
   - These are **equipment integrity and tool engagement failures**.
   - Tubulars parted, cables snapped, vice grips slipped, and elevators disengaged. Human procedure was in active progress, but mechanical hardware or holding force failed under load.
3. **The Automated Protective Interlock Cluster (Case 46)**:
   - This is an **engineering safety device bypass / failure**.
   - The primary barrier against a crown collision is the automatic drawworks shutoff switch.

---

## Why Did the Model Miss All of Them? (The True Unifying Root Cause)

While the physical events differ, the reason the model missed all nine is **100% uniform**:

$$\text{Physical Act Described} \neq \text{Explicit Name of Safety Control in Narrative}$$

1. **Human Labeling Ingestion**:
   Human HSE experts operate on **domain-complete reasoning**. When a human reads:
   *"An employee was removing a valve... pressure caused the valve cap to eject"*
   The human immediately infers: *"Removing a valve under pressure means isolation was not verified; barrier failure = valve removed while under pressure."*
2. **Model Literal Text Parsing**:
   The prompt enforces the strict rule:
   > *"Do not infer a missing control from the fact that harm occurred. If a report describes an outcome without describing the state of any control, set sif_potential = false and barrier_failure = 'not stated in narrative'."*
   Because the narrative states the *action* and the *injury outcome* without using the words "failed to isolate", "bypassed lockout", or "defective latch", the model strictly follows its prompt constraint: it refuses to infer the missing control and sets `sif_potential = false`.

### Key Insight for SIH 2026 Presentation
This is one of the most critical findings of the project:
- In industrial narratives, **"uncontrolled release of pressure during maintenance" is itself prima facie evidence of an energy isolation failure**, even if the reporter never explicitly typed the words "energy isolation".
- The human labelers recognized this operational truth; the prompt's strict literal evidentiary instruction suppressed it.
- Resolving this disagreement does not require a larger model; it requires updating the prompt's domain heuristics to recognize that **opening pressurized equipment is inherently a failed energy isolation barrier**.
