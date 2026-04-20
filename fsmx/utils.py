
def always_true[C](ctx: C) -> bool:
    """
    *So this function is always true.*

    This function is only used for debugging purposes, it always returns True and can be used as a default guard. 
 
    ```python
    lambda ctx: True
    ```

    Args:
        ctx (C): The context passed to the guard function.
    
    Returns:
        bool: Always returns True.
    """
    return True
