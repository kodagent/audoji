from django.urls import path

from audojifactory.views import AudioFileList, AudioSegmentList, SearchLyrics

urlpatterns = [
    path('audiofiles/', AudioFileList.as_view(), name='audiofile_list'),
    path('audiosegments/', AudioSegmentList.as_view(), name='audiosegment_list'),

    path('get-audoji/', SearchLyrics.as_view(), name='get_audoji'),
]
