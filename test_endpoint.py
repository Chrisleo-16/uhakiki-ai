#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/cb-fx/uhakiki-ai/backend')

from app.db.milvus_client import search_vault

def test_search():
    try:
        print("Testing search_vault function...")
        results = search_vault("Verification", limit=50)
        print(f"Results type: {type(results)}")
        print(f"Results length: {len(results)}")
        print(f"Results: {results}")
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_search()
