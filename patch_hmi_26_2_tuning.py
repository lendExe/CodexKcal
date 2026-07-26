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
# close to the screen edges. Pull each hand toward the centre and slightly
# farther from the camera before rendering both the arm and held item.
anchor = '''             this.particles
          );
          matrices.pushPose();
          this.mainHandPose('''
replacement = '''             this.particles
          );
          matrices.translate(-0.14F * l, 0.03F, -0.10F);
          matrices.pushPose();
          this.mainHandPose('''
if anchor not in text:
    raise RuntimeError('Hand framing insertion point not found')
text = text.replace(anchor, replacement, 1)
held.write_text(text, encoding='utf-8')
