from pathlib import Path

root = Path('hmi-source/mod/src/main/java')

# Minecraft 26.2 separates frame extraction/update/render more aggressively.
# Use a monotonic high-resolution clock and the render method's own
# advanceGameTime flag, rather than a float GLFW timer + Minecraft.isPaused().
game_renderer = root / 'com/holdmylua/source/mixin/client/GameRendererMixin.java'
game_renderer.write_text(r'''package com.holdmylua.source.mixin.client;

import com.holdmylua.source.LuaTestHMI;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.renderer.GameRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(GameRenderer.class)
public class GameRendererMixin {
   @Unique
   private static long hmi$lastFrameNanos = System.nanoTime();

   @Inject(method = "render", at = @At("HEAD"))
   private void hmi$updateDeltaTime(DeltaTracker deltaTracker, boolean advanceGameTime, CallbackInfo ci) {
      long now = System.nanoTime();
      float elapsed = (now - hmi$lastFrameNanos) / 1_000_000_000.0F;
      hmi$lastFrameNanos = now;

      if (!advanceGameTime || !Float.isFinite(elapsed) || elapsed < 0.0F) {
         LuaTestHMI.deltaTime = 0.0F;
      } else {
         LuaTestHMI.deltaTime = Math.min(elapsed, 0.05F);
      }
   }
}
''', encoding='utf-8')

# Keep HMI's independent hand counters, but do not throw away Minecraft 26.2's
# verified per-hand attack interpolation. This prevents frozen attack animation
# if a custom swing event is delayed or intercepted by another client mod.
held = root / 'com/holdmylua/source/mixin/render/HeldItemRendererMixin.java'
text = held.read_text(encoding='utf-8')
old = '''            float mainHandProgress = accessor.hMI5_0$getMainHandSwingProgress(tickProgress);
            this.mainHandSwingProgress = mainHandProgress;
            float offHandProgress = accessor.hMI5_0$getOffHandSwingProgress(tickProgress);
            this.offHandSwingProgress = offHandProgress;
            swingProgress = bl ? mainHandProgress : offHandProgress;'''
new = '''            float vanillaSwingProgress = swingProgress;
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
if old not in text:
    raise RuntimeError('Held item swing-progress block was not found')
text = text.replace(old, new, 1)
held.write_text(text, encoding='utf-8')
