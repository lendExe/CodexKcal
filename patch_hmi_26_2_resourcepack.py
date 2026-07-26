from pathlib import Path
import json

path = Path('hmi-source/mod/src/main/resources/resourcepacks/pack_test/pack.mcmeta')
data = json.loads(path.read_text(encoding='utf-8'))
pack = data.setdefault('pack', {})
pack['pack_format'] = 88
for obsolete in ('supported_formats', 'min_format', 'max_format'):
    pack.pop(obsolete, None)
path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
