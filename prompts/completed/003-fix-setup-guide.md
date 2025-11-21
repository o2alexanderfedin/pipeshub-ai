<objective>
Fix the setup guide at `./docs/setup-guide-local-anthropic.md` with the following corrections:

1. **Remove all Ollama references** - We're not using Ollama
2. **Use `all-MiniLM-L6-v2` for embeddings** - This is a Sentence Transformers model that runs locally
3. **Use short Anthropic model names** - Use "haiku", "sonnet", "opus" instead of version-specific names like "claude-sonnet-4-5-20250929"

The short model names are version-independent and won't break when models are retired.
</objective>

<context>
File to modify: `./docs/setup-guide-local-anthropic.md`

This guide should now describe:
- All local Docker services
- Anthropic (Claude) as LLM provider with short names (haiku/sonnet/opus)
- Local Sentence Transformers `all-MiniLM-L6-v2` for embeddings (no external service needed)
</context>

<changes_required>
1. **Prerequisites**: Remove Ollama installation section entirely

2. **Quick Start**:
   - Remove Ollama installation steps
   - Remove Ollama model download commands
   - Update embedding configuration to use Sentence Transformers

3. **Configuration Details**:
   - Remove `OLLAMA_API_URL` and related variables
   - Add Sentence Transformers embedding configuration
   - Change Anthropic model examples from `claude-sonnet-4-5-20250929` to `sonnet`
   - Document the short model names: haiku, sonnet, opus

4. **Verification**:
   - Remove Ollama connectivity checks
   - Add Sentence Transformers verification if applicable

5. **Troubleshooting**:
   - Remove Ollama troubleshooting section
   - Add any relevant Sentence Transformers issues

6. **Environment Variables Table**:
   - Update embedding model to `all-MiniLM-L6-v2`
   - Update LLM model examples to use short names
</changes_required>

<output>
Modify the file in place: `./docs/setup-guide-local-anthropic.md`
</output>

<verification>
After editing, verify:
- No remaining references to "Ollama" or "ollama"
- Embedding model is `all-MiniLM-L6-v2`
- Anthropic models use short names (haiku, sonnet, opus)
- Guide remains coherent and complete
</verification>

<success_criteria>
- Zero Ollama references in the document
- Embedding model correctly set to all-MiniLM-L6-v2
- All Anthropic model references use short version-independent names
- Guide is still complete and usable
</success_criteria>
