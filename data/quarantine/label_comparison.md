# Fatality Holdout: Human vs. AI Label Comparison

## Executive Summary

This evaluation compares initial zero-shot AI classifications (`ai_labels_v0`) against human ground truth (`labeling`) across 48 oil-and-gas fatality holdout narratives in `data/fatality_holdout_FINAL.xlsx`. The results highlight a fundamental systemic bias: the uncalibrated AI labeled 47/48 (97.9%) of records as SIF-potential, whereas human experts applying the rigorous two-part definition identified only 19/48 (39.6%). Because the model incorrectly treated fatality outcomes as de facto evidence of a control failure, it generated 28 false positives, resulting in an overall agreement of only 41.7% and a near-chance Cohen's kappa of 0.0275. When both agreed a SIF precursor existed, Life-Saving Rule (LSR) alignment reached 63.2% (12/19).

---

## Key Metrics

- **Total Evaluated Records**: 48
- **Overall Agreement on `sif_potential`**: **41.67%** (20/48)
- **Cohen's Kappa ($\kappa$)**: **0.0275** (slight / near-chance agreement due to extreme model positive bias)
- **`lsr_tag` Agreement (when both marked TRUE)**: **63.16%** (12/19)

---

## 2x2 Confusion Matrix

| Human (Ground Truth) \ AI (Prediction) | AI = TRUE (SIF) | AI = FALSE (Non-SIF) | Total Human |
|---|:---:|:---:|:---:|
| **Human = TRUE (SIF)** | **19** (TP) | **0** (FN) | **19** |
| **Human = FALSE (Non-SIF)** | **28** (FP) | **1** (TN) | **29** |
| **Total AI** | **47** | **1** | **48** |

> **Takeaway**: Recall on the human SIF-positive class is 100% (19/19, zero false negatives), but precision is only 40.43% due to 28 false positives where narratives lacked evidence of a failed or absent control.

---

## LSR Tag Agreement Breakdown (Both Marked TRUE)

Across the 19 cases where both Human and AI agreed on `sif_potential = TRUE`, 12 cases matched the exact Life-Saving Rule:

| ID | Human LSR Tag | AI LSR Tag | Matched? |
|---|---|---|:---:|
| 154 | Hot Work | Hot Work | ✅ Yes |
| 155 | Line of Fire | Line of Fire | ✅ Yes |
| 160 | Working at Height | Working at Height | ✅ Yes |
| 163 | Confined Space | Energy Isolation | ❌ No |
| 164 | Hot Work | Confined Space | ❌ No |
| 171 | Working at Height | Working at Height | ✅ Yes |
| 172 | Hot Work | Confined Space | ❌ No |
| 173 | Energy Isolation | Line of Fire | ❌ No |
| 178 | Hot Work | Hot Work | ✅ Yes |
| 179 | Working at Height | Working at Height | ✅ Yes |
| 180 | Energy Isolation | Line of Fire | ❌ No |
| 181 | Driving | Driving | ✅ Yes |
| 183 | Energy Isolation | Energy Isolation | ✅ Yes |
| 186 | Hot Work | Confined Space | ❌ No |
| 187 | Ground Disturbance | Line of Fire | ❌ No |
| 188 | Confined Space | Confined Space | ✅ Yes |
| 189 | Driving | Driving | ✅ Yes |
| 194 | Line of Fire | Line of Fire | ✅ Yes |
| 199 | Working at Height | Working at Height | ✅ Yes |

---

## Disagreements on `sif_potential`

Below are the **28** records where Human and AI disagreed. In every single case (**28/28**), Human marked `FALSE` while AI marked `TRUE` because the narrative did not demonstrate a missing, bypassed, or ineffective barrier.

| ID | Human SIF | AI SIF | Human `barrier_failure` | Narrative Snippet (First 120 chars) |
|---|:---:|:---:|---|---|
| 153 | `False` | `True` | not stated in narrative | ON THE MORNING OF APRIL 13, 1992, EMPLOYEES #1 AND #2 WERE KILLED WHEN A PRESSURE VESSEL EXPLODED NEAR THEM. THE UNFIRED... |
| 156 | `False` | `True` | not stated in narrative | At 12:05 a.m. on December 5, 2022, an employee was performing pipe tripping operations to remove the pipe from a newly d... |
| 157 | `False` | `True` | not stated in narrative | On January 4, 2011, Employee #1, a motorman of an oil drilling rig was, struck by an unexpected release of pressurized d... |
| 158 | `False` | `True` | not stated in narrative | Employee #1 and four other employees were working on a drilling rig floor during a washdown operation. Two employees wer... |
| 159 | `False` | `True` | not stated in narrative | On January 22, 2011, Employee #1 and a coworker were struck by a mousehole pipe as it was being lifted from the rig floo... |
| 161 | `False` | `True` | not stated in narrative | On July 20, 2015, an employee was operating a vacuum truck to transfer flowback water from a frac tank. The employee was... |
| 162 | `False` | `True` | not stated in narrative | Employee #1 was working as a floorhand on a drilling rig. The crew was in the process of picking up drill pipe. Employee... |
| 165 | `False` | `True` | not stated in narrative | An employee was operating a forklift to move drill pipe to the rig floor. The forklift mast contacted an overhead power ... |
| 166 | `False` | `True` | not stated in narrative | Employees were tripping pipe out of the hole. The drill pipe became stuck. While the crew was attempting to work the pip... |
| 167 | `False` | `True` | not stated in narrative | An employee was checking the fluid level in a production tank on a well site. He opened the thief hatch on the top of th... |
| 168 | `False` | `True` | not stated in narrative | Employee #1 was working on the rig floor while the crew was drilling ahead. His coveralls became caught in the rotating ... |
| 169 | `False` | `True` | not stated in narrative | During rig down operations, an employee was attempting to unpin the walking beam of a pumping unit. The beam shifted une... |
| 170 | `False` | `True` | not stated in narrative | Employees were laying down drill pipe. A joint of pipe rolled off the pipe racks and struck Employee #1 in the legs, kno... |
| 174 | `False` | `True` | not stated in narrative | Employee #1 entered a cellar around a wellhead to tighten a leaking flange. The cellar was approximately 6 feet deep. Hy... |
| 175 | `False` | `True` | not stated in narrative | At 3:00 p.m. on June 10, 2017, an employee was working as a floorhand on a drilling rig. While he was guiding a joint of... |
| 176 | `False` | `True` | not stated in narrative | An employee was tasked with checking the fluid levels of a crude oil storage tank. When the employee opened the thief ha... |
| 177 | `False` | `True` | not stated in narrative | Employee #1 was operating a pulling unit. The mast of the unit collapsed due to structural failure while pulling tubing ... |
| 182 | `False` | `True` | not stated in narrative | Employee #1 was assisting with a wireline operation on a well. The wireline cable was under high tension when a sheave w... |
| 184 | `False` | `True` | not stated in narrative | Employee #1 was transferring flowback fluids from a frac tank to a tanker truck. He climbed to the top of the tanker to ... |
| 185 | `False` | `True` | not stated in narrative | Employees were conducting well servicing operations on a pulling unit. A sudden release of pressurized gas from the well... |
| 190 | `False` | `True` | not stated in narrative | Employee #1 was gauging a crude oil storage tank on a well site. He ascended the stairs to the top of the tank and opene... |
| 191 | `False` | `True` | not stated in narrative | A drilling crew was in the process of tripping pipe out of the hole. Employee #1 was operating the manual tongs. The snu... |
| 192 | `False` | `True` | not stated in narrative | Employee #1 and a coworker were pressure testing a newly assembled manifold system. A high-pressure flexible hose ruptur... |
| 193 | `False` | `True` | not stated in narrative | An employee was driving a vacuum truck carrying produced water down a steep, unpaved lease road. The vehicle lost brakin... |
| 195 | `False` | `True` | not stated in narrative | Employee #1 was working on a pumping unit that had been shut down for maintenance. The brake failed, causing the walking... |
| 196 | `False` | `True` | not stated in narrative | An employee was using a grinder on a section of drill pipe. A spark ignited residual flammable vapors near a temporary s... |
| 197 | `False` | `True` | not stated in narrative | A crew was rigging down a workover rig. While lowering the derrick, a guy wire snapped. The derrick collapsed and struck... |
| 198 | `False` | `True` | not stated in narrative | Employee #1 was tasked with hydro-testing a pipeline segment. A pressurized plug failed and ejected from the pipe at hig... |

---

## Diagnostic Insights & SIF Methodology Validation

1. **Outcome Bias in Zero-Shot LLMs**:
   The zero-shot AI assumed that because a fatality occurred, a control must have failed. Human safety experts strictly enforce the definition: *SIF-potential requires high energy AND an identified barrier failure*.
2. **Information Scarcity in OSHA Abstracts**:
   Many OSHA abstracts simply state what occurred (e.g. medical collapse, heart failure, lightning, unassisted medical emergency) or report an injury without documenting whether proper safeguards were missing or breached.
   Human labelers correctly marked these as `barrier_failure = not stated in narrative` or `not applicable`, producing `sif_potential = FALSE`.
3. **LSR Rule Nuances**:
   Where both agreed on SIF, disagreements in LSR tagging occurred on overlapping hazard mechanisms (e.g., `Confined Space` vs. `Hot Work`, or `Energy Isolation` vs. `Line of Fire`).
