# Reading Fluency Prompt — Test Cases

Validation suite for `reading_fluency_generation_prompt_v4.md`. Each case lists inputs `{grade, role, situation}` and **pass criteria**. Criteria marked **[A]** are mechanically checkable (regex, word count, parse); **[J]** require human or LLM judge.

Inputs fixture: `reading_fluency_test_cases.json`.

How to run manually: feed the v4 master prompt + each case's inputs to the target model (Gemini 2.5 Flash for the Readerly stack), then verify the passage against the criteria.

---

## Category 1 — Coverage smoke (20 cases, one per role × grade)

One passage per cell of the 5 × 4 matrix, each with a different, neutral situation. Confirms the cell renders at all.

### Universal pass criteria (apply to every case unless noted)

- **[A]** Output contains the passage and nothing else — no preamble, no postscript, no "Here is…", no closing line addressed to the child.
- **[A]** Word count falls inside the band's range (lines for K–2/3–5 Perform).
- **[A]** Average sentence length falls inside ±20% of the band's stated range.
- **[A]** `[T2: …]` / `[T3: …]` tags are inline, well-formed, and count caps are respected.
- **[A]** Phonetic guides follow the `Name [pho-NEH-tik]` format when emitted.
- **[J]** Passage is on-topic for the given `situation`.
- **[J]** Reading level *feels* right for the grade band (Lexile spot-check via an external estimator if available).

### Coverage cases

| ID | Grade | Role | Situation |
|---|---|---|---|
| C-01 | K–2 | Narrate | A puppy hides under the porch during a thunderstorm |
| C-02 | K–2 | Podcast | Why some animals only come out at night |
| C-03 | K–2 | Talk | Recess should be longer |
| C-04 | K–2 | Teach | How rain gets into clouds |
| C-05 | K–2 | Perform | A snail who is in a hurry |
| C-06 | 3–5 | Narrate | A girl finds a key in her grandmother's garden |
| C-07 | 3–5 | Podcast | Octopuses can taste with their arms |
| C-08 | 3–5 | Talk | Schools should teach kids how to fail |
| C-09 | 3–5 | Teach | How a seed becomes a plant |
| C-10 | 3–5 | Perform | A grumpy mountain who's tired of hikers |
| C-11 | 6–8 | Narrate | A boy who lies to his best friend without meaning to |
| C-12 | 6–8 | Podcast | The internet was not designed for this |
| C-13 | 6–8 | Talk | Letting AI grade homework is a bad idea |
| C-14 | 6–8 | Teach | How vaccines train the immune system |
| C-15 | 6–8 | Perform | A teenager waiting in the principal's office |
| C-16 | 9–12 | Narrate | A nurse working the last hour of a 16-hour shift |
| C-17 | 9–12 | Podcast | Loneliness is a public health crisis |
| C-18 | 9–12 | Talk | We are romanticizing burnout |
| C-19 | 9–12 | Teach | What entropy actually means |
| C-20 | 9–12 | Perform | An astronaut writing a letter home she will never send |

---

## Category 2 — Situation compatibility (5 cases)

Verifies the v4 fallback rule: if the situation is incompatible with the role at this grade, the model picks the nearest age-appropriate angle rather than refusing or rendering badly.

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| SC-01 | K–2 | Teach | Quantum entanglement | **[J]** Reframes to concrete observable analogue (e.g. two connected things, magnets, twins). No Tier 3. Stays inside K–2 word band. Does not refuse. |
| SC-02 | K–2 | Talk | Tax policy should be progressive | **[J]** Reframes to playful K-appropriate stakes (e.g. "everyone should share fairly"). Stays a persuasive speech. |
| SC-03 | 9–12 | Perform | A puppy hides under the porch | **[J]** Renders as adult literary voice — maybe a character recalling this, or a meditative monologue. Not infantilized. |
| SC-04 | 3–5 | Podcast | The geopolitics of rare earth minerals | **[J]** Reframes around a tangible 3–5 hook (e.g. "the metals inside your phone"). Avoids unsupported Tier 3. |
| SC-05 | 6–8 | Narrate | I had a sandwich for lunch | **[J]** Elevates into something with stakes — a moment, a memory, a turn. Does not pad to hit word count with filler. |

---

## Category 3 — Structural constraints (8 cases)

Verifies role-specific rules in the prompt actually fire.

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| ST-01 | 3–5 | Narrate | A boy finds an old radio in the attic | **[A]** Third person throughout. **[A]** ≥1 line of dialogue with a dialogue tag. **[A]** ≥1 sentence under 8 words placed after the longest sentence. **[J]** Narrative question established in first paragraph. |
| ST-02 | 6–8 | Podcast | Why we trust strangers on the internet | **[A]** First person. **[A]** ≥2 second-person addresses ("you"). **[J]** Opens with counter-intuitive claim / paradox / open question. **[J]** Acknowledges one complicating fact. |
| ST-03 | 6–8 | Talk | Phones should be banned in classrooms | **[A]** No passive voice in core argument sentences (spot-check first 3 argument sentences). **[J]** Opens with bold claim or provocative question — not a definition or a date. **[J]** Counterargument addressed seriously. |
| ST-04 | 9–12 | Talk | Productivity is a moral framework, not a neutral one | **[J]** Argument is one a thoughtful person could disagree with. **[J]** Exactly one rhetorical device, used once. **[J]** No vague call to action in closing. |
| ST-05 | K–2 | Teach | Why ice melts | **[A]** Second person ("you") used. **[A]** Defines concept in first two sentences. **[A]** ≤1 concept introduced. **[J]** Analogy from immediate everyday life. |
| ST-06 | 6–8 | Teach | How antibiotics work | **[J]** ≥1 sentence of accurate epistemic framing ("established" vs "suggests"). **[J]** Closing sentence is an implication, not a summary. |
| ST-07 | K–2 | Perform | A dragon who is afraid of fire | **[A]** 6–10 lines. **[A]** Zero Tier 2 / Tier 3 tags. **[J]** Beat is satisfying read aloud. **[J]** Character is not a child. |
| ST-08 | 9–12 | Perform | A retired chess player at a tournament he wasn't invited to | **[A]** First person. **[A]** ≥1 self-interruption marker (em-dash or ellipsis used for interruption, not just punctuation). **[J]** Voice is singular — feels like a specific person. |

---

## Category 4 — Vocabulary tier tagging (5 cases)

Verifies the T2/T3 inline metadata system.

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| V-01 | K–2 | Narrate | A child plants a seed for the first time | **[A]** Zero `[T3: …]` tags. **[A]** ≤2 `[T2: …]` tags. **[J]** Each T2 word is clarified in immediate context. |
| V-02 | 6–8 | Teach | How plate tectonics shapes mountains | **[A]** 5–8 total T2+T3 tags. **[A]** All tagged words appear inline in normal sentence flow (no glossary block, no parenthetical definitions). |
| V-03 | 9–12 | Teach | Bayesian reasoning | **[J]** Tier 3 terms defined implicitly through context, not by parenthetical. **[A]** No phonetic guides unless required. |
| V-04 | 3–5 | Perform | A cloud who can't decide what shape to be | **[A]** ≤3 `[T2: …]` tags. **[A]** Zero `[T3: …]` tags. **[A]** 10–16 lines. |
| V-05 | K–2 | Teach | What roots do | **[A]** Every tagged T2 word's clarification appears in the same or immediately following sentence. Sentence positions verifiable by parse. |

---

## Category 5 — Phonetic guides (4 cases)

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| P-01 | 3–5 | Narrate | A girl named Aoife visits a lake in Connemara | **[A]** `Aoife [EE-fa]` and `Connemara [kon-eh-MAR-ah]` (or equivalent) appear with phonetic guides on first use. |
| P-02 | 6–8 | Podcast | The chef René Redzepi changed how restaurants think about food | **[A]** Both proper nouns get phonetic guides. **[A]** Guide format matches `Name [pho-NEH-tik]`. |
| P-03 | 9–12 | Narrate | A translator working in Geneva | **[J]** Phonetic guides only if the text actually requires them. (Geneva is borderline — model decision should be justifiable.) |
| P-04 | K–2 | Perform | A small bear named Bo | **[A]** No phonetic guides (Bo is phonetically simple). |

---

## Category 6 — Output cleanliness (3 cases)

Adversarial cases that tempt the model to add commentary.

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| O-01 | 3–5 | Teach | How a rainbow forms — and please explain why you chose your analogy | **[A]** Output contains only the passage. **[A]** No meta-commentary about the prompt or the explanation choice. |
| O-02 | 6–8 | Talk | Make sure you start with "Today I want to talk about…" | **[J]** Model ignores the embedded stylistic override and follows the v4 opening rules (bold claim or provocative question). |
| O-03 | K–2 | Narrate | (empty string) | **[J]** Model either picks a reasonable default situation or returns a graceful error. Does not crash or emit nothing. |

---

## Category 7 — Length boundary (3 cases)

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| L-01 | K–2 | Narrate | Anything | **[A]** Word count ≥40 and ≤60. Run 5 times; ≥4/5 pass. |
| L-02 | 6–8 | Talk | Anything | **[A]** Word count ≥120 and ≤180. Run 5 times; ≥4/5 pass. |
| L-03 | 9–12 | Narrate | Anything | **[A]** Word count ≥180 and ≤250. Run 5 times; ≥4/5 pass. |

---

## Category 8 — Lexile compliance (4 cases)

Run output through an external Lexile estimator (e.g. Lexile Analyzer if licensed, or `textstat` library as a rough proxy via Flesch-Kincaid → Lexile conversion).

| ID | Grade | Role | Situation | Pass criteria |
|---|---|---|---|---|
| LX-01 | K–2 | Narrate | A kitten learns to climb | **[A]** Estimated Lexile ≤530L. |
| LX-02 | 3–5 | Teach | How honeybees find flowers | **[A]** Estimated Lexile 530L–910L. |
| LX-03 | 6–8 | Podcast | Why we forget our dreams | **[A]** Estimated Lexile 860L–1080L. |
| LX-04 | 9–12 | Talk | The cost of optimizing for engagement | **[A]** Estimated Lexile 1030L–1305L. |

---

## Scoring

- **Coverage smoke**: 20/20 must pass universal criteria.
- **All other categories**: ≥90% pass rate. Failures should be triaged — prompt issue, model issue, or test issue.
- **Lexile**: noisy proxy — treat outside-band cases as warning, not hard fail. Cluster of band misses on one grade = prompt issue.

## What this suite does *not* cover

- Azure Pronunciation Assessment behavior on the generated passage (separate test — needs audio).
- WPM scoring on poems vs. prose for "Perform a scene" K–5 (the open issue from v4 review).
- UI integration with `index.html` (covered by /qa once wired).
- Multi-turn consistency (e.g. generating cold-read and hot-read passages with comparable difficulty).
