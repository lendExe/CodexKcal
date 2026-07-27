from pathlib import Path
import json

path = Path('hmi-source/mod/src/main/resources/holdmyitems.mixins.json')
data = json.loads(path.read_text(encoding='utf-8'))
entry = 'render.HangingSignMixin'
if entry in data.get('mixins', []):
    data['mixins'].remove(entry)
path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
