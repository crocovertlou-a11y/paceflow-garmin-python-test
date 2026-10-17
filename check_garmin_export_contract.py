
import importlib.metadata
import inspect
from garminconnect import Garmin

print("=== Garmin export contract ===")
print("Version:", importlib.metadata.version("garminconnect"))

client = Garmin().client

for name in ("loads", "dumps", "load", "dump"):
    method = getattr(client, name, None)
    print(f"{name}: {callable(method)}")
    if callable(method):
        print("Signature:", inspect.signature(method))

print("DONE - No Garmin login attempted.")
