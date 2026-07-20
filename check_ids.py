import re

with open(r'project/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find ALL getElementById references
for m in re.findall(r'getElementById\(['\x60"]([^'\x60"]*)['\x60"]\)', html):
    print(m)
print('---')
# Find all id=\" attributes in HTML elements
for m in re.findall(r'\bid=\"([a-zA-Z0-9_]+)\"', html):
    print(m)
