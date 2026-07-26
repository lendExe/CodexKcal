from pathlib import Path
import json

path = Path('hmi-source/mod/src/main/resources/resourcepacks/pack_test/pack.mcmeta')
data = json.loads(path.read_text(encoding='utf-8'))
pack = data.setdefault('pack', {})
pack['pack_format'] = 88
pack['supported_formats'] = [88, 88]
pack['min_format'] = 88
pack['max_format'] = 88
path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
