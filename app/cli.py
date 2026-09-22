import re

import click
from flask.cli import with_appcontext

from .models import admin as admins

MIN_PASSWORD_LENGTH = 12
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def _check_password(username, password):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise click.ClickException(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters. "
            "A few random words joined together works well.")
    if password.lower() == username.lower():
        raise click.ClickException("Password must not be the same as the username.")


@click.command("create-admin")
@click.option("--username", prompt=True, help="3-32 letters, digits, dot, dash or underscore.")
@click.password_option()
@with_appcontext
def create_admin_command(username, password):
    """Create the admin account (asks for the password securely)."""
    if not _USERNAME_RE.match(username):
        raise click.ClickException("Username must be 3-32 characters: letters, digits, . _ -")
    _check_password(username, password)
    if admins.get_by_username(username):
        raise click.ClickException("That username already exists. "
                                   "Use reset-admin-password to change its password.")
    admins.create_admin(username, password)
    click.echo(f"Admin '{username}' created.")


@click.command("reset-admin-password")
@click.option("--username", prompt=True)
@click.password_option()
@with_appcontext
def reset_admin_password_command(username, password):
    """Set a new password for an existing admin and clear any lockout."""
    _check_password(username, password)
    if not admins.set_password(username, password):
        raise click.ClickException("No such admin.")
    click.echo(f"Password updated for '{username}'.")
