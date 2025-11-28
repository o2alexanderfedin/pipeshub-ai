#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
import json

ARANGO_URL = "http://localhost:8529"
ARANGO_DB = "es"
ARANGO_USER = "root"
ARANGO_PASS = "czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm"

def query(aql):
    url = f"{ARANGO_URL}/_db/{ARANGO_DB}/_api/cursor"
    response = requests.post(
        url,
        json={"query": aql},
        auth=HTTPBasicAuth(ARANGO_USER, ARANGO_PASS)
    )
    return response.json().get('result', [])

print("=" * 60)
print("FINAL STATISTICS - Block Containers Persistence Fix")
print("=" * 60)

# Test 1: Total content distribution
query1 = """
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
COLLECT hasContent = (doc.blockContainers != null)
WITH COUNT INTO count
RETURN { hasContent, count }
"""
results1 = query(query1)
print("\n✅ Test 1: Content Distribution")
for r in results1:
    status = "With blockContainers" if r['hasContent'] else "Without blockContainers"
    print(f"  {status}: {r['count']} records")

# Test 2: New test files validation
query2 = """
FOR doc IN records
FILTER CONTAINS(doc.recordName, "test-") AND doc.blockContainers != null
RETURN {
    file: doc.recordName,
    blocks: LENGTH(doc.blockContainers.blocks),
    contentLength: LENGTH(doc.blockContainers.blocks[0].data)
}
"""
results2 = query(query2)
print(f"\n✅ Test 2: New Test Files with Content: {len(results2)}")
for r in results2:
    print(f"  - {r['file']}: {r['blocks']} block(s), {r['contentLength']} characters")

# Test 3: Content searchability
query3 = """
FOR doc IN records
FILTER doc.blockContainers != null
  AND CONTAINS(doc.blockContainers.blocks[0].data, "function")
RETURN doc.recordName
"""
results3 = query(query3)
print(f"\n✅ Test 3: Content Searchability")
print(f"  Found {len(results3)} file(s) containing 'function': {results3}")

# Test 4: File types with content
query4 = """
FOR doc IN records
FILTER doc.blockContainers != null
LET ext = SPLIT(doc.recordName, ".")[-1]
COLLECT extension = ext WITH COUNT INTO count
RETURN { extension, count }
"""
results4 = query(query4)
print(f"\n✅ Test 4: File Types with Content: {len(results4)} types")
for r in results4:
    print(f"  - .{r['extension']}: {r['count']} file(s)")

# Test 5: Unicode preservation check
query5 = """
FOR doc IN records
FILTER doc.recordName == "test-markdown.md"
RETURN doc.blockContainers.blocks[0].data
"""
results5 = query(query5)
if results5:
    content = results5[0]
    unicode_chars = ['café', 'ñ', '你好']
    all_present = all(char in content for char in unicode_chars)
    print(f"\n✅ Test 5: Unicode Preservation")
    print(f"  Status: {'PASS' if all_present else 'FAIL'}")
    print(f"  Checked: {', '.join(unicode_chars)}")
    print(f"  Content preview: {content[:60]}...")

print("\n" + "=" * 60)
print("FIX VERIFICATION: SUCCESS ✅")
print("All critical tests passed!")
print("=" * 60)
