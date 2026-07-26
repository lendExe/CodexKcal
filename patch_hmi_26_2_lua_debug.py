from pathlib import Path

path = Path('hmi-source/mod/src/main/java/com/holdmylua/source/lua_runtime/LuaScriptCache.java')
text = path.read_text(encoding='utf-8')
needle = 'System.err.println("[HoldMyItems] Lua runtime error: " + var21.getMessage());'
replacement = needle + '\n             var21.printStackTrace();'
if 'var21.printStackTrace();' not in text:
    if needle not in text:
        raise RuntimeError('Lua runtime error log statement not found')
    text = text.replace(needle, replacement, 1)
path.write_text(text, encoding='utf-8')
