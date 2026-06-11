from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

class Turno(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='turnos')
    empresa = models.ForeignKey('Empresas', on_delete=models.CASCADE)
    hora_inicio = models.DateTimeField(auto_now_add=True)
    hora_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Turno {self.usuario.email} - {'Activo' if self.activo else 'Cerrado'}"


class VentaTurno(models.Model):
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='ventas')
    producto_nombre = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio_unidad = models.DecimalField(max_digits=6, decimal_places=2)
    metodo_pago = models.CharField(max_length=10)
    hora_venta = models.DateTimeField(auto_now_add=True)

    devuelto = models.BooleanField(default=False)
    fecha_venta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto_nombre} x{self.cantidad} ({self.metodo_pago})"


class Empresas(models.Model):
    nombre_empresa = models.CharField(max_length=100)
    numero_empleados = models.IntegerField(default=1)

    def __str__(self):
        return self.nombre_empresa


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('ADMIN', 'Administrador/Dueño'),
        ('USER', 'Empleado'),
    ]
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='USER')
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=50, blank=True)
    apellidos = models.CharField(max_length=50, blank=True)


    empresa = models.ForeignKey(
        Empresas,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='empleados'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email



class Producto(models.Model):
    CATEGORIAS = [
        ('BEBIDAS', 'Bebidas'),
        ('COMIDA', 'Comida'),
        ('POSTRES', 'Postres'),
        ('TOSTADAS', 'tostadas'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)

    empresa = models.ForeignKey(
        Empresas,
        on_delete=models.CASCADE,
        related_name='productos',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.nombre} - {self.precio}€"