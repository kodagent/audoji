from rest_framework import serializers

from audojifactory.models import AudioFile, AudioSegment, UserSelectedAudoji


class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = [
            "id",
            "owner",
            "audio_file",
            "artiste",
            "title",
            "cover_image",
            "terms_condition",
        ]


class AudioSegmentSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = AudioSegment
        fields = [
            "id",
            "audio_file",
            "start_time",
            "end_time",
            "segment_file",
            "transcription",
            "category",
            "is_selected",
        ]

    def get_is_selected(self, obj):
        # Assuming 'self.context['request'].user_id' is the way to access the user_id in your context
        # You need to ensure that 'user_id' is passed to the serializer context in your view.
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            user_id = request.query_params.get("user_id")
            if user_id is not None:
                bool_val = UserSelectedAudoji.objects.filter(user_id=user_id, audio_segment=obj).exists()
                return bool_val
        return False


class AudioSegmentSerializerWebSocket(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = AudioSegment
        fields = [
            "id",
            "audio_file",
            "start_time",
            "end_time",
            "segment_file",
            "transcription",
            "category",
            "is_selected",
        ]

    def get_is_selected(self, obj):
        # Retrieve user_id from the serializer context directly
        user_id = self.context.get('user_id')
        if user_id:
            # Use the user_id to filter UserSelectedAudoji
            is_selected = UserSelectedAudoji.objects.filter(user_id=user_id, audio_segment=obj).exists()
            return is_selected
        return False