from django.http import HttpResponse

from lxml import etree
from rest_framework import status
from rest_framework.views import APIView

from projects.models import Project
from categories.models import Category
from contributions.serializers import ContributionSerializer

from serializer import ProjectFormSerializer, DataSerializer
from users.models import User


class EpiCollectProject(APIView):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        if not project.isprivate:
            serializer = ProjectFormSerializer()
            xml = serializer.serialize(project, request.get_host())
            return HttpResponse(
                etree.tostring(xml), content_type='text/xml; charset=utf-8')
        else:
            return HttpResponse(
                '<error>The project mus be public.</error>',
                content_type='text/xml; charset=utf-8',
                status=status.HTTP_403_FORBIDDEN
            )


class EpiCollectUploadView(APIView):
    def post(self, request, project_id):
        project = Project.objects.get(pk=project_id)

        if not project.isprivate and project.everyone_contributes:
            data = request.POST
            user = User.objects.get(display_name='AnonymousUser')
            project = Project.objects.get(pk=project_id)

            observation = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [
                        float(data.get('location_lon')),
                        float(data.get('location_lat'))
                    ]
                },
                'properties': {
                    'category': data.get('category'),
                    'attributes': {
                        'location_acc': data.get('location_acc'),
                        'location_provider': data.get('location_provider'),
                        'location_alt': data.get('location_alt'),
                        'location_bearing': data.get('location_bearing'),
                        'category': data.get('category'),
                        'unique_id': data.get('unique_id'),
                        'DeviceID': request.GET.get('phoneid')
                    }
                }
            }
            observationtype = Category.objects.get(
                pk=data.get('category'))

            for field in observationtype.fields.all():
                key = field.key.replace('-', '_')
                value = data.get(key + '_' + str(observationtype.id))
                observation['properties']['attributes'][field.key] = value

            ContributionSerializer(
                data=observation,
                context={'user': user, 'project': project}
            )
            return HttpResponse('1')

        return HttpResponse('0')


class EpiCollectDownloadView(APIView):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        if not project.isprivate:
            serializer = DataSerializer()
            if request.GET.get('xml') == 'false':
                tsv = serializer.serialize_to_tsv(project)
                return HttpResponse(
                    tsv,
                    content_type='text/plain; charset=utf-8'
                )
            else:
                xml = serializer.serialize_to_xml(project)
                return HttpResponse(
                    etree.tostring(xml),
                    content_type='text/xml; charset=utf-8'
                )