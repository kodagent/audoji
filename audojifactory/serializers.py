from rest_framework import serializers

from audojifactory.models import AudioFile, AudioSegment, UserSelectedAudoji
from audojifactory.utils import seconds_to_minutes


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
            "spotify_link",
        ]


class AudioSegmentSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    audio_file_duration = serializers.SerializerMethodField()
    start_time_minutes = serializers.SerializerMethodField()
    end_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = AudioSegment
        fields = [
            "id",
            "audio_file",
            "start_time",
            "end_time",
            "start_time_minutes",
            "end_time_minutes",
            "segment_file",
            "transcription",
            "category",
            "is_selected",
            "audio_file_duration",
        ]

    def get_is_selected(self, obj):
        # Assuming 'self.context['request'].user_id' is the way to access the user_id in your context
        # You need to ensure that 'user_id' is passed to the serializer context in your view.
        request = self.context.get("request")
        if request and hasattr(request, "query_params"):
            user_id = request.query_params.get("user_id")
            if user_id is not None:
                bool_val = UserSelectedAudoji.objects.filter(
                    user_id=user_id, audio_segment=obj
                ).exists()
                return bool_val
        return False

    def get_start_time_minutes(self, obj):
        return seconds_to_minutes(obj.start_time)

    def get_end_time_minutes(self, obj):
        return seconds_to_minutes(obj.end_time)

    def get_audio_file_duration(self, obj):
        if obj.audio_file.duration:
            return seconds_to_minutes(obj.audio_file.duration)
        return None


class AudioSegmentSerializerWebSocket(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    audio_file_duration = serializers.SerializerMethodField()
    start_time_minutes = serializers.SerializerMethodField()
    end_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = AudioSegment
        fields = [
            "id",
            "audio_file",
            "start_time",
            "end_time",
            "start_time_minutes",
            "end_time_minutes",
            "segment_file",
            "transcription",
            "category",
            "is_selected",
            "audio_file_duration",
        ]

    def get_is_selected(self, obj):
        # Retrieve user_id from the serializer context directly
        user_id = self.context.get("user_id")
        if user_id:
            # Use the user_id to filter UserSelectedAudoji
            is_selected = UserSelectedAudoji.objects.filter(
                user_id=user_id, audio_segment=obj
            ).exists()
            return is_selected
        return False

    def get_start_time_minutes(self, obj):
        return seconds_to_minutes(obj.start_time)

    def get_end_time_minutes(self, obj):
        return seconds_to_minutes(obj.end_time)

    def get_audio_file_duration(self, obj):
        if obj.audio_file.duration:
            return seconds_to_minutes(obj.audio_file.duration)
        return None
