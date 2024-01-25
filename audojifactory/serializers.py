from rest_framework import serializers

from audojifactory.models import AudioFile, AudioSegment


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
    class Meta:
        model = AudioSegment
        fields = [
            "id",
            "audio_file",
            "start_time",
            "end_time",
            "segment_file",
            "transcription",
            "mood",
        ]
