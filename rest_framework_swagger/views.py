import json
import os
import subprocess
import socket

from django.views.generic import View
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, RequestContext
from django.core.exceptions import PermissionDenied

from rest_framework.views import Response
from rest_framework_swagger.urlparser import UrlParser
from rest_framework_swagger.apidocview import APIDocView
from rest_framework.renderers import JSONRenderer
from rest_framework_swagger.docgenerator import DocumentationGenerator

from rest_framework_swagger import SWAGGER_SETTINGS


class SwaggerUIView(APIDocView):

    def get(self, request, *args, **kwargs):

        if not self.has_permission(request):
            raise PermissionDenied()

        template_name = "rest_framework_swagger/index.html"
        discovery_url = "{}{}docs/api-docs/".format(
                    self.base_uri, SWAGGER_SETTINGS.get('api_path', '/'))
        data = {
            'swagger_settings': {
                'discovery_url': discovery_url,
                'api_key': SWAGGER_SETTINGS.get('api_key', ''),
                'enabled_methods': mark_safe(
                    json.dumps( SWAGGER_SETTINGS.get('enabled_methods')))
            },
            'release_info': self.get_git_info(),
        }
        response = render_to_response(template_name, RequestContext(request, data))

        return response

    def has_permission(self, request):
        if SWAGGER_SETTINGS.get('is_superuser') and not request.user.is_superuser:
            return False

        if SWAGGER_SETTINGS.get('is_authenticated') and not request.user.is_authenticated():
            return False

        return True

    def get_git_info(self):
        module_dir = os.path.dirname(__file__)
        root_dir = os.path.abspath("{}/../..".format(module_dir))

        desc = os.path.join(root_dir, 'git-desc')
        if os.path.exists(desc):
            descr = open(desc).read()
        else:
            descr = subprocess.check_output(
                ['git', 'describe', '--tags', 'HEAD'],
                cwd=root_dir,
                stderr=subprocess.STDOUT,
            )
        descr = descr.strip()
        hostname = socket.gethostname()
        return "{}@{}".format(descr, hostname)


class SwaggerResourcesView(APIDocView):

    renderer_classes = (JSONRenderer,)

    def get(self, request):
        apis = []
        resources = self.get_resources()

        for path in resources:
            apis.append({
                'path': "%s" % path,
            })

        return Response({
            'apiVersion': SWAGGER_SETTINGS.get('api_version', ''),
            'swaggerVersion': '1.2',
            'basePath': "{}{}".format(self.base_uri, request.path),
            'apis': apis
        })

    def get_resources(self):
        urlparser = UrlParser()
        apis = urlparser.get_apis(exclude_namespaces=SWAGGER_SETTINGS.get('exclude_namespaces'))
        resources = urlparser.get_top_level_apis(apis)

        return resources


class SwaggerApiView(APIDocView):

    renderer_classes = (JSONRenderer,)

    def get(self, request, path):
        apis = self.get_api_for_resource(path)
        generator = DocumentationGenerator()

        return Response({
            'apis': generator.generate(apis),
            'models': generator.get_models(apis),
            'basePath': self.base_uri,
        })

    def get_api_for_resource(self, filter_path):
        urlparser = UrlParser()
        return urlparser.get_apis(filter_path=filter_path)
