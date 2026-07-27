from pathlib import Path
import re

java_root = Path('hmi-source/mod/src/main/java')
resource_root = Path('hmi-source/mod/src/main/resources/resourcepacks/pack_test/assets/minecraft/holdmyitems')

# Keep transitions slower than the raw 26.2 timing.
game_renderer = java_root / 'com/holdmylua/source/mixin/client/GameRendererMixin.java'
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

held = java_root / 'com/holdmylua/source/mixin/render/HeldItemRendererMixin.java'
text = held.read_text(encoding='utf-8')

# Remove the vanilla-progress fallback that made attacks snap too fast.
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

# Remove all previous framing experiments, including the arm-only correction.
text = re.sub(
    r'^[ \t]*matrices\.translate\((?:-0\.(?:14|30)F|0\.10F) \* l,\s*-?0\.(?:03|04|14)F,\s*-0\.(?:10|16|24|28)F\);\s*\n'
    r'(?:^[ \t]*matrices\.scale\(0\.86F,\s*0\.86F,\s*0\.86F\);\s*\n)?',
    '',
    text,
    flags=re.M,
)

# Apply one mild correction to the shared scene matrix. Both the arm and its
# held item inherit it, so the grip cannot separate again.
scene_start = text.find('this.scenePoseMain(')
if scene_start < 0:
    raise RuntimeError('scenePoseMain call not found')
next_push = text.find('matrices.pushPose();', scene_start)
if next_push < 0:
    raise RuntimeError('Shared branch pose push not found')
line_start = text.rfind('\n', 0, next_push) + 1
indent = text[line_start:next_push]
shared = 'matrices.translate(-0.10F * l, -0.04F, -0.10F);'
text = text[:line_start] + f'{indent}{shared}\n' + text[line_start:]
held.write_text(text, encoding='utf-8')

# Reduce attack amplitude at the common hand-scene level. This matrix is shared
# by the arm and item, preserving the grip while preventing off-screen swings.
hand_pose = resource_root / 'hand_pose.lua'
lua = hand_pose.read_text(encoding='utf-8')
values = {
    'regularSwing': '0.62',
    'swordSwing': '0.52',
    'pickaxeSwing': '0.65',
    'shovelSwing': '0.65',
    'generalSwing': '0.65',
    'axeSwing': '0.60',
    'tridentSwing': '0.65',
}
for name, value in values.items():
    lua, replaced = re.subn(
        rf'global\.{name}\s*=\s*[0-9.]+\s*;',
        f'global.{name} = {value};',
        lua,
        count=1,
    )
    if replaced != 1:
        raise RuntimeError(f'Could not tune {name}')
hand_pose.write_text(lua, encoding='utf-8')
