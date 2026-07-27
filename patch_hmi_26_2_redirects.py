from pathlib import Path

path = Path('hmi-source/mod/src/main/java/com/holdmylua/source/mixin/render/HeldItemRendererMixin.java')
text = path.read_text(encoding='utf-8')
old_method = 'renderHandsWithItems(FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/player/LocalPlayer;I)V'
new_method = 'submitHandsWithItems(FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/player/LocalPlayer;I)V'
old_target = 'Lnet/minecraft/client/renderer/ItemInHandRenderer;renderArmWithItem('
new_target = 'Lnet/minecraft/client/renderer/ItemInHandRenderer;submitArmWithItem('
if old_method not in text:
    raise RuntimeError('Old renderHandsWithItems target not found')
if old_target not in text:
    raise RuntimeError('Old renderArmWithItem target not found')
text = text.replace(old_method, new_method, 1)
text = text.replace(old_target, new_target, 1)
path.write_text(text, encoding='utf-8')
