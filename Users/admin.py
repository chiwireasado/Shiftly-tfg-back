from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from Users.models import User, Empresas, Producto

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'empresa', 'is_active')
    list_filter = ('rol', 'empresa')
    search_fields = ('username', 'email')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'empresa')
    list_filter = ('categoria', 'empresa')
    search_fields = ('nombre', 'descripcion')

@admin.register(Empresas)
class EmpresaInfoAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'numero_empleados')