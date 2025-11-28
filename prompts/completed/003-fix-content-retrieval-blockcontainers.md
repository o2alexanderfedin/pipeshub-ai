<objective>
Fix the search and retrieval system to correctly access document content from the ArangoDB blockContainers structure. Currently, the Q&A chat reports "token validation error" for all files when in fact the content is properly stored in the blockContainers.blocks[].data field. This prevents the AI assistant from providing meaningful answers based on indexed document content.

This matters because users cannot get answers from their indexed files, making the entire Q&A system non-functional despite successful indexing.
</objective>

<context>
The PipesHub AI system uses ArangoDB to store indexed documents. Investigation revealed:

**Current State:**
- 25 markdown files are successfully indexed with indexingStatus: "COMPLETED"
- File content IS stored in ArangoDB records collection
- Content structure: `record.blockContainers.blocks[0].data` contains the full text
- 50 vectors created in Qdrant for semantic search
- Chat interface works (no AttributeError after previous fix)

**The Problem:**
- When users ask questions, the retrieval system retrieves records but reports "token validation error"
- The retrieval code is NOT accessing content from the blockContainers structure
- It may be looking for content in old/deprecated fields like `text_content` (which is empty/null)

**Tech Stack:**
- Backend: Python (FastAPI)
- Database: ArangoDB (stores records with blockContainers structure)
- Vector DB: Qdrant (stores embeddings)
- LLM: Anthropic Claude Sonnet 4.5 via langchain_anthropic

**File Evidence:**
Query result showing content IS stored:
```json
{
  "virtualRecordId": "a8551a1c-d3ec-4bbb-8482-e445f335647c",
  "blockContainers": {
    "block_groups": [],
    "blocks": [
      {
        "id": "766e4542-edd6-444c-b5af-6f99bddd6c4f",
        "type": "text",
        "format": "txt",
        "data": "# Connector Integration Playbook\n\n**Target Audience:**..."
      }
    ]
  }
}
```

Read CLAUDE.md for project conventions and coding standards.
</context>

<requirements>
1. **Identify retrieval code**: Find where the system retrieves document content for Q&A
2. **Fix content extraction**: Update code to properly extract text from `blockContainers.blocks[].data`
3. **Handle multiple blocks**: If multiple blocks exist, concatenate them appropriately
4. **Preserve vector search**: Don't break the existing Qdrant vector search functionality
5. **Test the fix**: Verify that chat can now access actual document content
6. **Handle edge cases**: Empty blocks, missing blockContainers, null values
</requirements>

<research>
Start by exploring the codebase to understand the retrieval flow:

1. **Find the retrieval service:**
   - Look for code that queries ArangoDB records for Q&A
   - Search for: "retrieval", "search", "query_service", "chatbot"
   - Check: `backend/python/app/api/routes/chatbot.py` (chat endpoint)
   - Check: `backend/python/app/query/` or similar query service directories

2. **Identify where content is extracted:**
   - Find where record data is transformed for the LLM
   - Look for field access patterns (e.g., `record.text_content`, `record.content`)
   - Identify the data structure returned from ArangoDB queries

3. **Locate the bug:**
   - Find code that's NOT accessing `blockContainers.blocks[].data`
   - Look for deprecated field references or null checks

4. **Find related code:**
   - Vector search integration (Qdrant queries)
   - Document chunking/embedding generation (to understand expected format)
   - Indexing code (to see how content was originally stored)
</research>

<implementation>
**What to fix:**
1. Update the retrieval service to extract content from `blockContainers.blocks[].data`
2. Implement proper content extraction function:
   ```python
   def extract_content_from_blocks(record: dict) -> str:
       """Extract text content from blockContainers structure."""
       block_containers = record.get("blockContainers", {})
       blocks = block_containers.get("blocks", [])

       # Concatenate all text blocks
       content_parts = []
       for block in blocks:
           if block.get("type") == "text" and block.get("data"):
               content_parts.append(block["data"])

       return "\n\n".join(content_parts) if content_parts else ""
   ```
3. Replace any references to deprecated content fields (e.g., `text_content`)
4. Ensure the fix handles both old and new record formats (backward compatibility)

**What to avoid and WHY:**
- Don't modify the indexing pipeline - it's working correctly (content is being stored properly)
- Don't change the vector embedding structure - vectors are already created correctly
- Don't alter ArangoDB schema - the blockContainers structure is the correct format
- Don't break existing Qdrant searches - vector search is functional

**Testing approach:**
1. Restart the service after code changes
2. Use browser UI to ask: "Tell me about the connector integration playbook"
3. Verify the response contains actual content from the playbook (not "token validation error")
4. Check that sources and citations are properly linked
</implementation>

<output>
Modify the relevant Python files to fix content retrieval:
- Likely location: `./backend/python/app/query/` or `./backend/python/app/api/routes/chatbot.py`
- May need to update: retrieval service, document processors, or search utilities

After making changes:
1. Rebuild and restart the Docker service
2. Provide verification steps showing the fix works
</output>

<verification>
Before declaring complete, verify:

1. **Code changes made:**
   - [ ] Found and updated the content extraction code
   - [ ] Added blockContainers.blocks[].data access
   - [ ] Handled edge cases (empty blocks, missing fields)

2. **Service restarted:**
   - [ ] Rebuilt Docker image with changes
   - [ ] Service started without errors
   - [ ] No new errors in logs

3. **Functional test passed:**
   - [ ] Asked chat: "Tell me about the connector integration playbook"
   - [ ] Response contains actual content (not "token validation error")
   - [ ] Sources and citations work correctly
   - [ ] Can ask follow-up questions about the content

4. **No regressions:**
   - [ ] Vector search still works
   - [ ] Other indexed files also return content
   - [ ] No performance degradation
</verification>

<success_criteria>
- Retrieval code correctly accesses `blockContainers.blocks[].data`
- Chat assistant returns actual file content when asked questions
- No "token validation error" messages in responses
- All 25 indexed files are searchable with real content
- Service logs show no errors
- Q&A system is fully functional for demo use
</success_criteria>
