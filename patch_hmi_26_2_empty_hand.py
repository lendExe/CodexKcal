from pathlib import Path

lua = Path(
    'hmi-source/mod/src/main/resources/resourcepacks/pack_test/'
    'assets/minecraft/holdmyitems/hand_pose.lua'
)
text = lua.read_text(encoding='utf-8')

anchor = 'local swingOverall = M:sin(context.swingProgress * 3.14)'
anchor_pos = text.find(anchor)
if anchor_pos < 0:
    raise RuntimeError('Swing section anchor not found')

start = text.find('if I:isEmpty(context.item) then', anchor_pos)
end_marker = 'elseif I:isIn(context.item, Tags:getVanillaTag("pickaxes")) then'
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError('Empty-hand swing block not found')

replacement = '''if I:isEmpty(context.item) then
-- Minecraft 26.2 renders first-person arms closer to the camera.  The old
-- empty-hand swing had several unscaled Y/Z movements, which pushed the arm
-- outside the screen while punching or breaking blocks.  Scale the complete
-- empty-hand motion while leaving every held-item animation untouched.
local emptySwingScale = (context.blockBreaking and 0.30) or 0.46
M:translate(mat,
    -0.15 * l * swing * emptySwingScale,
    (0.1 * swingRiseS + 0.33 * swing + 0.05 * swing_rot + 0.14 * swingRise) * emptySwingScale,
    (-0.1 * swingRiseS - 0.4 * swing_hit - 0.2 * swing) * emptySwingScale)
M:rotateX(mat, -10 * swingRise * emptySwingScale)
M:moveZ(mat, 0.15 * swing_rot * emptySwingScale)
M:rotateX(mat, -20 * swing * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateX(mat, -7 * swing_hit * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateX(mat, 10 * swing_rot * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateZ(mat, 20 * l * swing * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateY(mat, 5 * l * swing * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateX(mat, -5 * swingRiseS * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateZ(mat, 10 * l * swingRiseS * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateY(mat, 5 * l * swingRiseS * emptySwingScale, 0.3 * l, -0.4, 0)
M:rotateY(mat, 15 * l * swing_hit * emptySwingScale, 0.3 * l, -0.4, 0)
'''

text = text[:start] + replacement + text[end:]
lua.write_text(text, encoding='utf-8')
