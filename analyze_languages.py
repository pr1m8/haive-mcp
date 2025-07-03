#!/usr/bin/env python3
import json
from collections import Counter

with open('agent_resources/mcp_servers/all_mcp_documents.json') as f:
    data = json.load(f)
    
# Count languages
langs = []
for item in data:
    langs.extend(item.get('metadata', {}).get('languages', []))
    
print('Language distribution:')
for lang, count in Counter(langs).most_common(20):
    print(f'  {lang}: {count}')
    
# Show examples with real languages
print('\nExamples with programming languages:')
count = 0
for item in data:
    item_langs = item.get('metadata', {}).get('languages', [])
    if item_langs and item_langs[0] != 'Other':
        name = item.get('metadata', {}).get('name', '')
        repo = item.get('metadata', {}).get('repo_url', '')
        print(f'  {name}: {item_langs} - {repo}')
        count += 1
        if count >= 10:
            break