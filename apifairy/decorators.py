from functools import wraps

from flask import Response
from webargs.flaskparser import use_args


def _annotate(f, **kwargs):
    if not hasattr(f, '_spec'):
        f._spec = {}
    for key, value in kwargs.items():
        f._spec[key] = value


def authenticate(auth, **kwargs):
    def decorator(f):
        roles = kwargs.get('role')
        if not isinstance(roles, list):
            roles = [roles]
        _annotate(f, auth=auth, roles=roles)
        return auth.login_required(**kwargs)(f)
    return decorator


def arguments(schema, location='query'):
    def decorator(f):
        if not hasattr(f, '_spec') or f._spec.get('args') is None:
            _annotate(f, args=[])
        f._spec['args'].append((schema, location))
        return use_args(schema, location=location)(f)
    return decorator


def body(schema):
    def decorator(f):
        _annotate(f, body=schema)
        return use_args(schema, location='json')(f)
    return decorator


def response(schema, status_code=200, description=None):
    def decorator(f):
        _annotate(f, response=schema, status_code=status_code,
                  description=description)

        @wraps(f)
        def _response(*args, **kwargs):
            rv = f(*args, **kwargs)
            if isinstance(rv, Response):  # pragma: no cover
                raise RuntimeError(
                    'The @response decorator cannot handle Response objects.')
            if isinstance(rv, tuple):
                json = schema.jsonify(rv[0])
                if len(rv) == 2:
                    if not isinstance(rv[1], int):
                        rv = (json, status_code, rv[1])
                    else:
                        rv = (json, rv[1])
                elif len(rv) >= 3:
                    rv = (json, rv[1], rv[2])
                else:
                    rv = json
                return rv
            else:
                return schema.jsonify(rv), status_code
        return _response
    return decorator


def other_responses(responses):
    def decorator(f):
        _annotate(f, other_responses=responses)
        return f
    return decorator