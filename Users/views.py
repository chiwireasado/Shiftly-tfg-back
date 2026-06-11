from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import transaction
from django.utils import timezone


from Users.models import Producto, Turno, VentaTurno
from Users.serializers.register_serializer import ProductoSerializer, RegisterSerializer, EmpleadoSerializer
from Users.serializers.login_serializer import CustomTokenObtainPairSerializer
from rest_framework.decorators import api_view, permission_classes


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            if user.rol == 'USER':

                Turno.objects.filter(usuario=user, activo=True).update(
                    activo=False,
                    hora_fin=timezone.now()
                )

                Turno.objects.create(usuario=user, empresa=user.empresa, activo=True)

        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_inventario(request):
    usuario_actual = request.user
    empresa_usuario = usuario_actual.empresa
    productos_empresa = Producto.objects.filter(empresa=empresa_usuario)
    serializer = ProductoSerializer(productos_empresa, many=True)
    return Response(serializer.data)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "username": user.username,
            "nombre_empresa": user.empresa.nombre_empresa if user.empresa else "Sin empresa",
            "empleados": user.empresa.numero_empleados if user.empresa else 0
        })


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario creado con éxito"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CrearEmpleadoView(generics.CreateAPIView):
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
       if self.request.user.rol != 'ADMIN':
            raise PermissionDenied("Solo los administradores pueden crear empleados.")
       serializer.save()


class CrearProductoView(generics.CreateAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.rol != 'ADMIN':
            raise PermissionDenied("Solo los administradores pueden añadir productos.")
        serializer.save(empresa=self.request.user.empresa)


class VerInventarioView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario_actual = self.request.user
        return Producto.objects.filter(empresa=usuario_actual.empresa)


class RegistrarPagoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        productos_vendidos = request.data.get('productos', [])
        metodo_pago = request.data.get('metodo_pago', 'EFECTIVO')


        try:
            turno_actual = Turno.objects.get(usuario=request.user, activo=True)
        except Turno.DoesNotExist:
            return Response({"error": "No tienes ningún turno activo abierto para registrar la venta."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not productos_vendidos:
            return Response({"error": "No hay productos en el pedido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                for item in productos_vendidos:
                    producto_id = item.get('id')
                    cantidad_vendida = item.get('cantidad', 1)

                    producto = Producto.objects.get(id=producto_id, empresa=request.user.empresa)

                    if producto.stock < cantidad_vendida:
                        return Response(
                            {"error": f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )


                    producto.stock -= cantidad_vendida
                    producto.save()

                    VentaTurno.objects.create(
                        turno=turno_actual,
                        producto_nombre=producto.nombre,
                        cantidad=cantidad_vendida,
                        precio_unidad=producto.precio,
                        metodo_pago=metodo_pago
                    )

            return Response({"message": "Pago registrado y stock actualizado con éxito"}, status=status.HTTP_200_OK)

        except Producto.DoesNotExist:
            return Response({"error": "Uno de los productos no existe o no pertenece a tu empresa"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CerrarTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            turno = Turno.objects.get(usuario=request.user, activo=True)
            turno.activo = False
            turno.hora_fin = timezone.now()
            turno.save()
            return Response({"message": "Turno cerrado correctamente."}, status=status.HTTP_200_OK)
        except Turno.DoesNotExist:
            return Response({"error": "No tienes ningún turno activo que cerrar o ya está cerrado."},
                            status=status.HTTP_400_BAD_REQUEST)


class ObtenerInformeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ultimo_turno = Turno.objects.filter(usuario=request.user).order_by('-hora_inicio').first()

        if not ultimo_turno:
            return Response({"error": "No se encontraron turnos registrados para este usuario."},
                            status=status.HTTP_404_NOT_FOUND)

        if ultimo_turno.activo:
            return Response(
                {"error": "Bloqueado: Debes presionar 'Cerrar Turno' antes de poder visualizar o imprimir el informe."},
                status=status.HTTP_403_FORBIDDEN)

        ventas = ultimo_turno.ventas.all()
        lista_ventas = []
        total_acumulado = 0

        for v in ventas:
            subtotal = v.cantidad * v.precio_unidad
            total_acumulado += subtotal
            lista_ventas.append({
                "producto": v.producto_nombre,
                "cantidad": v.cantidad,
                "precio_unidad": float(v.precio_unidad),
                "metodo_pago": v.metodo_pago,
                "subtotal": float(subtotal)
            })

        return Response({
            "empleado": request.user.nombre,
            "hora_inicio": ultimo_turno.hora_inicio.strftime('%d/%m/%Y %H:%M'),
            "hora_fin": ultimo_turno.hora_fin.strftime('%d/%m/%Y %H:%M'),
            "total_ventas": float(total_acumulado),
            "desglose": lista_ventas
        }, status=status.HTTP_200_OK)


class AbrirTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            Turno.objects.filter(usuario=request.user, activo=True).update(
                activo=False,
                hora_fin=timezone.now()
            )
            Turno.objects.create(usuario=request.user, empresa=request.user.empresa, activo=True)

            return Response({"message": "Turno abierto con éxito"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Error en el servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminVerInformesEmpresaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol != 'ADMIN':
            return Response({"error": "Acceso denegado. Solo administradores."}, status=status.HTTP_403_FORBIDDEN)

        turnos_empresa = Turno.objects.filter(
            empresa=request.user.empresa,
            activo=False
        ).order_by('-hora_fin')


        historial_informes = []
        for turno in turnos_empresa:

            ventas = turno.ventas.all()
            total_recaudado = sum(v.cantidad * v.precio_unidad for v in ventas)

            desglose_productos = []
            for v in ventas:
                desglose_productos.append({
                    "producto": v.producto_nombre,
                    "cantidad": v.cantidad,
                    "precio_unidad": float(v.precio_unidad),
                    "metodo_pago": v.metodo_pago,
                    "subtotal": float(v.cantidad * v.precio_unidad)
                })

            historial_informes.append({
                "id_turno": turno.id,
                "empleado_username": turno.usuario.username,
                "empleado_nombre": turno.usuario.nombre,
                "hora_inicio": turno.hora_inicio.strftime('%d/%m/%Y %H:%M'),
                "hora_fin": turno.hora_fin.strftime('%d/%m/%Y %H:%M') if turno.hora_fin else 'N/A',
                "total_ventas": float(total_recaudado),
                "productos_vendidos": desglose_productos
            })

        return Response(historial_informes, status=status.HTTP_200_OK)


class ModificarProductoView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if request.user.rol != 'ADMIN':
            return Response({"error": "Solo los administradores pueden modificar productos."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            producto = Producto.objects.get(id=pk, empresa=request.user.empresa)


            nuevo_precio = request.data.get('precio')
            nuevo_stock = request.data.get('stock')

            if nuevo_precio is not None:
                producto.precio = nuevo_precio
            if nuevo_stock is not None:
                producto.stock = nuevo_stock

            producto.save()
            return Response({"message": "Producto actualizado con éxito."}, status=status.HTTP_200_OK)

        except Producto.DoesNotExist:
            return Response({"error": "El producto no existe o no pertenece a tu empresa."},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistorialVentasAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol != 'ADMIN':
            return Response({"error": "Solo administradores."}, status=status.HTTP_403_FORBIDDEN)


        ventas = VentaTurno.objects.filter(
            turno__empresa=request.user.empresa,
            devuelto=False
        ).order_by('-fecha_venta')

        resultado = [{
            "id_venta": v.id,
            "producto": v.producto_nombre,
            "cantidad": v.cantidad,
            "precio": float(v.precio_unidad),
            "total": float(v.cantidad * v.precio_unidad),
            "metodo_pago": v.metodo_pago,
            "empleado": v.turno.usuario.nombre if v.turno.usuario.nombre else v.turno.usuario.username,
            "fecha": v.fecha_venta.strftime('%d/%m/%Y %H:%M') if hasattr(v, 'fecha_venta') else 'Reciente'
        } for v in ventas]

        return Response(resultado, status=status.HTTP_200_OK)


class EjecutarDevolucionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.rol != 'ADMIN':
            return Response({"error": "Solo administradores."}, status=status.HTTP_403_FORBIDDEN)

        try:
            with transaction.atomic():
                venta = VentaTurno.objects.get(id=pk, turno__empresa=request.user.empresa)

                if venta.devuelto:
                    return Response({"error": "Esta venta ya fue devuelta anteriormente."},
                                    status=status.HTTP_400_BAD_REQUEST)


                try:
                    producto = Producto.objects.get(nombre=venta.producto_nombre, empresa=request.user.empresa)
                    producto.stock += venta.cantidad
                    producto.save()
                except Producto.DoesNotExist:
                    pass


                venta.devuelto = True
                venta.save()

            return Response({"message": "Devolución completada y restock aplicado con éxito."},
                            status=status.HTTP_200_OK)

        except VentaTurno.DoesNotExist:
            return Response({"error": "El registro de venta no existe."}, status=status.HTTP_404_NOT_FOUND)


class ListaDevolucionesAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol != 'ADMIN':
            return Response({"error": "Solo administradores."}, status=status.HTTP_403_FORBIDDEN)


        devoluciones = VentaTurno.objects.filter(
            turno__empresa=request.user.empresa,
            devuelto=True
        ).order_by('-id')

        resultado = [{
            "id_venta": d.id,
            "producto": d.producto_nombre,
            "cantidad": d.cantidad,
            "total_reembolsado": float(d.cantidad * d.precio_unidad),
            "empleado_caja": d.turno.usuario.nombre if d.turno.usuario.nombre else d.turno.usuario.username,
            "metodo_pago": d.metodo_pago
        } for d in devoluciones]

        return Response(resultado, status=status.HTTP_200_OK)