#!/usr/bin/env python3
"""
Test script to verify chat retrieval is working correctly with blockContainers structure.
"""
import asyncio
import aiohttp
import json

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_QUERY = "Tell me about the connector integration playbook"

async def test_chat():
    """Test the chat endpoint with a simple query"""

    # This is a mock token - replace with actual token if needed
    headers = {
        "Content-Type": "application/json",
        # Add authorization header if needed
    }

    payload = {
        "query": TEST_QUERY,
        "limit": 5,
        "previousConversations": [],
        "retrievalMode": "HYBRID",
        "quickMode": False,
        "mode": "json"
    }

    url = f"{BASE_URL}/api/v1/query/chat"

    print(f"Testing chat endpoint: {url}")
    print(f"Query: {TEST_QUERY}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                print(f"Status Code: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print("\n=== RESPONSE ===")
                    print(json.dumps(result, indent=2))

                    # Check if we got actual content
                    if "answer" in result:
                        answer = result["answer"]
                        print(f"\n=== ANSWER ===")
                        print(answer)

                        # Check for the "token validation error" message
                        if "token validation error" in answer.lower():
                            print("\n❌ ERROR: Found 'token validation error' in response!")
                            return False
                        else:
                            print("\n✅ SUCCESS: No 'token validation error' found")
                            return True

                    if "citations" in result:
                        citations = result["citations"]
                        print(f"\n=== CITATIONS ({len(citations)}) ===")
                        for i, citation in enumerate(citations[:3]):  # Show first 3
                            print(f"\nCitation {i+1}:")
                            print(f"  Content: {citation.get('content', '')[:100]}...")
                            print(f"  Metadata: {citation.get('metadata', {})}")
                else:
                    error_text = await response.text()
                    print(f"\n❌ ERROR Response:")
                    print(error_text)
                    return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("CHAT RETRIEVAL TEST")
    print("=" * 80)
    print("\nThis script tests if the chat system can retrieve and display content")
    print("from indexed files with the blockContainers structure.\n")

    success = asyncio.run(test_chat())

    print("\n" + "=" * 80)
    if success:
        print("TEST PASSED ✅")
    else:
        print("TEST FAILED ❌")
    print("=" * 80)
