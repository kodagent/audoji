from django.urls import path

from audojifactory import views

urlpatterns = [
    path("audiofiles/", views.AudioFileList.as_view(), name="audiofile_list"),
    path("audiosegments/", views.AudioSegmentList.as_view(), name="audiosegment_list"),
    # path("search-audoji/", views.SearchAudoji.as_view(), name="search_audoji"),
    path("get-audoji/", views.GetAudoji.as_view(), name="get_audoji"),
    path('select-audoji/', views.SelectAudoji.as_view(), name='select-audoji'),
    path('selected-audojis/', views.SelectedAudojiList.as_view(), name='selected-audojis'),
]
