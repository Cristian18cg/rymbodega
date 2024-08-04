from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from .views import PedidosViews
from rest_framework import routers

router_compras= routers.DefaultRouter()
router_compras.register(r"", PedidosViews, basename="pedidos")

urlpatterns = [
    path("", include(router_compras.urls), name="pedidos"),
    # path('buscar_archivos/', buscar_archivos_view, name='buscar_archivos'),
]