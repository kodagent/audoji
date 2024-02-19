from django.db import models
from django.utils import timezone

# from accounts.models import OrganizationCustomer


class AudioFile(models.Model):
    # owner = models.ForeignKey(OrganizationCustomer, on_delete=models.CASCADE)
    owner = models.CharField(max_length=255)
    artiste = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to="audio_files/")
    title = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to="cover_images/", null=True, blank=True) 
    terms_condition = models.BooleanField(default=False)
    upload_date = models.DateTimeField(default=timezone.now)


def get_segment_upload_path(instance, filename):
    # Ensuring the title is filesystem-safe by replacing non-alphanumeric characters with "_"
    safe_title = "".join([c if c.isalnum() else "_" for c in instance.audio_file.title])
    return f"audio_segments/{safe_title}/{filename}"


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
    category = models.CharField(max_length=100, blank=True, null=True)
    # Added duration field to store the duration of the segment
    duration = models.FloatField(default=0.0, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.duration = self.end_time - self.start_time
        super(AudioSegment, self).save(*args, **kwargs)


class UserSelectedAudoji(models.Model):
    user_id = models.CharField(max_length=255)  # Adjust max_length as needed
    audio_segment = models.ForeignKey(AudioSegment, on_delete=models.CASCADE)
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'audio_segment')