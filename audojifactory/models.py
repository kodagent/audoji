from django.db import models
from django.utils import timezone

from accounts.models import OrganizationCustomer


class AudioFile(models.Model):
    owner = models.ForeignKey(OrganizationCustomer, on_delete=models.CASCADE)
    artiste = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to="audio_files/")
    title = models.CharField(max_length=255)
    cover_image = models.CharField(max_length=255)
    terms_condition = models.BooleanField(default=False)
    upload_date = models.DateTimeField(default=timezone.now)


def get_segment_upload_path(instance, filename):
    # Assuming 'title' is a field in 'AudioFile' model
    # Replace 'title' with the appropriate field if different
    return f"audio_segments/{instance.audio_file.title}/{filename}"


class AudioSegment(models.Model):
    audio_file = models.ForeignKey(
        AudioFile, related_name="segments", on_delete=models.CASCADE
    )
    start_time = models.FloatField()
    end_time = models.FloatField()
    segment_file = models.FileField(
        upload_to=get_segment_upload_path, blank=True, null=True
    )
    transcription = models.TextField(blank=True, null=True)
    mood = models.CharField(max_length=100, blank=True, null=True)

    @property
    def calculate_duration(self):
        return self.end_time - self.start_time

    def save(self, *args, **kwargs):
        self.duration = self.calculate_duration
        super(AudioSegment, self).save(*args, **kwargs)
