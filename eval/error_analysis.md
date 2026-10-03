# SIF Precursor Classification: Comprehensive Error Analysis

**Document**: `eval/error_analysis.md`  
**Evaluation Target**: OSHA Severe Injury Report (SIR) Holdout Dataset  
**Model**: `gemini-3.8-flash` (Cached evaluation results, temperature 0.1)  
**Dataset Support in Evaluation**: 38 Evaluated Holdout Records (5 SIF-Positive, 33 SIF-Negative)

---

## Executive Summary

This error analysis examines all discrepancies between human ground truth and the single runtime model (`gemini-3.8-flash`) across the evaluated holdout set:
- **3 False Negatives (FN)**: Rows **26, 36, 44** (Human = `True`, Model = `False`)
- **4 False Positives (FP)**: Rows **13, 21, 22, 28** (Human = `False`, Model = `True`)

A fundamental symmetry emerges from this audit:
1. **False Negatives occur when the human infers a failed control from a physical failure** (e.g. removing a valve under pressure, vice grips slipping, elevator slipping), but the text lacks formal administrative vocabulary, causing the model's strict evidentiary filter to reject the case.
2. **False Positives occur when the model treats worker exposure inside a crush/drop zone as an active breach of a Line-of-Fire barrier**, whereas human labelers marked `barrier_failure = "not stated in narrative"` unless an engineered guard or explicit barrier was mentioned.

---

## Part 1: False Negative Audit (Human = TRUE, Model = FALSE)

These are safety-critical errors where a true high-potential precursor was missed by the automated classifier.

---

### Case ID #26: Pedestal Grinder Workpiece Slip
* **Full Narrative**:
  > *"An employee was grinding at a pedestal grinder on a small piece of work. The work had been set in place using vice grips. The work slipped from its placement, moving and lodging into the space between the work rest and the disc. The employee's left hand was also moved by the force into this area, lacerating/crushing his index, middle, and ring fingers."*
* **Human Label**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Line of Fire**
  - `barrier_failure`: *"vice grips failed to hold work in place"*
* **Model Prediction**:
  - `sif_potential`: **False**
  - `lsr_tag`: **Line of Fire**
  - `barrier_failure`: *"not stated in narrative"*
* **Model Reasoning**:
  > *"The incident involved contact with a pedestal grinder resulting in finger injuries, which lacks fatal potential. Furthermore, no missing, bypassed, or defective control (such as tool rest clearance or guarding) is explicitly stated in the narrative."*
* **Root Cause Breakdown**:
  - **Human Perspective**: Vice grips were serving as the physical holding barrier to keep the worker's hands away from the rotating wheel; their slippage into the rest gap constitutes a barrier failure under Line of Fire.
  - **Model Perspective**: The model evaluated pedestal grinder finger contact as lacking fatal energy potential, and noted that no mandatory OSHA machine guard (such as the 1/8-inch tool rest gap rule) was stated as defective in the text.

---

### Case ID #36: Compressor Discharge Valve Removed Under Pressure
* **Full Narrative**:
  > *"An employee was removing an inboard discharge valve on an inlet cylinder. The pressure caused the compressor valve cap and valve to come out of the cylinder and strike the employee, resulting in a fractured wrist, dislocated elbow, and a torn ligament."*
* **Human Label**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Energy Isolation**
  - `barrier_failure`: *"inboard discharge valve removed while under pressure"*
* **Model Prediction**:
  - `sif_potential`: **False**
  - `lsr_tag`: **Energy Isolation**
  - `barrier_failure`: *"not stated in narrative"*
* **Model Reasoning**:
  > *"A high-energy pressure hazard was present and caused the valve cap to eject. However, the narrative does not state or describe the state of any safety control or energy isolation barrier, so under the evidentiary standard SIF potential is evaluated as false."*
* **Root Cause Breakdown**:
  - **Human Perspective**: Removing a valve while the system remains pressurized is prima facie evidence that energy isolation / depressurization procedures were omitted or failed.
  - **Model Perspective**: The prompt strictly instructs: *"Do not infer a missing control from the fact that harm occurred. If a report describes an outcome without describing the state of any control, set sif_potential = false"*. The report describes the physical act and outcome without explicitly naming an isolation barrier or LOTO SOP.

---

### Case ID #44: Tubing Elevator Mechanical Handling Slip
* **Full Narrative**:
  > *"While the employees were picking up tubing, a worker grabbed the bell and pulled it back. The elevator slipped and caught his finger between the horn's elevator and the bottom of the bell. His middle finger was amputated from the finger nail to the first knuckle of the finger. He was taken to the hospital, treated and released."*
* **Human Label**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Safe Mechanical Lifting**
  - `barrier_failure`: *"elevator slipped"*
* **Model Prediction**:
  - `sif_potential`: **False**
  - `lsr_tag`: **Line of Fire**
  - `barrier_failure`: *"not stated in narrative"*
* **Model Reasoning**:
  > *"The narrative describes the elevator slipping and catching a worker's finger during tubing handling, but does not explicitly state or describe any missing, bypassed, or failed controls. Per the evidentiary standard, SIF potential cannot be inferred and is marked false."*
* **Root Cause Breakdown**:
  - **Human Perspective**: Pipe elevators are the primary mechanical lifting control securing tubing during hoisting; the elevator slipping is an operational failure of mechanical lifting controls.
  - **Model Perspective**: The narrative states the physical slippage as an occurrence, but does not describe why it slipped (e.g. defective latch pin, worn slips, or improper rigging), causing the model to default to *"not stated in narrative"*.

---

## Part 2: False Positive Audit (Human = FALSE, Model = TRUE)

These are cases where the human labeler judged the incident as Non-SIF (often because no physical control was explicitly discussed), but the model identified fatal-potential energy and flagged an active control failure.

Grouping the False Positives by the **Model's Stated Barrier Failure**:

---

### Group A: Mechanical Hoist Control Failure (Winch Control Descent Rate)

#### Case ID #13: Hydraulic Hoist Winch Rapid Descent
* **Full Narrative**:
  > *"An employee was moving a metal pipe with a hydraulic hoist when the winch came down faster than expected. This caused the pipe to fall and as the employee went to catch it, his finger was pinched. The employee's right index finger was partially amputated."*
* **Human Label**:
  - `sif_potential`: **False**
  - `lsr_tag`: `None` (`NaN`)
  - `barrier_failure`: *"not stated in narrative"*
* **Model Prediction**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Safe Mechanical Lifting**
  - **Model Stated Barrier Failure**:
    > *"The winch control mechanism failed, causing it to descend faster than expected."*
* **Model Reasoning**:
  > *"A high-energy hazard (gravitational/suspended load) was present. The narrative directly describes a control failure where the winch descended faster than expected, failing to safely control the load."*
* **Analysis**:
  - The model treated *"the winch came down faster than expected"* as an explicit, described malfunction/failure of a mechanical hoist control mechanism under **Safe Mechanical Lifting**.
  - The human labeler appears to have judged that a single metal pipe falling during manual handling lacked fatal potential, or viewed the phrase as too vague to confirm an equipment defect.

---

### Group B: Line-of-Fire / Zone Boundary Control Breaches Around Suspended & Moving Heavy Loads

In all three of these incidents, the model's stated barrier failure is that **a worker positioned their body or reached into an active drop zone or crush point of heavy oilfield equipment**.

#### Case ID #21: Reaching for Slipping Well Pipe
* **Full Narrative**:
  > *"The employee was assisting with mobile rig removal from a well site. As pipe was being pulled from the hole, rope used for pullout got caught up and pipe began to slip. The employee reached in to grab the pipe and his hand/finger was caught between piping and the drilling equipment, resulting in amputation of the right middle finger down to the knuckle."*
* **Human Label**:
  - `sif_potential`: **False**
  - `lsr_tag`: `None` (`NaN`)
  - `barrier_failure`: *"not stated in narrative"*
* **Model Prediction**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Line of Fire**
  - **Model Stated Barrier Failure**:
    > *"Pullout rope fouled causing uncontrolled pipe movement and the worker reached directly into the line of fire/pinch point of moving equipment"*
* **Model Reasoning**:
  > *"Pulling pipe from a well involves heavy mechanical and gravitational energy. When the pipe slipped, the worker breached line-of-fire controls by reaching in between the pipe and drilling equipment, an action with fatal potential if pulled into moving machinery or crushed by heavy tubulars."*

#### Case ID #22: Sitting in the Drop/Crush Zone Behind Forklifted Slide
* **Full Narrative**:
  > *"While cleaning equipment prior to rig down, an employee was working with a rig contractor to rig down a centrifuge slide with a forklift. The employee was sitting on a beam under the centrifuge and behind the slide when the slide slipped off the forklift, swinging and pinning the employee against the beam of the centrifuge. He sustained a fractured tibia and fibula just below the left knee."*
* **Human Label**:
  - `sif_potential`: **False**
  - `lsr_tag`: `None` (`NaN`)
  - `barrier_failure`: *"not stated in narrative"*
* **Model Prediction**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Line of Fire**
  - **Model Stated Barrier Failure**:
    > *"Employee was positioned in the line of fire/pinch point under and behind an unsecured load being handled by a forklift"*
* **Model Reasoning**:
  > *"A heavy load (centrifuge slide) being handled by a forklift slipped and swung, striking and pinning an employee who was sitting directly beneath and behind the load within its drop and crush zone."*

#### Case ID #28: Placing Board Beneath Active Hoisted Drill Collar
* **Full Narrative**:
  > *"Employees were laying down an 8\" drill collar from the catwalk using the main rig hoist. During this, the injured employee was placing a 3x6 wooden board under the collar. When the collar came in contact with the board, it caused the end of the board to rise up, partially degloving the employee's left shin that required a skin graft."*
* **Human Label**:
  - `sif_potential`: **False**
  - `lsr_tag`: `None` (`NaN`)
  - `barrier_failure`: *"not stated in narrative"*
* **Model Prediction**:
  - `sif_potential`: **True**
  - `lsr_tag`: **Line of Fire**
  - **Model Stated Barrier Failure**:
    > *"Employee positioned in the line of fire manually placing a wooden board under an active, hoisted drill collar"*
* **Model Reasoning**:
  > *"A high-energy gravitational and mechanical hazard was present (handling a heavy 8\" drill collar with a rig hoist). Line of fire controls failed when the worker manually placed a board directly beneath the moving load while it was being lowered."*

---

## Part 3: Taxonomic Comparison & Synthesis

### Summary Comparison Table

| Row ID | Human SIF | AI SIF | Error Type | Stated Energy Hazard | Core Disagreement Factor |
|:---:|:---:|:---:|:---:|:---:|---|
| **26** | **True** | **False** | False Negative | Mechanical (Grinder) | Human counted vice grips as failed barrier; AI saw low energy and no guard failure. |
| **36** | **True** | **False** | False Negative | Pressure (Cylinder) | Human inferred isolation failure; AI rejected because LOTO/bleed procedure unstated. |
| **44** | **True** | **False** | False Negative | Mechanical (Elevator) | Human treated elevator slip as lifting barrier failure; AI saw unstated mechanism. |
| **13** | **False** | **True** | False Positive | Gravitational (Hoist) | AI treated "winch descended fast" as mechanical control failure; Human saw minor pipe pinch. |
| **21** | **False** | **True** | False Positive | Mechanical / Tension | AI treated reaching into moving drill pipe as Line of Fire breach; Human labeled no barrier failure. |
| **22** | **False** | **True** | False Positive | Suspended Load | AI treated sitting under forklift load as Line of Fire breach; Human labeled no barrier failure. |
| **28** | **False** | **True** | False Positive | Gravitational (Collar) | AI treated placing board under hoisted 8" collar as Line of Fire breach; Human labeled no barrier failure. |

---

## Core Findings & Recommendations

1. **The Asymmetry of "Line of Fire"**:
   - The AI classifier treats the IOGP Life-Saving Rule **Line of Fire** as an active behavioral/operational control. If a worker puts themselves directly beneath a suspended 8" drill collar (#28), under a forklifted centrifuge slide (#22), or reaches into moving tubulars (#21), the model logs this as a **Line of Fire control failure**.
   - Human labelers, by contrast, reserved `sif_potential = True` for cases with an engineered barrier breakdown (e.g. physical guards, interlocks, or equipment integrity). They treated poor body positioning without an engineered failure as `barrier_failure = "not stated in narrative"`.

2. **The Asymmetry of "Energy Isolation"**:
   - For pressurized line-breaking (#36), the human labeler applied industrial common sense: you cannot have high-pressure discharge during valve removal unless isolation failed.
   - The AI strictly parsed the text and found no mention of valves, locks, or permits, triggering the literal evidentiary stop rule.

3. **Strategic Adjustment for Prompt Development**:
   To align the model with human ground truth without sacrificing precision:
   - **Narrow Line of Fire**: Instruct the model that body positioning errors during manual material handling do not constitute a SIF barrier failure unless a formal exclusion zone, barricade, or engineered guard was bypassed.
   - **Broaden Energy Isolation**: Explicitly define that **uncontrolled release of stored pressure during active disassembly, unbolting, or maintenance is per se evidence of an Energy Isolation failure**, even if the report does not mention the word "procedure" or "LOTO".
