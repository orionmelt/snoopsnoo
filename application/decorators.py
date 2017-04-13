"""

Decorators for URL handlers

"""

from functools import wraps
from google.appengine.api import users
from flask import redirect, request, abort


def login_required(func):
  """Requires standard login credentials"""
  @wraps(func)
  def decorated_view(*args, **kwargs):
    """
    Redirects to login page if user is not logged in.
    """
    if not users.get_current_user():
      return redirect(users.create_login_url(request.url))
    return func(*args, **kwargs)
  return decorated_view


def admin_required(func):
  """Requires App Engine admin credentials"""
  @wraps(func)
  def decorated_view(*args, **kwargs):
    """
    Returns 401 Unauthorized if logged in user is not an admin.
    """
    if users.get_current_user():
      if not users.is_current_user_admin():
        abort(401)  # Unauthorized
      return func(*args, **kwargs)
    return redirect(users.create_login_url(request.url))
  return decorated_view
