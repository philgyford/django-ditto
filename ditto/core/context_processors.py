import warnings


def ditto(request):
    """
    Deprecated.
    """
    warnings.warn("The ditto context_processor is no longer used.", DeprecationWarning)
    return {}
