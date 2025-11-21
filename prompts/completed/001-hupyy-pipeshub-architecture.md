<objective>
Create comprehensive technical architecture documentation for the Hupyy (SMT verification service) integration with PipesHub, strictly following the concepts in the source document.

The output should be a detailed architecture document using Mermaid diagrams as the primary visualization tool. Use code only when absolutely necessary to illustrate specific implementations that cannot be effectively shown with diagrams.

This documentation will serve as the technical blueprint for implementing verification-guided search where SMT verification acts as a truth filter to continuously improve retrieval quality.
</objective>

<context>
PipesHub is an open-source enterprise RAG platform with:
- Qdrant (vector database) for semantic search
- ArangoDB (knowledge graph) for PageRank-based document scoring
- MongoDB for user data
- Apache Kafka for event-driven messaging
- Python/Node.js microservices

Hupyy provides formal SMT verification capabilities using solvers like Z3 and cvc5, returning rich verification metadata including SAT/UNSAT/UNKNOWN verdicts, confidence scores, proofs, and failure mode classifications.

The integration creates a three-stage pipeline: Semantic Retrieval → Formal Verification → Feedback Integration, enabling a reinforcement loop where successfully verified chunks rank higher in future searches.

Source document: @/Users/alexanderfedin/Projects/hapyy/pipeshub-ai-orig/docs/compass_artifact_wf-01877f67-7032-4e45-a5b8-1e2a0fb221a3_text_markdown.md
</context>

<requirements>
Thoroughly analyze the source document and create architecture documentation that includes:

1. **System Architecture Overview**
   - High-level system diagram showing all components and their relationships
   - Microservice integration pattern for the new Verification Service
   - Data flow between PipesHub Core, Verification Orchestrator, and Hupyy

2. **Data Flow Diagrams**
   - Query processing pipeline from user query to verified results
   - Verification request/response flow
   - Feedback loop data flow (Fast/Medium/Slow tiers)

3. **Component Interaction Diagrams**
   - Sequence diagram for chunk verification process
   - Event-driven integration via Kafka
   - PageRank calculation with verification weights

4. **Metadata Architecture**
   - Entity relationship diagrams for verification metadata
   - Qdrant payload structure
   - ArangoDB document properties

5. **Ranking Algorithm Visualization**
   - Flow diagram showing score computation with verification signals
   - Failure mode classification decision tree
   - Three-tier feedback architecture

6. **Implementation Phases**
   - Timeline diagrams showing phased rollout
   - Cold start handling strategy
   - Expected improvement curves

7. **Monitoring and Health**
   - Dashboard metrics architecture
   - Alert system flow

Use Mermaid diagram types appropriately:
- `flowchart` for data flows and processes
- `sequenceDiagram` for component interactions
- `erDiagram` for data structures
- `gantt` for timelines
- `stateDiagram` for state machines
- `classDiagram` for API structures
</requirements>

<constraints>
- Prefer Mermaid diagrams over code blocks
- Only use code when illustrating specific formulas, algorithms, or API signatures that cannot be effectively shown in diagrams
- All diagrams must be valid Mermaid syntax
- Each diagram should have a clear title and be accompanied by explanatory text
- Diagrams should be readable and not overly complex (break into multiple diagrams if needed)
- Follow the exact terminology and concepts from the source document
- Include all key metrics, thresholds, and parameters mentioned in the source
</constraints>

<output>
Save the architecture documentation as a single comprehensive markdown file:
`./docs/hupyy-pipeshub-integration-architecture.md`

Structure the document with clear sections, each containing:
1. Section title
2. Brief explanation
3. Mermaid diagram(s)
4. Key details and parameters

Include a table of contents at the beginning.
</output>

<verification>
Before completing, verify:
- All major concepts from the source document are covered
- Each diagram renders correctly (valid Mermaid syntax)
- The document tells a complete story from high-level architecture to implementation details
- Key metrics and thresholds from the source are included
- The feedback loop mechanisms are clearly illustrated
- Failure modes and their handling are documented
</verification>

<success_criteria>
- Comprehensive coverage of the source document's architecture concepts
- Minimum 10 Mermaid diagrams covering different aspects
- Clear visual representation of the three-stage pipeline
- Actionable technical detail for implementation
- Professional documentation quality suitable for engineering team review
</success_criteria>
