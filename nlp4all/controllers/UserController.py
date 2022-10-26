"""User / Login related controller."""

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database.

    Args:
        user_id (int): The id of the user to load.

    Returns:
       User: User object.
    """
    return User.query.get(int(user_id))