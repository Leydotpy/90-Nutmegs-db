from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


from .serializers import AudioCreateSerializer


class MediaAudioAPIView(APIView):
    permission_classes = [AllowAny,]
    serializer_class = AudioCreateSerializer


    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        ser = self.get_serializer_class()
        context = {'request': self.request, "view": self}
        kwargs.setdefault('context', context)
        return ser(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)