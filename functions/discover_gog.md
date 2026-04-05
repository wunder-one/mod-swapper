This module will check the windows regitry 

The registry location
HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\


**How you'd walk it in Python**

Use winreg.EnumKey() to iterate over all subkeys:

Generated Code, need to review:

```python
import winreg
import re

UNINSTALL_PATH = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
GOG_KEY_PATTERN = re.compile(r"^(\d+)_is1$")

with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALL_PATH) as uninstall_key:
    index = 0
    while True:
        try:
            subkey_name = winreg.EnumKey(uninstall_key, index)
            # check if it matches GOG's pattern
            match = GOG_KEY_PATTERN.match(subkey_name)
            if match:
                game_id = match.group(1)
                # open the subkey and read values
            index += 1
        except OSError:
            break  # no more subkeys
```


`EnumKey` gives you the *name* of the subkey, not its contents. You then need a second `OpenKey` call to read the values inside it. A common mistake is trying to read `InstallLocation` from the parent key — it's not there, it's one level down.

**Filtering to BG3 specifically**

You'd need BG3's GOG product ID to match against `game_id`. That's worth looking up — it's different from the Steam App ID. Once you have it, you can either filter during the loop or collect all GOG games and let the caller search by ID.

**Why this approach is actually better for your use case**

Since you only care about one specific game, you could also just construct the key name directly if you know the GOG ID — `1207664643_is1` or whatever it is — and skip the enumeration entirely. 

