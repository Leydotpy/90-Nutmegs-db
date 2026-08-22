from rest_framework import serializers



class AudioCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=True)
    #file = serializers.FileField(required=True)
    master = serializers.BooleanField(default=True)

    class Meta:
        fields = '__all__'

    def create(self, validated_data):
        return validated_data