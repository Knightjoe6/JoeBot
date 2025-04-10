from discord import Interaction, app_commands

def check_if_is_labra(interaction: Interaction):
    return interaction.user.id == 397664205798637568

def check_if_is_admin_or_moderator(interaction: Interaction):
    """Return whether the user is an Admin or a Moderator"""
    # Replace 'admin' and 'moderator' with the exact names of your roles
    allowed_roles = ['Admin', 'Mods']
    user_roles = [role.name for role in interaction.user.roles]
    if any(role in user_roles for role in allowed_roles):
        return True
    return False