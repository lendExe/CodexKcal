from pathlib import Path

path = Path('hmi-source/mod/src/main/java/com/holdmylua/source/lua_runtime/LuaScriptCache.java')
text = path.read_text(encoding='utf-8')
old = '''          } catch (Exception var21) {
             System.err.println("[HoldMyItems] Lua runtime error: " + var21.getMessage());'''
new = '''          } catch (Exception var21) {
             System.err.println("[HoldMyItems] Lua runtime error: " + var21.getMessage());
             var21.printStackTrace();'''
if old not in text:
    raise RuntimeError('Lua runtime catch block not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
