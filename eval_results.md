# Classical Philosophy & Statecraft Text Explorer - Evaluation Report

## 1. Executive Summary

This report documents the rigorous evaluation of the grounded RAG application against the 50-page compendium of classical Indian statecraft (*Arthashastra*) and philosophy (*Bhagavad Gita*).

## 2. Core Assessment Questions (Q1 - Q5)

| ID | Question | Expected Behavior | Actual Status | Rerank Score | Verified Citations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1** | According to the Saptanga theory section of the provided text, what are the seven constituent limbs (Prakritis) of a sovereign state? | Grounded Answer | ✅ PASS | `8.0989` | [p. 8] |
| **Q2** | In which year was the Battle of Plassey fought between the British East India Company and the Nawab of Bengal? | Refusal Message | ✅ PASS | `-11.0312` | None |
| **Q3** | How many categories of envoys (Dutas) are identified in the text according to their level of authority, and what are their designations? | Grounded Answer | ✅ PASS | `7.7048` | [p. 19] |
| **Q4** | What metaphor does Chapter 2 of the provided text use to explain how a person of steady wisdom (Sthitaprajna) withdraws their senses from sense objects? | Grounded Answer | ✅ PASS | `8.3378` | [p. 36] |
| **Q5** | Which political coalition won the 2024 Indian General Election? | Refusal Message | ✅ PASS | `-10.9855` | None |

### Detailed Outputs for Core Questions

#### [Q1] According to the Saptanga theory section of the provided text, what are the seven constituent limbs (Prakritis) of a sovereign state?

- **Status:** ✅ PASSED
- **Evaluation Detail:** Passed: Grounded answer with verified page citations and complete required terms.
- **Top Cross-Encoder Score:** `8.0989`
- **Verified Cited Pages:** [8]
- **Execution Mode:** `gemini`

**Generated Answer:**
> According to the Saptanga theory, a sovereign state is constituted by seven interdependent organic limbs (Prakritis) [p. 8]:
> 1. Swamin (The Sovereign Ruler or King) [p. 8]
> 2. Amatya (The Council of Ministers and High Officials) [p. 8]
> 3. Janapada (The Territory and its Settled Population) [p. 8]
> 4. Durga (The Fortified Capital and Defensive Strongholds) [p. 8]
> 5. Kosha (The Royal Treasury and Financial Reserves) [p. 8]
> 6. Danda or Bala (The Standing Army and Coercive Authority) [p. 8]
> 7. Mitra (The Steadfast Foreign Ally) [p. 8]

**Top Retrieved Passage (Page 8, BOOK VI, CHAPTER 1: THE SAPTANGA THEORY OF THE SEVEN LIMBS OF STATE):**
```text
BOOK VI, CHAPTER 1: THE SAPTANGA THEORY OF THE SEVEN LIMBS OF STATE According to the Saptanga theory expounded in this compendium, a sovereign state is constituted by seven interdependent organic limbs (Prakritis): 1. Swamin (The Sovereign Ruler or King) 2. Amatya (The Council of Ministers and High Officials) 3. Janapada (The Territory and its Settled Population) 4. Durga (The Fortified Capital and Defensive Strongholds) 5. Kosha (The Royal Treasury and Financial Reserves) 6. Danda or Bala (The Standing Army and Coercive Authority) 7. Mitra (The Steadfast Foreign Ally)
```

---

#### [Q2] In which year was the Battle of Plassey fought between the British East India Company and the Nawab of Bengal?

- **Status:** ✅ PASSED
- **Evaluation Detail:** Passed: Correctly refused out-of-scope question with standard refusal message.
- **Top Cross-Encoder Score:** `-11.0312`
- **Verified Cited Pages:** []
- **Execution Mode:** `refusal_gate`

**Generated Answer:**
> This information is not available in the provided text.

**Top Retrieved Passage (Page 29, 1. Overview of Ethics of Detached Action (Nishkama Karma) and Moral Duty in):**
```text
1. Overview of Ethics of Detached Action (Nishkama Karma) and Moral Duty in Governance (Reference Clause 29.1) This section of ’Compendium of Classical Statecraft & Philosophy: Arthashastra & Gita Selections’ establishes the baseline operational procedures, governance standards, and quality assurance metrics applicable to Page 29. Practitioners must ensure that routine workflows adhere to documented institutional protocols and maintain verifiable audit logs across all stages of execution. 2. Standard Procedural Guidelines (Reference Clause 29.2) During standard operations under Module 29, teams are required to conduct periodic reviews of system state, documentation completeness, and safety margins. All routine records associated with ethics of detached action (nishkama karma) and moral duty in governance shall be archived in the central repository at the conclusion of each operational cycle for longitudinal review. 3. Archival & Verification Notes (Reference Clause 29.3) No external assumptions or unverified parameters may be substituted for the explicit tables contained within this 50-page manual. Refer to the specific numbered sections of this handbook for exact quantitative thresholds, timelines, and escalation contacts.
```

---

#### [Q3] How many categories of envoys (Dutas) are identified in the text according to their level of authority, and what are their designations?

- **Status:** ✅ PASSED
- **Evaluation Detail:** Passed: Grounded answer with verified page citations and complete required terms.
- **Top Cross-Encoder Score:** `7.7048`
- **Verified Cited Pages:** [19]
- **Execution Mode:** `gemini`

**Generated Answer:**
> According to the text, there are exactly three distinct categories of envoys (Dutas) based on their level of authority [p. 19]. Their designations are:
> 1. Nisrishtarthah [p. 19]
> 2. Parimitarthah [p. 19]
> 3. Shasanaharah [p. 19]

**Top Retrieved Passage (Page 19, BOOK I, CHAPTER 16: CLASSIFICATION AND AUTHORITY OF ENVOYS (DUTAS)):**
```text
BOOK I, CHAPTER 16: CLASSIFICATION AND AUTHORITY OF ENVOYS (DUTAS) In diplomatic missions, envoys (Dutas) are classified into exactly three distinct categories based on their level of authority: 1. Nisrishtarthah: A Plenipotentiary Ambassador endowed with full ministerial qualifications and discretionary authority to negotiate treaties. 2. Parimitarthah: An Envoy Extraordinary entrusted with a strictly limited, predefined mission. 3. Shasanaharah: A Royal Messenger or Bearer of Dispatches authorized only to deliver written decrees.
```

---

#### [Q4] What metaphor does Chapter 2 of the provided text use to explain how a person of steady wisdom (Sthitaprajna) withdraws their senses from sense objects?

- **Status:** ✅ PASSED
- **Evaluation Detail:** Passed: Grounded answer with verified page citations and complete required terms.
- **Top Cross-Encoder Score:** `8.3378`
- **Verified Cited Pages:** [36]
- **Execution Mode:** `gemini`

**Generated Answer:**
> In Chapter 2, a person of steady wisdom (Sthitaprajna) who completely withdraws their senses from external sense objects is explicitly compared to a tortoise (kurma) drawing its head and limbs entirely inside its protective shell [p. 36].

**Top Retrieved Passage (Page 36, PART II, CHAPTER 2, VERSE 58: THE METAPHOR OF STEADY WISDOM (STHITAPRAJNA)):**
```text
PART II, CHAPTER 2, VERSE 58: THE METAPHOR OF STEADY WISDOM (STHITAPRAJNA) In Chapter 2 of the philosophical dialogue, the sage of steady wisdom (Sthitaprajna) who completely withdraws their senses from external sense objects is explicitly compared to a tortoise (kurma) drawing its head and limbs entirely inside its protective shell.
```

---

#### [Q5] Which political coalition won the 2024 Indian General Election?

- **Status:** ✅ PASSED
- **Evaluation Detail:** Passed: Correctly refused out-of-scope question with standard refusal message.
- **Top Cross-Encoder Score:** `-10.9855`
- **Verified Cited Pages:** []
- **Execution Mode:** `refusal_gate`

**Generated Answer:**
> This information is not available in the provided text.

**Top Retrieved Passage (Page 46, 1. Overview of Historical Philology and Manuscript Transmission of Classical):**
```text
1. Overview of Historical Philology and Manuscript Transmission of Classical Sanskrit Treaties (Reference Clause 46.1) This section of ’Compendium of Classical Statecraft & Philosophy: Arthashastra & Gita Selections’ establishes the baseline operational procedures, governance standards, and quality assurance metrics applicable to Page 46. Practitioners must ensure that routine workflows adhere to documented institutional protocols and maintain verifiable audit logs across all stages of execution. 2. Standard Procedural Guidelines (Reference Clause 46.2) During standard operations under Module 46, teams are required to conduct periodic reviews of system state, documentation completeness, and safety margins. All routine records associated with historical philology and manuscript transmission of classical sanskrit treaties shall be archived in the central repository at the conclusion of each operational cycle for longitudinal review. 3. Archival & Verification Notes (Reference Clause 46.3) No external assumptions or unverified parameters may be substituted for the explicit tables contained within this 50-page manual. Refer to the specific numbered sections of this handbook for exact quantitative thresholds, timelines, and escalation contacts.
```

---

## 3. Extended Benchmark (10 Additional Questions)

| ID | Type | Question | Status | Top Score |
| :--- | :--- | :--- | :--- | :--- |
| **EQ1** | `in_scope` | What is the primary objective of revenue auditing and forty ways of embezzlement discussed in the text? | ❌ FAIL | `2.2551` |
| **EQ2** | `in_scope` | What is the sixfold royal strategy (Shadgunya) in foreign policy referenced in Mandala theory? | ❌ FAIL | `8.2736` |
| **EQ3** | `in_scope` | How does the text define the ethics of detached action (Nishkama Karma) in state governance? | ❌ FAIL | `6.6398` |
| **EQ4** | `in_scope` | What standard protocols are outlined for witness examination and civil contracts? | ✅ PASS | `6.9206` |
| **EQ5** | `in_scope` | What role does the Swamin or Sovereign play in Book VI, Chapter 1 of the Arthashastra? | ❌ FAIL | `3.2773` |
| **EQ6** | `out_of_scope` | What were the key economic reforms introduced during the 1991 balance of payments crisis in India? | ✅ PASS | `-11.1342` |
| **EQ7** | `out_of_scope` | Who was elected as the Prime Minister of the United Kingdom in July 2024? | ✅ PASS | `-10.9547` |
| **EQ8** | `out_of_scope` | Which Mughal Emperor commissioned the construction of the Taj Mahal in Agra? | ✅ PASS | `-11.0581` |
| **EQ9** | `out_of_scope` | What were the primary boundary divisions established under the 1947 Indian Independence Act? | ✅ PASS | `-11.0185` |
| **EQ10** | `out_of_scope` | How does Shor's algorithm threaten 2048-bit RSA encryption keys on quantum hardware? | ✅ PASS | `-11.2793` |

## 4. Retrieval Performance: Hit@K

Hit@K measures the proportion of in-scope questions where the ground truth page appears in the top-K retrieved chunks:

| Metric | Accuracy | Status |
| :--- | :--- | :--- |
| **Hit@1** | **100.0%** | ✅ Optimal |
| **Hit@3** | **100.0%** | ✅ Optimal |
| **Hit@6** | **100.0%** | ✅ Optimal |

## 5. Out-of-Scope Relevance Threshold Calibration

To calibrate the hallucination and refusal guard, a labeled balanced benchmark of 8 in-scope questions and 8 out-of-scope questions was evaluated using cross-encoder rerank scores:

| # | Query | Category | Top Rerank Score | Result |
| :--- | :--- | :--- | :--- | :--- |
| 1 | According to the Saptanga theory, what are the seven limbs of state? | `In-Scope` | `9.3277` | Passed Gate |
| 2 | How many categories of envoys (Dutas) are identified and what are their ranks? | `In-Scope` | `7.1776` | Passed Gate |
| 3 | What metaphor explains how a person of steady wisdom (Sthitaprajna) withdraws senses? | `In-Scope` | `8.4446` | Passed Gate |
| 4 | What are the procedures for fiscal administration and forty ways of embezzlement? | `In-Scope` | `5.2078` | Passed Gate |
| 5 | Explain the Mandala theory of foreign policy and the sixfold royal strategy. | `In-Scope` | `8.8869` | Passed Gate |
| 6 | What constitutes the ethics of detached action (Nishkama Karma) in governance? | `In-Scope` | `7.7623` | Passed Gate |
| 7 | What guidelines govern judicial procedure and witness examination protocols? | `In-Scope` | `7.1322` | Passed Gate |
| 8 | What is the description of Nisrishtartha plenipotentiary ambassador in diplomacy? | `In-Scope` | `6.0679` | Passed Gate |
| 9 | In which year was the Battle of Plassey fought between Robert Clive and Siraj ud-Daulah? | `Out-of-Scope` | `-11.0521` | Refusal Triggered |
| 10 | Which political party or coalition won the 2024 Indian General Election? | `Out-of-Scope` | `-10.9985` | Refusal Triggered |
| 11 | What were the major resolutions of the 1942 Quit India Movement? | `Out-of-Scope` | `-11.1797` | Refusal Triggered |
| 12 | Who was appointed the CEO of Google in August 2015? | `Out-of-Scope` | `-11.1808` | Refusal Triggered |
| 13 | How does backpropagation calculate weight gradients in deep convolutional neural networks? | `Out-of-Scope` | `-11.3577` | Refusal Triggered |
| 14 | What were the terms of the Treaty of Versailles signed in 1919? | `Out-of-Scope` | `-10.5655` | Refusal Triggered |
| 15 | What was the result of the ICC Men's Cricket World Cup final in 2023? | `Out-of-Scope` | `-10.9886` | Refusal Triggered |
| 16 | What is the capital city of Australia and what is its population? | `Out-of-Scope` | `-10.5676` | Refusal Triggered |

### Calibration Findings

- **In-Scope Score Range:** `[5.2078, 9.3277]` (Mean: `7.5009`)
- **Out-of-Scope Score Range:** `[-11.3577, -10.5655]` (Mean: `-10.9863`)
- **Selected Refusal Threshold:** `-2.0` (Recommended midpoint: `-2.7`)
- **Safety Margin:** There is an extensive score margin of ~15.8 points separating in-scope and out-of-scope queries, providing zero false rejections and zero hallucination leakages.
