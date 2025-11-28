#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app/python')

from app.connectors.core.base.db.arango_service import ArangoService
from app.config.arango_config import get_arango_config

try:
    config = get_arango_config()
    service = ArangoService(config)

    # Query for records with blockContainers
    query = """
    FOR doc IN records
    FILTER doc.connectorName == "LOCAL_FILESYSTEM"
      AND HAS(doc, 'blockContainers')
    LIMIT 5
    RETURN {
        recordName: doc.recordName,
        hasBlocks: LENGTH(doc.blockContainers.blocks) > 0,
        blockCount: LENGTH(doc.blockContainers.blocks),
        contentPreview: doc.blockContainers.blocks[0] ? SUBSTRING(doc.blockContainers.blocks[0].data, 0, 100) : null
    }
    """

    results = service.execute_query(query)
    print(f"✅ SUCCESS: Found {len(results)} records with blockContainers")

    if len(results) > 0:
        print("\nSample results:")
        for i, r in enumerate(results[:3], 1):
            print(f"\n{i}. File: {r['recordName']}")
            print(f"   Has blocks: {r['hasBlocks']}")
            print(f"   Block count: {r['blockCount']}")
            if r['contentPreview']:
                preview = r['contentPreview'][:60]
                print(f"   Content: {preview}...")
    else:
        print("\n❌ ISSUE: No records found with blockContainers field")
        print("This means the fix didn't work OR no sync has occurred yet")

        # Check total records
        query2 = "FOR doc IN records FILTER doc.connectorName == 'LOCAL_FILESYSTEM' LIMIT 10 RETURN doc.recordName"
        total = service.execute_query(query2)
        print(f"\nTotal LOCAL_FILESYSTEM records: {len(total)}")
        if len(total) > 0:
            print(f"Sample files: {', '.join(total[:5])}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
