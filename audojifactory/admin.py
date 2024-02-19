from django.contrib import admin

from audojifactory.models import AudioFile, AudioSegment, UserSelectedAudoji


class AudioSegmentInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = AudioSegment
    extra = 0  # Removes extra blank forms
    fields = ('start_time', 'end_time', 'segment_file', 'transcription', 'category', 'duration')

    
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ("artiste", "title", "owner", "terms_condition", "upload_date")
    search_fields = ("artiste", "title", "owner", "upload_date")
    list_filter = ("upload_date",)
    inlines = [AudioSegmentInline]


class AudioSegmentAdmin(admin.ModelAdmin):
    list_display = ("id", "transcription", "start_time", "end_time", "duration")
    search_fields = ("audio_file__title", "transcription")
    list_filter = ("audio_file",)

    def duration(self, obj):
        return obj.calculate_duration

    duration.short_description = "Duration (seconds)"


class UserSelectedAudojiAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'audio_segment_display', 'selected_at')
    search_fields = ('user_id', 'audio_segment__audio_file__title')  # Adjusted to reflect the correct relationship path
    list_filter = ('selected_at',)

    def audio_segment_display(self, obj):
        return obj.audio_segment.transcription
    audio_segment_display.short_description = 'Audio Segment'


admin.site.register(AudioSegment, AudioSegmentAdmin)
admin.site.register(AudioFile, AudioFileAdmin)
admin.site.register(UserSelectedAudoji, UserSelectedAudojiAdmin)
