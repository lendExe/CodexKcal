from pathlib import Path

root = Path('hmi-source/mod/src/main/java')

# Slow all time-based Lua transitions to 65% of their previous speed.
game_renderer = root / 'com/holdmylua/source/mixin/client/GameRendererMixin.java'
text = game_renderer.read_text(encoding='utf-8')
old = 'LuaTestHMI.deltaTime = Math.min(elapsed, 0.05F);'
new = 'LuaTestHMI.deltaTime = Math.min(elapsed * 0.65F, 0.05F);'
if old not in text:
    raise RuntimeError('Delta-time assignment not found')
text = text.replace(old, new, 1)
game_renderer.write_text(text, encoding='utf-8')

held = root / 'com/holdmylua/source/mixin/render/HeldItemRendererMixin.java'
text = held.read_text(encoding='utf-8')

# Remove the vanilla-progress fallback. It made the custom 10-tick HMI swing
# snap to Minecraft's shorter attack animation and therefore look too fast.
fast_swing = '''            float vanillaSwingProgress = swingProgress;
             float mainHandProgress = accessor.hMI5_0$getMainHandSwingProgress(tickProgress);
             float offHandProgress = accessor.hMI5_0$getOffHandSwingProgress(tickProgress);
             if (bl) {
                mainHandProgress = Math.max(mainHandProgress, vanillaSwingProgress);
             } else {
                offHandProgress = Math.max(offHandProgress, vanillaSwingProgress);
             }
             this.mainHandSwingProgress = mainHandProgress;
             this.offHandSwingProgress = offHandProgress;
             swingProgress = bl ? mainHandProgress : offHandProgress;'''
custom_swing = '''            float mainHandProgress = accessor.hMI5_0$getMainHandSwingProgress(tickProgress);
             this.mainHandSwingProgress = mainHandProgress;
             float offHandProgress = accessor.hMI5_0$getOffHandSwingProgress(tickProgress);
             this.offHandSwingProgress = offHandProgress;
             swingProgress = bl ? mainHandProgress : offHandProgress;'''
if fast_swing not in text:
    raise RuntimeError('Fast swing fallback block not found')
text = text.replace(fast_swing, custom_swing, 1)

# Minecraft 26.2's first-person projection makes the old HMI framing sit too
# close to the screen edges. Insert the correction after scenePoseMain and
# before the arm/item branches without depending on whitespace formatting.
scene_start = text.find('this.scenePoseMain(')
if scene_start < 0:
    raise RuntimeError('scenePoseMain call not found')
next_push = text.find('matrices.pushPose();', scene_start)
if next_push < 0:
    raise RuntimeError('Pose push after scenePoseMain not found')
line_start = text.rfind('\n', 0, next_push) + 1
indent = text[line_start:next_push]
correction = f'{indent}matrices.translate(-0.14F * l, 0.03F, -0.10F);\n'
text = text[:line_start] + correction + text[line_start:]
held.write_text(text, encoding='utf-8')
