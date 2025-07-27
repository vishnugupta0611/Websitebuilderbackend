from rest_framework import viewsets
from .models import getuserdata 
from .serializers import UserDataSerializer
from rest_framework.response import Response
from rest_framework.decorators import action

class UserDataViewSet(viewsets.ModelViewSet):
    queryset = getuserdata.objects.all()
    serializer_class = UserDataSerializer

    # Custom GET endpoint: /userdata/by_email/?email=abc@gmail.com
    @action(detail=False, methods=['get'], url_path='by_email', url_name='by_email')
    def by_email(self, request):
        email = request.query_params.get('email')
        if email:
            print(email)
            users = self.queryset.filter(email=email)
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response({"error": "Email parameter is required"}, status=400)
