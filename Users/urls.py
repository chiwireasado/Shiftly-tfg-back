from django.urls import path
from Users.views import (RegisterView, UserProfileView, CustomTokenObtainPairView, CrearEmpleadoView, CrearProductoView, \
    VerInventarioView, RegistrarPagoView, CerrarTurnoView, ObtenerInformeView, AbrirTurnoView, AdminVerInformesEmpresaView,
                         ModificarProductoView, HistorialVentasAdminView, EjecutarDevolucionView, ListaDevolucionesAdminView)

from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('crear-empleado/', CrearEmpleadoView.as_view(), name='crear_empleado'),
    path('crear-producto/', CrearProductoView.as_view(), name='crear_producto'),
    path('inventario/', VerInventarioView.as_view(), name='ver_inventario'),
    path('registrar-pago/', RegistrarPagoView.as_view(), name='registrar-pago'),
    path('cerrar-turno/', CerrarTurnoView.as_view(), name='cerrar-turno'),
    path('ver-informe/', ObtenerInformeView.as_view(), name='ver-informe'),
    path('abrir-turno/', AbrirTurnoView.as_view(), name='abrir-turno'),
    path('admin/historial-informes/', AdminVerInformesEmpresaView.as_view(), name='admin-historial-informes'),
    path('modificar-producto/<int:pk>/', ModificarProductoView.as_view(), name='modificar-producto'),
    path('admin/devoluciones/', HistorialVentasAdminView.as_view(), name='admin-historial-ventas'),
    path('admin/devolver-item/<int:pk>/', EjecutarDevolucionView.as_view(), name='admin-devolver-item'),
    path('admin/lista-devoluciones/', ListaDevolucionesAdminView.as_view(), name='admin-lista-devoluciones'),
path('create-payment-intent/', views.crear_intencion_pago, name='crear_intencion_pago'),
]