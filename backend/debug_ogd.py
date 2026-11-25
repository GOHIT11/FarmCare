import json
import sys
import os
sys.path.append(os.path.dirname(__file__))
from ogd_service import OGDService
s = OGDService()
data = s.fetch_data('18/03/2026')
with open('c:/tmp/ogd_debug.json', 'w') as f:
    json.dump(data, f, indent=2)
print(f"Saved {len(data)} records to debug file")
