from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def role_required(*, admin):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if bool(request.user.is_staff) != admin:
                raise PermissionDenied("This dashboard is for another role.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
