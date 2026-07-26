from pathlib import Path

path = Path('hmi-source/mod/src/main/java/com/holdmylua/source/mixin/player/CameraMixin.java')
text = path.read_text(encoding='utf-8')
if 'import org.joml.Vector3fc;' not in text:
    text = text.replace('import org.joml.Vector3f;\n', 'import org.joml.Vector3f;\nimport org.joml.Vector3fc;\n')
for name in ('FORWARDS', 'UP', 'LEFT'):
    old = f'private static Vector3f {name};'
    new = f'private static Vector3fc {name};'
    if old not in text:
        raise RuntimeError(f'Expected camera shadow not found: {old}')
    text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
