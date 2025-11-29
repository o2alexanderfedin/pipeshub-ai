# Research: Provider-Agnostic Batch API & Prompt Caching Implementation

<objective>
Research how to implement Batch API and Prompt Caching in the PipesHub indexing pipeline in a provider-agnostic way that:

1. Works across all LLM providers supported by PipesHub (Anthropic, OpenAI, Google, etc.)
2. Provides a unified interface regardless of underlying provider
3. Maximizes cost savings when features are available
4. Gracefully falls back to standard API when features are unavailable
5. Does NOT lock the codebase to a single provider

This is critical for maintaining PipesHub's multi-provider architecture while achieving 50-95% cost reduction.
</objective>

<context>
- **Current system**: PipesHub supports multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini, local models)
- **Discovery**: Anthropic offers Batch API (50% discount) and Prompt Caching (90% savings)
- **Goal**: Implement these optimizations WITHOUT breaking multi-provider support
- **Challenge**: Each provider has different batching and caching APIs (or none at all)
- **Requirement**: Unified abstraction layer that works identically across all providers

**Current Architecture** (assumption - verify in codebase):
- Likely has an LLM abstraction layer or adapter pattern
- Indexing service makes LLM calls for document processing
- Need to inject batch/cache logic without breaking existing interfaces
</context>

<requirements>

## Primary Research Questions

### 1. Provider Feature Comparison

**Research each provider's capabilities**:

**Anthropic Claude**:
- Batch API: Yes (50% discount, 24hr processing)
- Prompt Caching: Yes (90% savings on cached context)
- API format: Custom headers and endpoints
- Documentation: Official Anthropic docs

**OpenAI GPT**:
- Batch API: Yes (similar to Anthropic, 50% discount)
- Prompt Caching: No official caching, but has "context window optimization"
- API format: Different from Anthropic
- Documentation: OpenAI Batch API docs

**Google Gemini**:
- Batch API: Has batch processing capabilities
- Prompt Caching: Yes ("context caching" feature)
- API format: Different from both Anthropic and OpenAI
- Documentation: Google AI docs

**Other Providers** (verify if PipesHub supports):
- Local models (Ollama, etc.): No batch/cache (in-process)
- Azure OpenAI: Same as OpenAI
- AWS Bedrock: Provider-specific batching

**Create comparison table**:
```
| Provider   | Batch API | Caching | Discount | Async? | Implementation Complexity |
|------------|-----------|---------|----------|--------|---------------------------|
| Anthropic  | ✅        | ✅      | 50-95%   | Yes    | Medium                    |
| OpenAI     | ✅        | ❌/⚠️   | 50%      | Yes    | Medium                    |
| Google     | ✅        | ✅      | 50-90%   | Yes    | Medium                    |
| Local      | ❌        | ❌      | N/A      | No     | N/A                       |
```

### 2. Abstraction Layer Design

**Design unified interface** that works across all providers:

```typescript
interface BatchRequest {
  messages: Message[];
  model: string;
  config: RequestConfig;
}

interface CacheableContext {
  cacheKey: string;
  content: string;
  ttl?: number;
}

interface LLMProvider {
  // Standard methods (already exist)
  send(message: Message): Promise<Response>;

  // New methods for optimization
  sendBatch?(requests: BatchRequest[]): Promise<BatchJob>;
  sendWithCache?(message: Message, cache: CacheableContext): Promise<Response>;

  // Feature detection
  supportsBatching(): boolean;
  supportsCaching(): boolean;
}
```

**Key design decisions**:
- Should batching/caching be opt-in or automatic?
- How to handle providers that don't support features?
- Where to inject batch/cache logic in existing pipeline?
- How to maintain backward compatibility?

### 3. Implementation Strategies

**Research THREE possible approaches**:

**A. Adapter Pattern** (Recommended):
- Each provider implements common interface
- Provider-specific batch/cache logic encapsulated
- Indexing service uses unified API
- Graceful fallback built into adapters

**B. Decorator Pattern**:
- Wrap existing LLM calls with batch/cache decorators
- Decorators check provider capabilities
- Fall back to standard calls if unsupported

**C. Strategy Pattern**:
- Runtime selection of batch/cache strategy
- Provider capabilities detected dynamically
- Switch between optimized and standard calls

**Compare approaches**:
- Which best maintains multi-provider support?
- Which is easiest to implement in existing codebase?
- Which provides best performance?
- Which has least risk of breaking changes?

### 4. Codebase Integration

**Investigate PipesHub's current architecture**:

Research in codebase:
- Find LLM abstraction layer (likely in `backend/python/app/services/`)
- Identify where LLM calls are made during indexing
- Check existing provider implementations
- Locate configuration for provider selection

Search for:
- `anthropic`, `openai`, `google` imports
- `llm_provider`, `ai_service`, `model_service` modules
- Indexing pipeline code that calls LLMs
- Provider configuration (environment variables, config files)

**Map out injection points**:
- Where to add batch submission logic?
- Where to inject caching headers?
- How to make changes backward compatible?

### 5. Fallback Strategy

**Design graceful degradation**:

```
IF provider.supportsBatching() AND request.canBeBatched():
  → Use Batch API (50% savings)
ELSE IF provider.supportsCaching() AND request.hasCacheableContext():
  → Use Prompt Caching (90% savings)
ELSE:
  → Use standard API (no savings, but still works)
```

**Questions**:
- How to detect if batching is beneficial?
- When to use caching vs batching vs both?
- How to handle mixed workloads (some urgent, some async)?

### 6. Configuration & Control

**Research configuration approach**:

```yaml
# Example config structure
llm_optimization:
  batching:
    enabled: true
    providers: ["anthropic", "openai", "google"]
    max_batch_size: 10000
    timeout: 86400  # 24 hours

  caching:
    enabled: true
    providers: ["anthropic", "google"]
    ttl: 3600  # 1 hour

  fallback:
    enabled: true  # Fall back to standard API if batch/cache fails
```

**Questions**:
- Should this be per-provider or global?
- How to override for specific use cases?
- How to monitor effectiveness (cache hit rates, batch savings)?

</requirements>

<output>
Save comprehensive research to: `.prompts/005-llm-batch-caching-abstraction-research/llm-batch-caching-abstraction-research.md`

Include:

### 1. Provider Capability Matrix
[Complete comparison table of batch/cache support across providers]

### 2. Recommended Architecture
[Detailed design for provider-agnostic implementation]

### 3. Code Examples
[TypeScript/Python examples showing unified interface]

### 4. Integration Plan
[Where and how to modify existing PipesHub codebase]

### 5. Migration Strategy
[Step-by-step plan to add features without breaking changes]

### 6. Testing Approach
[How to test across multiple providers]

### 7. Monitoring & Metrics
[How to track cost savings and feature usage]

Create SUMMARY.md with:
- **One-liner**: How to implement provider-agnostic batch/cache optimization
- **Key Findings**: Best architecture pattern, provider compatibility matrix
- **Decisions Needed**: Which pattern to use, configuration approach
- **Blockers**: Any provider-specific limitations or codebase constraints
- **Next Step**: Concrete action to start implementation

<metadata>
- `<confidence>`: High/Medium/Low based on codebase analysis
- `<dependencies>`: Access to PipesHub codebase, provider documentation
- `<open_questions>`: Unknowns about current architecture, provider capabilities
- `<assumptions>`: Assumptions about existing abstraction layer
</metadata>
</output>

<verification>
Before finalizing, verify:
- [ ] Checked ALL major LLM provider docs (Anthropic, OpenAI, Google)
- [ ] Analyzed PipesHub codebase for existing LLM abstraction
- [ ] Identified specific files/modules to modify
- [ ] Confirmed backward compatibility approach
- [ ] Designed provider capability detection
- [ ] Created unified interface definition
- [ ] Validated fallback strategy
- [ ] Provided code examples in PipesHub's language (Python/TypeScript)
</verification>

<success_criteria>
- Clear comparison of batch/cache capabilities across providers
- Recommended architecture pattern for abstraction
- Concrete integration plan for PipesHub codebase
- Graceful fallback strategy for unsupported providers
- No breaking changes to existing multi-provider support
- Code examples in correct language
- Monitoring/configuration approach defined
</success_criteria>
