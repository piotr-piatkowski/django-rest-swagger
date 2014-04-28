from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework_swagger import SWAGGER_SETTINGS
from pprint import pformat

class APIDocView(APIView):

    def initial(self, request, *args, **kwargs):
        self.permission_classes = (self.get_permission_class(request),)
        protocol = "https" if request.is_secure() else "http"

        if 'HTTP_X_FORWARDED_HOST' in request.META:
            host_list = request.META['HTTP_X_FORWARDED_HOST'].split(',')
            host = host_list[0].strip()
        else:
            host = request.get_host()

        self.base_uri = "%s://%s" % (protocol, host)
        self.base_uri = self.base_uri.rstrip('/')

        return super(APIDocView, self).initial(request, *args, **kwargs)

    def get_permission_class(self, request):
        if SWAGGER_SETTINGS['is_superuser'] and not request.user.is_superuser:
            return IsAdminUser
        if SWAGGER_SETTINGS['is_authenticated'] and not request.user.is_authenticated():
            return IsAuthenticated

        return AllowAny
