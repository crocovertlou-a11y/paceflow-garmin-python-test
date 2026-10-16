"""Read-only offline inspection of garminconnect tokenstore implementation."""
import inspect
import importlib.metadata
from garminconnect import Garmin

print('=== TOKENSTORE DIAGNOSTIC (no login, no network, no credentials) ===')
print('garminconnect:', importlib.metadata.version('garminconnect'))
for name in ('__init__', 'login', 'logout'):
    method = getattr(Garmin, name)
    print(f'\n=== Garmin.{name}{inspect.signature(method)} ===')
    try:
        source = inspect.getsource(method).splitlines()
    except (OSError, TypeError) as e:
        print('Source unavailable:', type(e).__name__)
        continue
    terms = ('tokenstore', 'oauth', 'dump', 'load', 'session', 'login', 'garth', 'token')
    for n, line in enumerate(source, 1):
        if any(term in line.lower() for term in terms):
            # Source-code lines only: no invocation or credentials.
            print(f'{n:3}: {line[:240]}')
print('\n=== Related instance methods ===')
for name in sorted(dir(Garmin)):
    if any(t in name.lower() for t in ('token', 'session', 'auth', 'login')):
        value = getattr(Garmin, name)
        print(name, inspect.signature(value) if callable(value) else '(attribute)')
print('\nDONE. No authentication attempted.')
