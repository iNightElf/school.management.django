"""
WSGI middleware that adds CORS headers.
The alwaysdata alproxy strips Access-Control-* headers from Django responses,
so we inject them here at the WSGI level as a workaround.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

_django_app = get_wsgi_application()

ALLOWED_ORIGINS = [
    'https://iNightElf.github.io',
    'http://localhost:5173',
    'http://localhost:3000',
]


def application(environ, start_response):
    origin = environ.get('HTTP_ORIGIN', '')
    method = environ.get('REQUEST_METHOD', '')

    if origin in ALLOWED_ORIGINS:
        def custom_start_response(status, headers, exc_info=None):
            header_dict = dict(headers)

            if 'access-control-allow-origin' not in header_dict:
                headers.append(('Access-Control-Allow-Origin', origin))
                headers.append(('Access-Control-Allow-Credentials', 'true'))

                if method == 'OPTIONS':
                    headers.append(('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS'))
                    headers.append(('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With'))
                    headers.append(('Access-Control-Max-Age', '86400'))

            return start_response(status, headers, exc_info)

        return _django_app(environ, custom_start_response)

    return _django_app(environ, start_response)
