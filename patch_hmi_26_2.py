from pathlib import Path
import re

root = Path('hmi-source/mod/src/main/java')
for path in root.rglob('*.java'):
    text = path.read_text(encoding='utf-8')
    text = text.replace('.getMainCamera()', '.mainCamera()')
    text = text.replace(
        'Minecraft.getInstance().getToastManager()',
        'Minecraft.getInstance().gui.toastManager()'
    )
    path.write_text(text, encoding='utf-8')

held = root / 'com/holdmylua/source/mixin/render/HeldItemRendererMixin.java'
held_text = held.read_text(encoding='utf-8')
held_text, removed = re.subn(
    r'\n\s*@Shadow\s*\n\s*protected abstract void renderArmWithItem\(.*?\n\s*\);\s*\n',
    '\n',
    held_text,
    count=1,
    flags=re.S,
)
if removed != 1:
    raise RuntimeError(f'Expected to remove one obsolete renderArmWithItem shadow, removed {removed}')
held.write_text(held_text, encoding='utf-8')

item = root / 'com/holdmylua/source/mixin/render/ItemRendererMixin.java'
item.write_text(r'''package com.holdmylua.source.mixin.render;

import com.holdmylua.source.global.GlobalsStorage;
import com.holdmylua.source.global.item_model.ItemModelContext;
import com.holdmylua.source.global.item_model.ItemModelStorage;
import com.holdmylua.source.lua_runtime.ModelScriptCache;
import com.holdmylua.source.lua_runtime.ScriptHolder;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.QuadInstance;
import com.mojang.blaze3d.vertex.SheetedDecalTextureGenerator;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.MatrixUtil;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.feature.FeatureFrameContext;
import net.minecraft.client.renderer.feature.ItemFeatureRenderer;
import net.minecraft.client.renderer.feature.RenderTypeFeatureRenderer;
import net.minecraft.client.renderer.item.ItemStackRenderState.FoilType;
import net.minecraft.client.renderer.rendertype.OutputTarget;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.jspecify.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ItemFeatureRenderer.class)
public abstract class ItemRendererMixin extends RenderTypeFeatureRenderer<ItemFeatureRenderer.Submit> {
   @Inject(method = "buildGroup", at = @At("HEAD"), cancellable = true)
   private void hmi$buildGroup(FeatureFrameContext frameContext, List<ItemFeatureRenderer.Submit> submits, CallbackInfo ci) {
      Map<ItemFeatureRenderer.Submit, ItemModelContext> contexts = new IdentityHashMap<>();
      for (ItemFeatureRenderer.Submit submit : submits) {
         ItemModelContext context = null;
         if (hmi$isFirstPersonHand(submit)) {
            context = ItemModelStorage.get();
            contexts.put(submit, context);
         }
         hmi$renderPass(submit, false, context);
      }
      for (ItemFeatureRenderer.Submit submit : submits) {
         hmi$renderPass(submit, true, contexts.get(submit));
      }
      ci.cancel();
   }

   @Unique
   private static boolean hmi$isFirstPersonHand(ItemFeatureRenderer.Submit submit) {
      ItemDisplayContext type = submit.displayContext();
      return (type == ItemDisplayContext.THIRD_PERSON_LEFT_HAND || type == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND)
         && Minecraft.getInstance().options.getCameraType().isFirstPerson();
   }

   @Unique
   private void hmi$renderPass(ItemFeatureRenderer.Submit submit, boolean foilPass, @Nullable ItemModelContext context) {
      boolean animated = context != null;
      if (animated) {
         AbstractClientPlayer player = context.player != null ? context.player : Minecraft.getInstance().player;
         ItemStack item = context.item;
         ScriptHolder.itemModelCache.executeModel(context, item, player, GlobalsStorage.modelPartAnimator);
         for (ModelScriptCache cache : ScriptHolder.itemModelAddonsCache) {
            cache.executeModel(context, item, player, GlobalsStorage.modelPartAnimator);
         }
      }

      QuadInstance instance = new QuadInstance();
      instance.setLightCoords(submit.lightCoords());
      instance.setOverlayCoords(submit.overlayCoords());
      PoseStack posed = new PoseStack();
      int index = 0;

      for (BakedQuad quad : submit.quads()) {
         BakedQuad.MaterialInfo material = quad.materialInfo();
         RenderType renderType = material.itemRenderType();
         posed.pushPose();
         posed.last().set(submit.pose());
         if (animated) GlobalsStorage.modelPartAnimator.applyPoses(index, posed);
         PoseStack.Pose pose = posed.last();

         if (foilPass) {
            if (submit.foilType() != FoilType.NONE) {
               instance.setColor(-1);
               VertexConsumer buffer = this.getVertexBuilder(hmi$getFoilRenderType(renderType));
               if (submit.foilType() == FoilType.SPECIAL) {
                  buffer = new SheetedDecalTextureGenerator(buffer, hmi$computeFoilPose(submit.displayContext(), pose), 0.0078125F);
               }
               buffer.putBakedQuad(pose, quad, instance);
            }
         } else if (submit.outlineColor() != 0) {
            RenderType outline = renderType.outline().orElse(null);
            if (outline != null) {
               instance.setColor(submit.outlineColor());
               this.getVertexBuilder(outline).putBakedQuad(pose, quad, instance);
            }
         } else {
            int tint = material.isTinted() && material.tintIndex() >= 0 && material.tintIndex() < submit.tintLayers().length
               ? submit.tintLayers()[material.tintIndex()] : -1;
            instance.setColor(tint);
            this.getVertexBuilder(renderType).putBakedQuad(pose, quad, instance);
         }
         posed.popPose();
         index++;
      }
      if (animated) GlobalsStorage.modelPartAnimator.clear();
   }

   @Unique
   private static RenderType hmi$getFoilRenderType(RenderType renderType) {
      boolean transparent = Minecraft.getInstance().gameRenderer.gameRenderState().useShaderTransparency()
         && renderType.outputTarget() == OutputTarget.ITEM_ENTITY_TARGET;
      return transparent ? RenderTypes.glintTranslucent() : RenderTypes.glint();
   }

   @Unique
   private static PoseStack.Pose hmi$computeFoilPose(ItemDisplayContext type, PoseStack.Pose pose) {
      PoseStack.Pose result = pose.copy();
      if (type == ItemDisplayContext.GUI) MatrixUtil.mulComponentWise(result.pose(), 0.5F);
      else if (type.firstPerson()) MatrixUtil.mulComponentWise(result.pose(), 0.75F);
      return result;
   }
}
''', encoding='utf-8')

particle = root / 'com/holdmylua/source/patricles/render/ParticleRenderLayers.java'
particle.write_text(r'''package com.holdmylua.source.patricles.render;

import com.holdmylua.source.mixin.render.RenderTypeInvoker;
import com.mojang.blaze3d.pipeline.BlendFunction;
import com.mojang.blaze3d.pipeline.ColorTargetState;
import com.mojang.blaze3d.pipeline.DepthStencilState;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.platform.CompareOp;
import java.util.function.Function;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.rendertype.RenderSetup;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Util;

public class ParticleRenderLayers {
   static final RenderPipeline ADDITIVE_PARTICLE = RenderPipelines.register(
      RenderPipeline.builder(RenderPipelines.GUI_TEXTURED_SNIPPET)
         .withLocation("pipeline/additive_particle_effect")
         .withColorTargetState(new ColorTargetState(BlendFunction.LIGHTNING))
         .withDepthStencilState(new DepthStencilState(CompareOp.ALWAYS_PASS, false))
         .build()
   );
   private static final Function<Identifier, RenderType> ADDITIVE_PARTICLE_LAYER = Util.memoize(
      texture -> RenderTypeInvoker.hmi$create("hmi_additive_particle", RenderSetup.builder(ADDITIVE_PARTICLE).withTexture("Sampler0", texture).createRenderSetup())
   );
   public static RenderType additiveParticle(Identifier texture) {
      return ADDITIVE_PARTICLE_LAYER.apply(texture);
   }
}
''', encoding='utf-8')
