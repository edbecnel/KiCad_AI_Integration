# What is the KiCad AI Integration Project?

[Home](README.md) · [Project Index](PROJECT_INDEX.md)

> **Status:** Approved
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration — project introduction
> **Last Reviewed:** 2026-07-29
> **Review Frequency:** Annual
> **Authoritative:** Yes

The KiCad AI Integration Project began as a relatively simple idea:

> *Allow KiCad to send a schematic to a Large Language Model (LLM) such as Claude Sonnet for engineering review.*

As development progressed, it became clear that simply sending a netlist or schematic image to an AI would produce only superficial results. A language model has no inherent understanding of electronics—it only understands the information provided to it.

This realization fundamentally changed the direction of the project.

Today, the project is no longer simply an "AI chat window for KiCad." It has evolved into the design of an **AI-assisted Electrical Engineering reasoning platform** that uses KiCad as its primary engineering environment.

---

## The Core Philosophy

The project's guiding philosophy is:

> **An AI should not merely describe a circuit—it should reason about it like an experienced electrical engineer.**

To accomplish this, the system must first construct an internal engineering understanding of the design before asking an LLM to perform higher-level reasoning.

Rather than treating a schematic as a collection of symbols and wires, the system progressively transforms it into structured engineering knowledge.

---

## Beyond Circuit Recognition

Most AI-assisted design tools stop after identifying components and reading their values.

This project goes much further.

The system is designed to infer engineering intent by determining:

- the functional role of every component
- how energy flows through the circuit
- which portions of the design form functional subsystems
- what operating states the circuit can enter
- which electrical principles explain its behavior
- what information is known
- what information is inferred
- what information remains unknown

This allows the AI to explain **why** a circuit behaves the way it does—not merely **what** components it contains.

---

## The Engineering Knowledge Model

At the center of the architecture is a structured [Engineering Knowledge Model (EKM)](docs/Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md).

The EKM serves as the authoritative engineering representation of the project by separating:

- facts extracted directly from KiCad
- engineering inferences
- supporting evidence
- confidence levels
- simulation results
- user-supplied knowledge
- unresolved questions

This separation ensures that the AI never confuses verified information with inferred conclusions.

**Ratified by:** [ADR-0005: EKM Foundation](docs/Architecture/ADRs/ADR-0005-EKM-Foundation.md)

---

## The AI Engineering Reasoning Framework

Rather than sending raw schematic data in a single ad-hoc prompt, the project introduces an [AI Engineering Reasoning Framework (AERF)](docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md).

**Before each AERF stage**, the system deterministically:

- collects KiCad facts into `ProjectContext`
- classifies circuit family (heuristics, user hint, or prior EKM)
- loads the matching Circuit Family KB excerpt for that stage
- injects prior stage JSON and EKM sections into the prompt

**Each AERF stage (0–7)** is then one LLM call with a scoped engineering question, structured output schema, and [Engineering Reasoning Methodology](docs/Engineering_Knowledge/Engineering_Reasoning_Methodology.md) rules (classification, unknowns, confidence, evidence chains).

The LLM remains the inference engine. AERF provides **process, knowledge injection, epistemic discipline, accumulation across stages, and human approval gates** — not a separate non-AI engineering brain.

See [How AERF Works](docs/User_Guides/How_AERF_Works.md) for a newcomer-oriented explanation and [AERF Stage Index](docs/Engineering_Knowledge/AERF_Stage_Index.md) for canonical stage definitions.

---

## Human-Like Engineering Reasoning

One of the primary goals is to emulate the workflow of an experienced engineer.

When presented with a new schematic, an engineer typically asks questions such as:

- What kind of circuit is this?
- Which components form each functional block?
- Where does energy flow?
- Which components control operation?
- What assumptions am I making?
- What evidence supports those assumptions?
- What information is missing?
- What additional measurements or simulations would increase confidence?

The project aims to teach the AI to follow this same disciplined reasoning process. See [Engineering Reasoning Methodology](docs/Engineering_Knowledge/Engineering_Reasoning_Methodology.md) for how each AERF stage applies this process.

---

## Not Limited to One Circuit Family

Although early development focuses on the John Bedini SSG and related blocking oscillators, the architecture is intentionally designed to be extensible.

Future engineering knowledge modules may support:

- switching power supplies
- linear regulators
- audio amplifiers
- RF circuits
- motor controllers
- battery chargers
- digital logic
- embedded systems
- mixed-signal electronics
- entirely new circuit families

Each new domain contributes engineering knowledge without requiring changes to the core reasoning architecture. See the [Circuit Families](docs/Engineering_Knowledge/Circuit_Families/README.md) registry for current and planned families.

---

## Engineering Before Artificial Intelligence

Perhaps the most important evolution of the project is the recognition that this is **not primarily an AI project.**

It is an **engineering knowledge project** that happens to use modern AI as one of its reasoning tools.

The true intellectual property of the project is not the choice of LLM provider, prompt format, or user interface.

It is the growing body of structured engineering knowledge, deterministic reasoning processes, inference methods, evidence models, and architectural frameworks that enable an AI to think more like an electrical engineer.

Large Language Models become interchangeable reasoning engines operating on top of this engineering foundation.

---

## Platform, Frameworks, and Host Integrations

The repository implements an **AI-assisted Electrical Engineering Reasoning Platform** with three architectural layers:

| Layer | Description |
|-------|-------------|
| **Platform** | Product vision and cross-host contracts |
| **Frameworks** | EKM, AERF, EIE, Prompt Architecture, AI Provider Layer, and related components |
| **Host Integrations** | Environment-specific adapters — KiCad AI Integration is the first |

AERF defines *what* to reason about (stages, methodology, circuit-family knowledge). The Engineering Inference Engine (EIE) defines *how* reasoning runs at runtime. KiCad provides schematic connectivity, context collection, and the initial user interface.

See [Platform Architecture](docs/Architecture/Platform_Architecture.md) for the authoritative platform overview.

---

## Long-Term Vision

The long-term vision is to transform KiCad from a schematic capture application into an intelligent engineering assistant capable of collaborating with engineers throughout the entire design lifecycle.

Rather than simply answering questions, the system should become an active engineering partner capable of:

- understanding complex designs
- explaining circuit operation
- identifying design weaknesses
- proposing improvements
- highlighting uncertainty
- recommending simulations
- documenting engineering rationale
- preserving engineering knowledge
- accelerating learning for students
- assisting experienced engineers with increasingly sophisticated analysis

The ultimate objective is not to replace engineers, but to augment their expertise by combining deterministic engineering knowledge with modern AI reasoning into a transparent, explainable, and extensible engineering platform.

---

## Related Documents

| Topic | Document |
|-------|----------|
| Platform architecture | [Platform Architecture](docs/Architecture/Platform_Architecture.md) |
| Governance scope and goals | [Project Charter](PROJECT_CHARTER.md) |
| Current capabilities | [Feature Overview](docs/User_Guides/Feature_Overview.md) |
| EKM architecture | [ADP-001: Engineering Knowledge Model Foundation](docs/Architecture/ADP-001-Engineering-Knowledge-Model-Foundation.md) |
| AERF architecture | [ADP-008: AI Engineering Reasoning Framework](docs/Architecture/ADP-008-AI-Engineering-Reasoning-Framework.md) |
| AERF stage definitions | [AERF Stage Index](docs/Engineering_Knowledge/AERF_Stage_Index.md) |
| Engineering reasoning process | [Engineering Reasoning Methodology](docs/Engineering_Knowledge/Engineering_Reasoning_Methodology.md) |
| Circuit family registry | [Circuit Families](docs/Engineering_Knowledge/Circuit_Families/README.md) |
| Full documentation map | [Project Index](PROJECT_INDEX.md) |
