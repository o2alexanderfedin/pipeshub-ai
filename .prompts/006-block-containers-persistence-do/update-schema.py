#!/usr/bin/env python3
"""
Update ArangoDB records collection schema to include blockContainers field.
"""
import json
import requests
from requests.auth import HTTPBasicAuth

# ArangoDB connection
ARANGO_URL = "http://localhost:8529"
ARANGO_DB = "es"
ARANGO_USER = "root"
ARANGO_PASS = "czXG+1VB1mMGFcRoLJ2lzGA+E9fxGJqm"
COLLECTION = "records"

# Load current schema
with open('current-schema.json', 'r') as f:
    current_schema = json.load(f)

# Add blockContainers to schema properties
block_containers_schema = {
    "type": ["object", "null"],
    "properties": {
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "format": {"type": "string"},
                    "data": {"type": "string"},
                    "index": {"type": ["number", "null"]},
                    "parent_index": {"type": ["number", "null"]},
                    "name": {"type": ["string", "null"]},
                    "comments": {"type": ["array", "null"]},
                    "source_creation_date": {"type": ["number", "null"]},
                    "source_update_date": {"type": ["number", "null"]},
                    "source_id": {"type": ["string", "null"]},
                    "source_name": {"type": ["string", "null"]},
                    "source_type": {"type": ["string", "null"]},
                    "links": {"type": ["array", "null"]},
                    "weburl": {"type": ["string", "null"]},
                    "public_data_link": {"type": ["string", "null"]},
                    "public_data_link_expiration_epoch_time_in_ms": {"type": ["number", "null"]},
                    "citation_metadata": {"type": ["object", "null"]},
                    "list_metadata": {"type": ["object", "null"]},
                    "table_row_metadata": {"type": ["object", "null"]},
                    "table_cell_metadata": {"type": ["object", "null"]},
                    "code_metadata": {"type": ["object", "null"]},
                    "media_metadata": {"type": ["object", "null"]},
                    "file_metadata": {"type": ["object", "null"]},
                    "link_metadata": {"type": ["object", "null"]},
                    "image_metadata": {"type": ["object", "null"]},
                    "semantic_metadata": {"type": ["object", "null"]}
                },
                "required": ["id", "type", "format", "data"]
            }
        },
        "block_groups": {
            "type": "array",
            "items": {"type": "object"}
        }
    }
}

# Insert blockContainers after isShared
current_schema['schema']['rule']['properties']['blockContainers'] = block_containers_schema

print("Updated schema with blockContainers field")
print(f"Total properties: {len(current_schema['schema']['rule']['properties'])}")

# Save updated schema
with open('updated-schema.json', 'w') as f:
    json.dump(current_schema, f, indent=2)
print("Saved to updated-schema.json")

# Prepare schema update payload (only the schema part)
schema_update = {
    "schema": current_schema['schema']
}

# Update collection schema
url = f"{ARANGO_URL}/_db/{ARANGO_DB}/_api/collection/{COLLECTION}/properties"
response = requests.put(
    url,
    json=schema_update,
    auth=HTTPBasicAuth(ARANGO_USER, ARANGO_PASS)
)

if response.status_code == 200:
    print(f"\n✅ SUCCESS: Schema updated for collection '{COLLECTION}'")
else:
    print(f"\n❌ ERROR: Failed to update schema")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
