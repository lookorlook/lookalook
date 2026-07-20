import os

# Read current file
path = r'project/app/reconciliation.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _score_name with improved version
old = '''def _score_name(att_name, inv_name):
    ca = _clean(att_name).upper()
    ci = _clean(inv_name).upper()
    if ca == ci: return 1.0
    wa = set(ca.split())
    wi = set(ci.split())
    if not wa or not wi: return 0.0
    overlap = len(wa & wi)
    total = len(wa | wi)
    return overlap / total if total > 0 else 0.0'''

new = '''from difflib import SequenceMatcher

def _normalize(s):
    \"\"\"Normalize name: remove accents, lowercase, remove special chars.\"\"\"
    s = s.lower().replace('\\u00e9', 'e').replace('\\u00e8', 'e').replace('\\u00ea', 'e')
    s = s.replace('\\u00e0', 'a').replace('\\u00e2', 'a')
    s = s.replace('\\u00ee', 'i').replace('\\u00ef', 'i')
    s = s.replace('\\u00f4', 'o').replace('\\u00f9', 'u').replace('\\u00fc', 'u')
    s = s.replace('\\u00e7', 'c')
    return s

def _score_name(att_name, inv_name):
    \"\"\"Hybrid name similarity: word overlap + character-level matching.\"\"\"
    ca = _clean(_normalize(att_name))
    ci = _clean(_normalize(inv_name))
    if ca == ci: return 1.0
    
    # Word overlap score
    wa = set(ca.split())
    wi = set(ci.split())
    word_overlap = len(wa & wi) / max(len(wa | wi), 1) if wa and wi else 0
    
    # Character-level similarity for individual words
    char_scores = []
    for aw in wa:
        best = max(SequenceMatcher(None, aw, iw).ratio() for iw in wi) if wi else 0
        char_scores.append(best)
    avg_char = sum(char_scores) / max(len(char_scores), 1) if char_scores else 0
    
    # Combined score (word overlap matters more)
    return max(word_overlap, avg_char * 0.8)'''

content = content.replace(old, new, 1)

# Also reduce threshold to 0.35 since some names are quite different
content = content.replace('AUTO_MATCH_THRESHOLD = 0.4', 'AUTO_MATCH_THRESHOLD = 0.35')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated:', path)
