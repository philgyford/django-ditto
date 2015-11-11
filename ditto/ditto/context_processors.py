from .apps import ditto_apps

def ditto(request):
    return {
        'enabled_apps': ditto_apps.enabled(),
    }

