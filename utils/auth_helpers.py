"""Add to utils/helpers.py"""

def verify_user_account(user_context, logger_instance) -> bool:
    """
    Verify user has valid account selected.
    
    Args:
        user_context: User context object
        logger_instance: Logger instance for debugging
    
    Returns:
        True if account is valid, False otherwise
    """
    if not user_context.has_account():
        logger_instance.warning(
            f"User {user_context.user_id} has no account selected. "
            f"Credentials: {user_context.account_credentials}"
        )
        return False
    
    logger_instance.debug(
        f"User {user_context.user_id} account verified: "
        f"{user_context.account_name} (index={user_context.account_index})"
    )
    return True
  
