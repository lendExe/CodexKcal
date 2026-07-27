from pathlib import Path
import re

root = Path('hmi-source/mod/src/main/java')

# Keep animations slower than the raw 26.2 timing.
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

# Remove every previous global framing experiment. Those affected both the arm
# and the held item and made the hands move toward the centre of the camera.
text = re.sub(
    r'^[ \t]*matrices\.translate\(-0\.(?:14|30)F \* l,\s*-?0\.0[34]F,\s*-0\.(?:10|24|28)F\);\s*\n'
    r'(?:^[ \t]*matrices\.scale\(0\.86F,\s*0\.86F,\s*0\.86F\);\s*\n)?',
    '',
    text,
    count=1,
    flags=re.M,
)

# Apply a conservative correction ONLY to the player-arm branch. The held item
# keeps the original HMI matrices. Positive X*l sends each arm toward its own
# screen edge; negative Y/Z moves the arm lower and farther from the camera.
scene_start = text.find('this.scenePoseMain(')
if scene_start < 0:
    raise RuntimeError('scenePoseMain call not found')
arm_pose = text.find('this.mainHandPose(', scene_start)
if arm_pose < 0:
    raise RuntimeError('mainHandPose call not found')
arm_push = text.rfind('matrices.pushPose();', scene_start, arm_pose)
if arm_push < 0:
    raise RuntimeError('Arm pose push not found')
line_end = text.find('\n', arm_push)
indent_start = text.rfind('\n', 0, arm_push) + 1
indent = text[indent_start:arm_push]
arm_correction = f'{indent}matrices.translate(0.10F * l, -0.14F, -0.16F);\n'
if 'matrices.translate(0.10F * l, -0.14F, -0.16F);' not in text:
    text = text[:line_end + 1] + arm_correction + text[line_end + 1:]

held.write_text(text, encoding='utf-8')
