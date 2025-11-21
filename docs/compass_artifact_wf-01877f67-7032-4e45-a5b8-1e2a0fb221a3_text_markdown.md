# Verification-Guided Search Architecture: PipesHub + Hupyy Integration

PipesHub's natural language search capabilities combined with Hupyy's formal verification can create a powerful feedback loop where **SMT verification acts as a truth filter**, continuously improving retrieval quality. This architecture bridges probabilistic semantic search with deterministic formal verification.

## Core Architecture: How the Feedback Loop Works

The system operates as a **three-stage pipeline with continuous learning**:

**Stage 1: Semantic Retrieval** (PipesHub does naturally)
PipesHub retrieves document chunks using its hybrid approach combining vector similarity search (Qdrant) with knowledge graph traversal (ArangoDB PageRank). Each chunk includes source citations, metadata, and initial relevance scores.

**Stage 2: Formal Verification** (Hupyy's role)
Hupyy extracts formal SMT specifications from retrieved chunks, evaluates them with solvers (Z3, cvc5), and returns rich verification results including SAT/UNSAT verdicts, proofs, unsatisfiable cores, confidence metrics, and failure mode classifications.

**Stage 3: Feedback Integration** (The innovation)
Verification results flow back to PipesHub as structured quality signals, updating chunk metadata in Qdrant and document properties in the ArangoDB knowledge graph. This creates a **reinforcement loop** where successfully verified chunks rank higher in future searches, while failed verifications help filter noise.

### The Key Insight in Practice

Traditional RAG systems rely purely on semantic similarity—a chunk that *sounds* relevant gets high scores. With verification feedback, **only chunks containing actually valid, verifiable formal specifications** maintain high rankings. This dramatically improves precision for technical queries requiring formal correctness.

## A. PipesHub's Natural Language Search + Citation Capabilities

### Architecture Overview

PipesHub is an **open-source enterprise RAG platform** with sophisticated multi-database architecture perfectly suited for verification integration:

**Core Components:**
- **Qdrant** (vector database): HNSW algorithm for fast semantic search with extensible JSON payloads per chunk
- **ArangoDB** (knowledge graph): PageRank-based document importance scoring with property-rich nodes/edges
- **MongoDB**: User data and configuration
- **Apache Kafka**: Event-driven messaging for real-time feedback
- **Microservices**: Python indexing/query services, Node.js API layer

### How Citations Work

PipesHub tracks provenance throughout the pipeline. Document ingestion preserves source metadata (file, author, timestamp, application). Chunking maintains parent document references and position within document. Retrieval tracks which chunks contributed to each answer. Response generation includes explicit citations with links to original sources.

**Citation metadata includes:**
- Source document reference with direct access links
- Author and timestamp information  
- Chunk location within larger document
- Knowledge graph context showing related entities

### Ranking and Scoring System

**Two-stage hybrid retrieval:**

**Vector similarity** (Qdrant) performs fast approximate nearest neighbor search to retrieve candidate chunks based on semantic similarity. Then **PageRank reranking** (ArangoDB) applies graph-based importance scoring to prioritize documents with more citations and stronger relationships.

This dual approach provides both **semantic relevance** (vector search) and **structural authority** (PageRank)—ideal for integrating a third signal: **formal verification quality**.

### Quality Signal Tracking Capabilities

PipesHub's architecture inherently supports verification feedback through multiple mechanisms:

**Chunk-level metadata** (Qdrant payloads) can store verification scores, verification status, formal specification quality, verification counts, and success rates as extensible JSON fields.

**Document-level properties** (ArangoDB nodes) can track average verification scores, verification levels, reliability scores, and formal property counts as node properties that influence PageRank calculations.

**Extensibility advantages:**
- Open-source: full code access for customization
- Flexible metadata: arbitrary JSON in Qdrant, arbitrary properties in ArangoDB
- Event-driven: Kafka enables real-time feedback processing
- Microservices: easy to add verification service without disrupting core system

## B. Verification Results as Feedback Signals

### Rich SMT Verification Metadata

Modern SMT solvers provide far more than binary SAT/UNSAT verdicts. Hupyy can return:

**Primary signals:**
- **Verdict**: SAT (satisfiable), UNSAT (unsatisfiable), UNKNOWN (timeout/incomplete)
- **Confidence score** (0-1): Computed from verdict quality, solve time, proof characteristics, theory decidability
- **Model** (SAT case): Satisfying assignments showing how specification can be satisfied
- **Proof** (UNSAT case): Natural deduction proof tree in formats like LFSC or Alethe
- **Unsatisfiable core**: Minimal subset of assertions causing contradiction
- **Solve time**: Performance metric indicating specification complexity

**Secondary signals:**
- **Statistics**: Conflicts, propagations, lemmas generated, theory mixing
- **Proof complexity**: Size (node count), depth, instantiation count
- **Failure mode classification**: Invalid/ambiguous/incomplete/timeout/theory-incomplete
- **Theory information**: Which logics used (linear arithmetic, bit-vectors, arrays, etc.)

### How to Use Each Signal Type

**SAT results → Boost rankings significantly**. Chunk contains valid, satisfiable specification. Model provides concrete example. Apply ranking multiplier of 1.5-2.0× base score. Track model characteristics like constrained vs under-constrained variables.

**UNSAT results → Context-dependent handling**. With small core (2-5 assertions), likely invalid specification with direct contradiction—penalize heavily (0.3× multiplier) or filter completely. Use for debugging queries like "show me conflicting specifications". With large core (10+ assertions), indicates complex interaction or sophisticated property—moderate penalty (0.7× multiplier), useful for "edge cases" or "complex constraints" queries.

**UNKNOWN results → Careful interpretation**. Timeout indicates specification likely valid but complex—small penalty (0.85× multiplier), consider for "challenging properties" searches. Theory incomplete (quantifiers, non-linear arithmetic) means specification in undecidable fragment—neutral or small boost for "advanced" queries, flag for manual expert review.

### Distinguishing Failure Modes

Research on verification-guided systems identifies five primary failure modes:

**Invalid Specification** (Direct Contradiction): UNSAT with 2-3 assertions in core, shallow proof (1-2 steps), fast solve time. Example: `x > 5 ∧ x < 3`. Strong negative feedback signal (-0.7). Message: "Chunk contains contradictory specification".

**Ambiguous Specification** (Multiple Models): SAT with different models across solver runs, many "else" clauses. Detection via multiple runs with different random seeds. Moderate negative signal (-0.3). Message: "Specification under-constrained, multiple interpretations possible".

**Incomplete Specification** (Missing Constraints): SAT with >50% variables appearing only in model, not assertions. Function defined for few inputs with arbitrary "else" behavior. Small negative signal (-0.2). Message: "Specification incomplete, some behaviors unconstrained".

**Solver Timeout** (Resource Limit): UNKNOWN after timeout, high complexity metrics. Timeout cores (cvc5 feature) identify problematic assertion subsets. Small negative signal (-0.15). Message: "Complex specification, verification inconclusive".

**Theory Incompleteness** (Undecidable Fragment): UNKNOWN with theory-specific reasons like quantifiers or non-linear arithmetic. Neutral to positive signal (+0.0 to +0.1). Message: "Advanced specification in undecidable logic fragment".

### Ranking Formula with Verification

Combine multiple signals using weighted scoring:

```python
def compute_final_score(chunk):
    # Base scores from PipesHub
    semantic_sim = chunk.vector_similarity  # 0-1
    pagerank = chunk.pagerank_score  # 0-1
    
    # Verification signals from Hupyy
    verification_confidence = chunk.verification_confidence  # 0-1
    historical_success = chunk.success_rate  # 0-1
    
    # Failure mode adjustment
    failure_multiplier = {
        "verified_sat": 1.8,
        "invalid": 0.3,
        "ambiguous": 0.7,
        "incomplete": 0.8,
        "timeout": 0.85,
        "theory_incomplete": 1.0,
        "never_verified": 1.0  # Cold start: neutral
    }[chunk.failure_mode]
    
    # Weighted combination
    base_score = (0.45 * semantic_sim + 
                  0.30 * pagerank + 
                  0.15 * verification_confidence +
                  0.10 * historical_success)
    
    final_score = base_score * failure_multiplier
    
    return final_score
```

Weights: semantic similarity (45%) as primary signal for query intent matching, PageRank (30%) for document authority, verification confidence (15%) as direct quality signal, historical success (10%) for long-term patterns. These should be tuned based on domain, starting conservatively with higher semantic weight and gradually increasing verification weight as the system matures.

## C. Feedback Loops in RAG/Search Systems

### Three-Tier Feedback Architecture

Research on production RAG systems identifies optimal feedback loops at three timescales:

**Tier 1: Fast Feedback** (Real-time, per verification) with immediate latency (<100ms) updates individual chunk scores using exponential moving average. New observation weighted at 10% (α=0.1) against 90% historical score, directly updating Qdrant payloads.

**Tier 2: Medium Feedback** (Hourly/Daily batches) with 1-24 hour latency retrains reranker on accumulated successful retrievals, updates query expansion rules based on successful patterns, and adjusts precision-recall operating points using batch learning.

**Tier 3: Slow Feedback** (Weekly/Monthly retraining) with 7-30 day latency fine-tunes embedding models using contrastive learning (pulling verified chunks closer to queries, pushing failed verifications away), rebuilds ArangoDB PageRank with updated verification weights, and conducts comprehensive A/B testing of system changes.

### Learning from Analogous Systems

**Click-through rate (CTR) models** from search engines provide direct analogs. Position #1 gets 39.8% CTR, analogous to verification success being the "click". Top 3 capture 68.7% of clicks, so ensure verified chunks rank in top positions. CTR is not a direct ranking factor but validation metric—similarly, verification supplements rather than replaces semantic relevance.

**RLHF for retrieval** shows measurable improvements: RAG-Reward framework achieved 6-8% improvement using preference pairs, while Pistis-RAG demonstrated online learning with human feedback simulation. For PipesHub-Hupyy, the SMT solver acts as a perfect "human labeler" providing deterministic feedback.

**Relevance feedback** (classical IR technique still effective) like the Rocchio algorithm moves queries toward relevant documents. Modern adaptation ReFit shows 2-3% Recall@100 improvement with single iteration. Application: adjust query embeddings toward successfully verified chunks.

### Avoiding Feedback Loop Pitfalls

**Query Drift Prevention**: Constrain modification magnitude with `||Q_new - Q_orig|| < 0.3`. Use interpolation `Q_final = 0.7*Q_orig + 0.3*Q_updated`. Monitor semantic similarity between original and updated queries. Implement rollback if downstream performance drops below 95% baseline.

**Overfitting to Verifier Quirks**: Use multiple solvers (Z3, cvc5) requiring consensus. Maintain holdout set never used for feedback. Regular evaluation on unseen queries. L2 regularization in score updates.

**Confirmation Bias**: ε-greedy exploration with 10-15% probability of random/low-ranked retrieval. Stratified sampling ensures diverse document types get verified. Track verification coverage (% of document types with ≥5 verifications). Boost under-explored regions temporarily.

**Cold Start Problem**: Three-phase approach. Phase 1 (Days 1-7) uses pseudo-relevance feedback with conservative 90% semantic, 10% pseudo-feedback weight. Phase 2 (Days 8-30) applies hybrid approach gradually increasing verification weight from 10% to 30%. Phase 3 (Day 30+) implements full feedback integration with verification at 25% weight.

**Sparse Feedback Handling**: When verification rate is low (<5%), use uncertainty sampling to prioritize high-uncertainty retrievals. Apply transfer learning propagating signals from verified to similar unverified chunks. Enable PageRank propagation where verification quality flows through knowledge graph relationships.

## D. Truth Filtering and Verification-Guided Search

### How Verification Acts as Truth Filter

**CEGAR (Counterexample-Guided Abstraction Refinement)** provides the theoretical foundation. Abstraction via semantic search provides coarse-grained candidates. Verification through SMT solving checks candidates at fine-grained formal level. Refinement using failed verifications guides retrieval refinement. Iteration continues until high-precision retrieval achieved.

The flow: Semantic Search (probabilistic) generates candidates → SMT Verification (deterministic) provides truth labels → Feedback (learning) refines search → Improved Retrieval achieves higher precision.

### Deterministic Verification Refining Probabilistic Search

**Hybrid symbolic-statistical approach**: Research shows neural-symbolic systems outperform pure neural approaches by 38.5% on structured tasks. The key insight: use symbolic systems where they excel (logical correctness) and neural systems where they excel (pattern recognition).

**For PipesHub-Hupyy:**
- **Neural (PipesHub)**: Semantic understanding, fuzzy matching, context awareness
- **Symbolic (Hupyy)**: Logical consistency, formal correctness, proof generation
- **Synergy**: Neural proposes, symbolic validates, feedback closes the loop

**Concrete example for query "Find API specifications with timeout guarantees"**:

PipesHub retrieves 50 chunks mentioning "timeout", "guarantee", "API" based on semantic similarity. Hupyy extracts formal temporal logic specifications from each chunk. Z3 verifies which chunks contain valid, satisfiable timeout properties.

Results: 8 chunks successfully verified timeout specifications (high rank), 15 chunks mentioned "timeout" but no formal property extractable (medium rank), 12 chunks contained contradictory timeout constraints (filter out), 15 chunks had timeout property in undecidable fragment (flag for expert review).

Feedback: Update embeddings to prioritize "timeout" co-occurring with formal specification keywords like "within", "before", numerical bounds.

### Precision-Recall Tradeoffs

**Initial retrieval (high recall strategy)**: Retrieve k=100 candidates to maximize chance of including correct chunks. Accept initial precision of 30-40%. Use efficient first-stage retriever (dense embedding search).

**After reranking (balance)**: Rerank to k=20 using cross-encoder. Target Recall@20 = 80-85%, Precision@20 = 60-70%.

**After verification (high precision)**: Present top k=5-10 verified chunks. Target Precision@5 = 90%+. Trade recall for certainty.

Mathematical optimization: Maximize Precision@k subject to Recall@k ≥ 0.80 and k ≤ verification_budget.

This multi-stage funnel ensures comprehensive recall early while achieving high precision for final results, optimizing the expensive verification stage.

### Handling UNKNOWN Results

**Timeout UNKNOWN** indicates specification complexity, not necessarily incorrectness. Include with moderate confidence (0.7-0.8). Use "timeout cores" (cvc5 feature) to identify problematic assertions. Suggest simplification or increased resources to user.

**Theory-incomplete UNKNOWN** means specification uses undecidable logic (quantifiers, non-linear arithmetic). Treat as potential positive for advanced queries. Flag as requiring expert review. May indicate sophisticated specification.

Distinguish from genuine failures by checking solver reason codes and analyzing proof attempts.

## E. Integration Patterns

### System Architecture Design

**Recommended microservice integration:**

PipesHub Core contains Query Service, Retrieval (Qdrant + ArangoDB), and Reranking Service. A new Verification Service microservice integrates via Kafka with Verification Orchestrator receiving chunks, calling Hupyy API, and aggregating results. Hupyy Integration extracts SMT specs, calls Z3/cvc5, and structures metadata.

Feedback Loop via Kafka publishes metadata update events containing chunk ID, verification result, confidence score, and failure mode. Metadata Store Updates service updates Qdrant chunk payloads, ArangoDB document properties, and tracks verification history.

### Data Flow: Chunk → Extract → Verify → Update

**Query Initiation**: User Query → Query Service → Embedding Generation → Qdrant Search

**Initial Retrieval**: Qdrant performs vector similarity search (k=100), ArangoDB handles knowledge graph traversal + PageRank, combined hybrid ranking produces top-50 candidates.

**Verification Request** (New stage): Reranking Service publishes Kafka event "verify_chunks". Verification Orchestrator consumes event. For each chunk: extract text content, call Hupyy API to extract_smt_spec(chunk.content), receive formal_spec and extraction_confidence.

**SMT Solving**: For each formal_spec, Hupyy calls Z3/cvc5 returning verdict (SAT/UNSAT/UNKNOWN), confidence (0.0-1.0), artifacts (model/proof/core), statistics (solve_time, conflicts), and failure mode classification.

**Metadata Structuring**: Verification Orchestrator aggregates results with chunk_id, verification_result containing verdict, confidence, solve_time_ms, failure_mode, proof_complexity, theories_used, and timestamp.

**Feedback Update** (Critical step): Publish Kafka event "verification_complete". Metadata Update Service consumes event, updates Qdrant payload adding verification metadata, updates ArangoDB properties incrementing verification_count and updating avg_verification_score, adjusts PageRank weight.

**Result Presentation**: Reranking Service re-scores with verification data. Top k=10 chunks presented to user with original content + citation, verification badge (verified/failed/pending), confidence indicator, and proof summary (if UNSAT).

### Metadata Storage Strategy

**Per-chunk metadata in Qdrant** stores chunk_id, content, embedding, document_id, position, plus verification metadata including status, confidence, verdict, formal_spec, last_verified, verification_count, success_rate, failure_mode, solve_time_ms, theories, proof_complexity, and verification_history array.

**Per-document metadata in ArangoDB** stores document key, title, source, plus verification_metrics including total_chunks, verified_chunks, verification_rate, avg_confidence, sat_count, unsat_count, unknown_count, last_verification_scan. Quality signals include quality_score (used as PageRank weight multiplier), reliability_class, and citation network data.

### PageRank Integration

**Modified PageRank incorporating verification quality:**

Standard PageRank: `PR(A) = (1-d)/N + d * Σ(PR(Ti)/C(Ti))`

**Verification-weighted PageRank:**
```
PR_v(A) = (1-d)/N + d * Σ(Q(Ti) * PR_v(Ti) / C(Ti))

Where:
- Q(Ti) = quality multiplier based on verification (0.5 to 2.0)
- Q(Ti) = 0.5 if avg_confidence < 0.5 (low quality)
- Q(Ti) = 1.0 if no verification data (neutral)
- Q(Ti) = 1.0 + avg_confidence if avg_confidence ≥ 0.5
- Example: 0.9 avg_confidence → Q = 1.9 (strong boost)
```

This creates "quality flow" through the knowledge graph where high-verification documents boost connected documents.

### Cold Start Handling

**New documents without verification history:**

Weeks 1-2: Initial neutral treatment with no verification penalty or boost. Rely on semantic similarity + basic PageRank. Log all retrievals for verification candidates.

Week 3: Rapid verification prioritizing frequently retrieved new documents. Use uncertainty sampling to verify chunks where model is least confident. Allocate 20% of verification budget to exploration (new documents).

Week 4+: Transfer learning propagating verification scores from similar documents. Use content similarity to initialize verification priors with formula: `initial_score = 0.7 * avg_similar_doc_scores + 0.3 * global_avg`.

### Avoiding Overfitting

**Multi-level safeguards:**

**Document-type diversity**: Track verification distribution across document types (API specs, design docs, requirements). Ensure no single type dominates training. Stratified sampling maintains 10% minimum per type.

**Temporal weighting**: Apply exponential decay to old verification results with `weight = exp(-λ * (current_time - verification_time))` where λ = 0.01 for daily decay gives 90% weight after 10 days. Prevents stale data from dominating.

**Query-specific adaptation**: Track which document types relevant for which query patterns. Don't let "API timeout" verifications boost chunks for "database schema" queries. Use query type classification to segment feedback.

**Regularization**: Limit maximum boost from verification capping multiplier at 2.0×. Limit maximum penalty with floor multiplier at 0.3×. Prevents extreme outliers from distorting rankings.

**Holdout validation**: Maintain 15% of documents never used for feedback training. Regular evaluation on holdout set. Alert if holdout performance drops >5% below training set (overfitting signal).

## F. Practical Implementation

### Metadata Schema Design

**Comprehensive verification metadata structure:**

VerificationMetadata dataclass contains verdict (SAT/UNSAT/UNKNOWN), confidence (0.0-1.0), solve_time_ms, timestamp, formal_spec in SMT-LIB2 format, extraction_confidence, theories_used list, optional model (SAT case), optional proof (UNSAT case), optional unsat_core (UNSAT case minimal conflicting assertions), failure_mode classification, failure_indicators list, statistics dictionary, proof_complexity level, solver_info, recommended_action, and user_message for human-readable explanation.

ChunkMetadata dataclass extends existing PipesHub fields (chunk_id, document_id, content, embedding, source, position) with optional verification field, verification_history list, aggregated metrics (verification_count, success_rate, avg_confidence, last_verified), and quality scores for ranking (verification_quality_score, temporal_weight).

### API Design

**Hupyy → PipesHub Integration API:**

```python
class HupyyIntegrationAPI:
    async def verify_chunk(
        self, 
        chunk_id: str,
        content: str,
        context: Optional[Dict] = None
    ) -> VerificationMetadata:
        """Verify a single chunk, returning full verification results"""
        
    async def batch_verify(
        self,
        chunks: List[Tuple[str, str]]
    ) -> List[VerificationMetadata]:
        """Batch verification for efficiency with parallel execution"""
    
    def update_ranking_scores(
        self,
        chunk_id: str,
        verification: VerificationMetadata
    ) -> None:
        """Update Qdrant and ArangoDB with verification results"""
```

The verify_chunk method extracts formal specification, runs SMT solver, classifies failure mode, and computes confidence. The batch_verify method enables parallel execution of verifications. The update_ranking_scores method updates Qdrant payload, updates ArangoDB document properties, and triggers PageRank recalculation asynchronously via Kafka.

### Kafka Event Schema

**Event-driven integration for real-time feedback:**

Events contain event_type "verification_complete", timestamp, chunk_id, document_id, verification_result with verdict/confidence/failure_mode/solve_time_ms/quality_score, and actions array specifying which services to update (qdrant_updater for payloads, arangodb_updater for document metrics, pagerank_calculator for scheduling recalculation).

Event consumers include qdrant_updater (updates chunk payloads immediately), arangodb_updater (updates document-level aggregates), pagerank_calculator (batches PageRank recalculations hourly), and metrics_collector (tracks system-wide verification patterns).

## G. Expected Improvements and Common Pitfalls

### Expected Improvements Over Time

**Retrieval Quality (Primary metrics):**

**NDCG@10**: Baseline 0.65-0.70 (semantic only), target at 3 months 0.75-0.80 (+8-15% improvement)

**MRR**: Baseline 0.55, target 0.70 (+27% improvement) for mean reciprocal rank of first verified result

**Precision@5**: Baseline 40%, target 65-70% (+60-75% improvement) for percentage of top-5 that verify successfully

**Recall@50**: Baseline 85%, target 90%+ (maintain high recall) for percentage of all verifiable chunks in top-50

**Verification Efficiency:**

**Average retrievals per successful verification**: Baseline 10 (10% success rate), target 5 (20% success rate) providing 2× fewer wasted verifications

**Time to first verified result**: Baseline 2.5 rank position, target 1.3 rank position helping users find correct answer faster

**User Experience:**

**Click-through rate on top-3**: Baseline 55%, target 70%

**User satisfaction** (1-5 scale): Baseline 3.8, target 4.3

### Timeline Expectations

**Phase 1 (Weeks 1-4): Foundation** implementing verification integration, collecting baseline metrics, beginning fast feedback loop. Expected improvement: 0-2% (instrumentation overhead may initially hurt).

**Phase 2 (Weeks 5-12): Fast feedback maturation** with real-time score updates stabilizing and sufficient verification data accumulating (>100 per document type). Expected improvement: 3-5% NDCG improvement, 10-15% Precision@5.

**Phase 3 (Weeks 13-24): Medium feedback activation** implementing reranker retraining with verification labels and query pattern optimization. Expected improvement: 6-9% NDCG improvement, 25-35% Precision@5.

**Phase 4 (Weeks 25-52): Slow feedback + optimization** with embedding model fine-tuning and PageRank algorithm optimization. Expected improvement: 8-12% NDCG improvement, 60-75% Precision@5.

**Long-term (Year 2+): Maintenance and continued gains** with continuous improvement as more verifications accumulate. Diminishing returns of 1-2% annual improvement. Focus shifts to coverage of new document types and domains.

### Common Pitfalls and Mitigation

**Pitfall 1: Verification Bottleneck**. Problem: SMT solving expensive, becomes system bottleneck. Symptoms: Query latency increases, verification queue grows. Mitigation: Async verification (don't block user queries), smart sampling (verify high-uncertainty chunks preferentially), caching (reuse verification results for similar chunks), timeout budgets (set aggressive 1-5s timeouts, accept UNKNOWN), tiered verification (fast pre-check filters before expensive full verification).

**Pitfall 2: Feedback Loop Amplification**. Problem: Small biases amplify, system converges to narrow solution space. Symptoms: Verification success rate plateaus early, diversity metrics decrease. Mitigation: Exploration injection (force 10-15% of retrievals from low-ranked candidates), diversity monitoring (track entropy of retrieved document types), rollback triggers (if diversity drops >20%, roll back recent feedback updates), multi-objective optimization (balance verification success with diversity).

**Pitfall 3: Specification Extraction Errors**. Problem: Hupyy extracts incorrect formal specs from natural language. Symptoms: High verification failure rate on documents humans consider correct. Mitigation: Extraction confidence thresholding (only verify if extraction confidence >0.7), human-in-the-loop (flag low-confidence extractions for manual review), specification validation (run sanity checks like vacuity detection), feedback to extraction (track which extraction patterns fail verification, improve extractor).

**Pitfall 4: Theory-Specific Bias**. Problem: System learns to favor specific theories (e.g., QF_LIA) over others. Symptoms: Quantified formulas, non-linear arithmetic consistently rank low. Mitigation: Theory-aware scoring (normalize confidence by theory difficulty), theory-specific models (separate ranking models for different logics), explicit theory handling (mark UNKNOWN-due-to-theory as "advanced" not "failed").

**Pitfall 5: Cold Start Persistence**. Problem: New document types remain under-verified indefinitely. Symptoms: Coverage metrics show persistent gaps. Mitigation: Active learning (allocate verification budget to maximize coverage), mandatory verification (new document types get guaranteed verification slots), transfer learning (initialize new types with similar type's verification patterns).

**Pitfall 6: Temporal Staleness**. Problem: Verification results become outdated as specifications evolve. Symptoms: User complaints about "incorrect" highly-ranked results. Mitigation: Re-verification triggers (document updates trigger re-verification), temporal decay (old verifications count less with exponential decay), periodic scanning (re-verify top-ranked documents quarterly), version tracking (maintain verification results per document version).

**Pitfall 7: Adversarial Specifications**. Problem: Malicious or buggy documents contain "trojan" specifications that verify but behave incorrectly. Symptoms: Verified chunks lead to incorrect user implementations. Mitigation: Model validation (check satisfying models for reasonableness), multiple solvers (require consensus across Z3 and cvc5), proof checking (validate UNSAT proofs with independent proof checker), user feedback (allow users to report "verified but wrong" results).

### Monitoring Dashboard

Key indicators for system health tracked in dashboard:

**RETRIEVAL QUALITY**: NDCG@10, MRR, Precision@5, Recall@50 with percentage changes vs baseline

**VERIFICATION METRICS**: Total verifications, success rate, avg confidence, avg solve time, failure mode distribution showing verified/invalid/ambiguous/incomplete/timeout/theory-incomplete percentages

**FEEDBACK LOOP HEALTH**: Coverage (doc types with ≥5 verifications), diversity entropy in bits, query drift magnitude, exploration rate percentage, holdout performance NDCG comparison

**SYSTEM PERFORMANCE**: Avg query latency, verification queue size, cache hit rate, Kafka lag

**ALERTS**: Critical alerts for holdout performance >10% below training (severe overfitting), warning for diversity <3.0 bits (feedback loop narrowing), warning for verification queue >100 (bottleneck forming), info for success rate changes >5% week-over-week

## Conclusion: Architectural Recommendations Summary

**1. What verification metadata Hupyy should send back to PipesHub:**

Primary signals include verdict (SAT/UNSAT/UNKNOWN), confidence score (0-1), and solve time. Failure mode classification distinguishes invalid/ambiguous/incomplete/timeout/theory-incomplete. Artifacts include models (SAT), proofs (UNSAT), unsatisfiable cores (UNSAT), and statistics. Specification quality data covers formal spec, extraction confidence, and theories used. Diagnostics provide proof complexity, solver info, and recommended actions. User messaging offers human-readable explanations of results.

**2. How PipesHub should use this feedback to improve retrieval:**

Fast feedback (real-time) updates chunk-level quality scores in Qdrant payloads using exponential moving average. Medium feedback (hourly/daily) retrains reranker on verified examples, optimizes query patterns, and adjusts precision-recall tradeoffs. Slow feedback (weekly/monthly) fine-tunes embeddings with contrastive learning (pulling verified chunks closer), rebuilds PageRank with verification-weighted edges. The ranking formula combines semantic similarity (45%) + PageRank (30%) + verification confidence (15%) + historical success (10%), multiplied by failure-mode-specific factor (0.3-1.8×).

**3. Expected improvements in precision/recall over time:**

At 3 months: 8-12% NDCG improvement, 60-75% increase in Precision@5, 2× reduction in wasted verifications. At 6 months: Plateau around 15% total improvement with focus shifting to coverage and edge cases. Long-term: Continuous 1-2% annual gains with asymptotic improvement as verification data saturates.

**4. How to avoid common pitfalls:**

Query drift prevention limits modification magnitude, interpolates with original query, and monitors semantic similarity. Overfitting avoidance uses L2 regularization, temporal decay, holdout validation, and diversity monitoring. Confirmation bias mitigation applies ε-greedy exploration (10-15%), stratified sampling, and coverage tracking. Cold start handling employs three-phase approach (pseudo-RF → hybrid → full feedback) with transfer learning from similar documents. Verification bottleneck solutions include async execution, smart sampling, aggressive timeouts, and caching.

**5. Integration API/data flow design:**

Architecture adds new microservice ("Verification Orchestrator") integrated via Kafka events. Data flow: Query → Retrieve → Verify (async) → Update metadata → Rerank → Present. Storage uses Qdrant payloads for chunk-level metadata and ArangoDB properties for document-level aggregates. PageRank employs modified algorithm using verification quality as edge weights. API provides REST/gRPC endpoints for verify_chunk(), batch_verify(), and update_ranking_scores().

This architecture creates a powerful synergy: **PipesHub's semantic understanding combined with Hupyy's formal verification truth filter produces a search system that improves over time, learning to prioritize formally correct, verifiable content while maintaining the flexibility and context-awareness of neural semantic search.**