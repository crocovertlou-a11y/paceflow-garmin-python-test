"""Offline Garmin export contract probe; never uses credentials or prints token data."""
import importlib.metadata
import inspect
from garminconnect import Garmin


def inspect_contract():
    version = importlib.metadata.version('garminconnect')
    instance = Garmin()
    client = instance.client
    result = {'version': version}
    for method in ('loads', 'dumps', 'load', 'dump'):
        obj = getattr(client, method, None)
        result[method] = callable(obj)
        if callable(obj):
            try:
                result[method + '_signature'] = str(inspect.signature(obj))
            except (ValueError, TypeError):
                result[method + '_signature'] = 'unavailable'
    return result


if __name__ == '__main__':
    print('=== Offline Garmin session export contract ===')
    for key, value in inspect_contract().items():
        print(f'{key}: {value}')
    print('No login, no network calls, no token contents.')
