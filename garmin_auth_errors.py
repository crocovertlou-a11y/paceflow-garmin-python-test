"""Conservative classification of Garmin login failures.

Only explicit credential rejection is retryable. Do not log exception strings
(they may contain sensitive endpoints or account details).
"""


def classify_login_error(exc):
    message = str(exc).lower()
    if any(term in message for term in (
        'rate limit', 'rate_limit', 'too many requests', '429',
        'preauthorized', 'throttl',
    )):
        return 'rate_limited'
    # Explicit credential failures only. Ambiguous 401s may be token/API errors.
    if any(term in message for term in (
        'invalid credentials', 'incorrect password', 'invalid password',
        'wrong password', 'bad credentials',
    )):
        return 'auth_failed'
    return 'uncertain'
