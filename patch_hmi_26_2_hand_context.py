from pathlib import Path

root = Path('hmi-source/mod/src/main/java')

storage = root / 'com/holdmylua/source/global/item_model/ItemModelStorage.java'
storage.write_text(r'''package com.holdmylua.source.global.item_model;

import com.holdmylua.source.LuaTestHMI;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.Items;

public class ItemModelStorage {
   private static final List<ItemModelContext> data = new ArrayList<>();

   public static void addData(ItemModelContext info, ItemStack item) {
      if (!item.isEmpty() && item.getUseAnimation() != ItemUseAnimation.BLOCK && item.getUseAnimation() != ItemUseAnimation.TRIDENT) {
         data.add(info);
      }
   }

   public static ItemModelContext getForArm(boolean rightArm) {
      for (int index = 0; index < data.size(); index++) {
         ItemModelContext context = data.get(index);
         if (context.bl == rightArm) {
            data.remove(index);
            return context;
         }
      }
      return get();
   }

   public static ItemModelContext get() {
      if (!data.isEmpty()) {
         return data.removeFirst();
      }
      return new ItemModelContext(
         false,
         0.0F,
         Minecraft.getInstance().player,
         InteractionHand.MAIN_HAND,
         false,
         LuaTestHMI.deltaTime,
         0.0F,
         0.0F,
         0.0F,
         false,
         false,
         false,
         false,
         false,
         false,
         Items.AIR.getDefaultInstance()
      );
   }

   public static void clear() {
      data.clear();
   }
}
''', encoding='utf-8')

mixin = root / 'com/holdmylua/source/mixin/render/ItemRendererMixin.java'
text = mixin.read_text(encoding='utf-8')
old = 'context = ItemModelStorage.get();'
new = 'context = ItemModelStorage.getForArm(submit.displayContext() == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND);'
if old not in text:
    raise RuntimeError('Item model context retrieval call not found')
text = text.replace(old, new, 1)
mixin.write_text(text, encoding='utf-8')
