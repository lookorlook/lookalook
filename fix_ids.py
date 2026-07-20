import re

with open(r'project/templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix corrupted element IDs caused by Chinese translation
fixes = {
    'sel国家': 'selCountry',
    'sel供应商': 'selSupplier', 
    'rule标签': 'ruleLabel',
    'ruleItem分类': 'ruleItemClass',
}

for old, new in fixes.items():
    count = html.count(old)
    if count > 0:
        html = html.replace(old, new)
        print('Fixed %s: %d occurrences' % (old, count))

with open(r'project/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
