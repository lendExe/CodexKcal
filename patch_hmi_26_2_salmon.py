from pathlib import Path
import json

pack = Path('hmi-source/mod/src/main/resources/resourcepacks/pack_test/assets/minecraft')
model_path = pack / 'models/item/salmon_bucket_3d.json'
model = json.loads(model_path.read_text(encoding='utf-8'))

fixed = 0
for element in model.get('elements', []):
    for face in element.get('faces', {}).values():
        uv = face.get('uv')
        if uv == [-1, 2, 0, 2]:
            face['uv'] = [0, 2, 1, 2]
            fixed += 1
        elif uv == [-1, 1, 0, 1]:
            face['uv'] = [0, 1, 1, 1]
            fixed += 1

if fixed != 2:
    raise RuntimeError(f'Expected to repair two salmon bucket UV faces, repaired {fixed}')

model_path.write_text(json.dumps(model, indent=2) + '\n', encoding='utf-8')

# The bundled PNG is a single 32x32 image, but the old metadata references
# frames 0..20. Minecraft 26.2 treats those as invalid. Keep it static.
metadata = pack / 'textures/item/salmon_bucket_3d.png.mcmeta'
metadata.unlink(missing_ok=True)
