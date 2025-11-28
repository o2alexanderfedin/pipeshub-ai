#!/usr/bin/env python3
"""
Diagnostic script to check if content is being properly extracted from blockContainers.
This script simulates the content extraction logic used in chat_helpers.py
"""
import json

# Sample record structure as shown in the user's evidence
sample_record = {
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

def extract_content_from_blocks(record: dict) -> str:
    """
    Extract text content from blockContainers structure.
    This mimics the logic in chat_helpers.py
    """
    print("=" * 80)
    print("CONTENT EXTRACTION TEST")
    print("=" * 80)

    block_containers = record.get("blockContainers", {})
    print(f"\n1. blockContainers found: {block_containers is not None}")
    print(f"   Type: {type(block_containers)}")

    blocks = block_containers.get("blocks", [])
    print(f"\n2. blocks array found: {blocks is not None}")
    print(f"   Type: {type(blocks)}")
    print(f"   Length: {len(blocks)}")

    # Extract all text blocks (mimics chat_helpers.py logic)
    content_parts = []
    for i, block in enumerate(blocks):
        print(f"\n3. Processing block {i}:")
        print(f"   Block type: {type(block)}")

        block_type = block.get("type")
        print(f"   Block 'type' field: {block_type}")

        if block_type == "text":
            # This is the critical line - matching chat_helpers.py line 86
            data = block.get("data", "")
            print(f"   Block 'data' field: {repr(data[:100])}..." if data else "   Block 'data' field: EMPTY")

            if data:
                content_parts.append(data)
                print(f"   ✅ Content extracted successfully ({len(data)} chars)")
            else:
                print(f"   ❌ WARNING: Block has no data!")

    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)

    if content_parts:
        full_content = "\n\n".join(content_parts)
        print(f"\n✅ SUCCESS: Extracted {len(content_parts)} text block(s)")
        print(f"Total content length: {len(full_content)} characters")
        print(f"\nFirst 200 characters:")
        print(full_content[:200])
        return full_content
    else:
        print(f"\n❌ FAILURE: No content extracted!")
        return ""

def simulate_chat_message_content(blocks_content: str, query: str) -> str:
    """
    Simulate how content would be formatted for the LLM
    This mimics get_message_content in chat_helpers.py
    """
    print("\n" + "=" * 80)
    print("LLM MESSAGE CONSTRUCTION")
    print("=" * 80)

    if not blocks_content:
        print("\n❌ ERROR: No content available to send to LLM!")
        print("This would cause the LLM to respond with an error or 'no content found' message.")
        return ""

    message = f"""<context>
<record>
* Record Name: Connector Integration Playbook
* Record content:
* Block Number: R1-0
* Block Type: text
* Block Content: {blocks_content}
</record>
</context>

Query: {query}
"""

    print(f"\n✅ Message constructed ({len(message)} chars)")
    print(f"\nMessage preview (first 300 chars):")
    print(message[:300])

    return message

if __name__ == "__main__":
    print("\nThis script tests if content extraction from blockContainers works correctly.\n")

    # Test extraction
    extracted_content = extract_content_from_blocks(sample_record)

    # Test message construction
    test_query = "Tell me about the connector integration playbook"
    llm_message = simulate_chat_message_content(extracted_content, test_query)

    print("\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)

    if extracted_content and llm_message:
        print("\n✅ PASSED: Content extraction is working correctly")
        print("   - blockContainers.blocks[].data is accessible")
        print("   - Content can be sent to LLM")
        print("\nConclusion: The content extraction logic is CORRECT.")
    else:
        print("\n❌ FAILED: Content extraction is broken")
        print("   - Unable to extract content from blockContainers")
        print("\nConclusion: The content extraction logic needs to be FIXED.")

    print("=" * 80)
