from django.urls import path
from perdcomp import views
from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, PERViewSet, DcompViewSet, DcompDebitosViewSet, PerCancViewSet

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'pers', PERViewSet)
router.register(r'dcomps', DcompViewSet)
router.register(r'dcomp-debitos', DcompDebitosViewSet)
router.register(r'per-cancs', PerCancViewSet)

urlpatterns = router.urls