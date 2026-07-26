from pathlib import Path
import re

root = Path('hmi-source/mod/src/main/java')

# Keep the slower timing that already feels better on Minecraft 26.2.
game_renderer = root / 'com/holdmylua/source/mixin/client/GameRendererMixin.java'
text = game_renderer.read_text(encoding='utf-8')
text, count = re.subn(
    r'LuaTestHMI\.deltaTime\s*=\s*Math\.min\(elapsed(?:\s*\*\s*0\.65F)?,\s*0\.05F\);',
    'LuaTestHMI.deltaTime = Math.min(elapsed * 0.65F, 0.05F);',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError(f'Delta-time assignment replacement count: {count}')
game_renderer.write_text(text, encoding='utf-8')

held = root / 'com/holdmylua/source/mixin/render/HeldItemRendererMixin.java'
text = held.read_text(encoding='utf-8')

# Remove the vanilla-progress fallback. It made the HMI attack snap too fast.
custom_swing = '''float mainHandProgress = accessor.hMI5_0$getMainHandSwingProgress(tickProgress);
             this.mainHandSwingProgress = mainHandProgress;
             float offHandProgress = accessor.hMI5_0$getOffHandSwingProgress(tickProgress);
             this.offHandSwingProgress = offHandProgress;
             swingProgress = bl ? mainHandProgress : offHandProgress;'''
pattern = re.compile(
    r'float\s+vanillaSwingProgress\s*=\s*swingProgress;\s*'
    r'float\s+mainHandProgress\s*=\s*accessor\.hMI5_0\$getMainHandSwingProgress\(tickProgress\);\s*'
    r'float\s+offHandProgress\s*=\s*accessor\.hMI5_0\$getOffHandSwingProgress\(tickProgress\);\s*'
    r'if\s*\(bl\)\s*\{\s*mainHandProgress\s*=\s*Math\.max\(mainHandProgress,\s*vanillaSwingProgress\);\s*\}\s*'
    r'else\s*\{\s*offHandProgress\s*=\s*Math\.max\(offHandProgress,\s*vanillaSwingProgress\);\s*\}\s*'
    r'this\.mainHandSwingProgress\s*=\s*mainHandProgress;\s*'
    r'this\.offHandSwingProgress\s*=\s*offHandProgress;\s*'
    r'swingProgress\s*=\s*bl\s*\?\s*mainHandProgress\s*:\s*offHandProgress;',
    re.S,
)
match = pattern.search(text)
if match:
    indent_start = text.rfind('\n', 0, match.start()) + 1
    indent = text[indent_start:match.start()]
    replacement = custom_swing.replace('\n', '\n' + indent)
    text = text[:match.start()] + replacement + text[match.end():]
elif 'Math.max(mainHandProgress' in text or 'vanillaSwingProgress' in text:
    raise RuntimeError('Fast swing fallback exists but did not match safely')

# Remove a previous framing correction if this script is applied repeatedly.
text = re.sub(
    r'\s*matrices\.translate\(-0\.(?:14|30)F \* l,\s*-?0\.0[34]F,\s*-0\.(?:10|24)F\);\s*'
    r'(?:matrices\.scale\(0\.86F,\s*0\.86F,\s*0\.86F\);\s*)?',
    '\n',
    text,
    count=1,
)

# Stronger 26.2 first-person framing: pull both hands toward the centre,
# slightly down and farther away, then reduce the complete arm/item scene.
scene_start = text.find('this.scenePoseMain(')
if scene_start < 0:
    raise RuntimeError('scenePoseMain call not found')
next_push = text.find('matrices.pushPose();', scene_start)
if next_push < 0:
    raise RuntimeError('Pose push after scenePoseMain not found')
line_start = text.rfind('\n', 0, next_push) + 1
indent = text[line_start:next_push]
correction = (
    f'{indent}matrices.translate(-0.30F * l, -0.04F, -0.24F);\n'
    f'{indent}matrices.scale(0.86F, 0.86F, 0.86F);\n'
)
text = text[:line_start] + correction + text[line_start:]
held.write_text(text, encoding='utf-8')
