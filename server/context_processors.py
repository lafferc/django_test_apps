from django.conf import settings

def selected_settings(request):
    return {'APP_VERSION_NUMBER': settings.APP_VERSION_NUMBER}
