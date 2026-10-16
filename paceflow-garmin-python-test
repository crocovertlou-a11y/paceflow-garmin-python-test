
import inspect
import importlib.metadata
from garminconnect import Garmin

print("=== Garmin session compatibility ===")
print("garminconnect version:", importlib.metadata.version("garminconnect"))

for method_name in (
    "login",
    "logout",
    "get_activities",
    "get_activities_by_date",
):
    method = getattr(Garmin, method_name, None)
    if method is None:
        print(f"{method_name}: unavailable")
    else:
        print(f"{method_name}: {inspect.signature(method)}")

print("\n=== Session capabilities ===")

for name in ("garth", "session", "connectapi"):
    print(f"Garmin.{name}:", hasattr(Garmin, name))

try:
    import garth
    print("garth version:", importlib.metadata.version("garth"))
    print("garth client loads:", hasattr(garth, "Client"))
    print("garth dump:", hasattr(garth, "dump"))
    print("garth load:", hasattr(garth, "load"))
except ImportError as exc:
    print("garth unavailable:", exc)

print("\nDiagnostic completed without Garmin credentials.")
