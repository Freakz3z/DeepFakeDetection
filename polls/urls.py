from django.urls import path
# from .views import upload_video, detect_objects_from_video
from django.conf import settings
from django.conf.urls.static import static
from .views import upload_video, detect_objects_from_video, upload_image, detect_objects_from_image

# urlpatterns = [
#     path('', upload_video, name='home'),  # Root URL points to the upload_video view
#     path('upload_video/', upload_video, name='upload_video'),
#     path('detect_objects_from_video/', detect_objects_from_video, name='detect_objects_from_video'),
# ]

urlpatterns = [
    path('', upload_video, name='home'),  # Root URL points to the upload_video view
    path('upload_video/', upload_video, name='upload_video'),
    path('detect_objects_from_video/', detect_objects_from_video, name='detect_objects_from_video'),
    path('upload_image/', upload_image, name='upload_image'),
    path('detect_objects_from_image/', detect_objects_from_image, name='detect_objects_from_image'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
