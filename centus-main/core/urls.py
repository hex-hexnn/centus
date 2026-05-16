from django.contrib import admin
from django.urls import path, include # <--- Upewnij się, że masz import 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Tutaj mówimy: "Wszystko co wchodzi na stronę główną, wyślij do pliku urls w folderze finance"
    path('accounts/', include('django.contrib.auth.urls')),

    path('', include('finance.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)