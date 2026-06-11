from rest_framework import serializers
from Users.models import User, Empresas


class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(required=True, min_length=6, write_only=True)
    password2 = serializers.CharField(required=True, min_length=6, write_only=True)


    nombre_empresa = serializers.CharField(required=True, max_length=100, write_only=True)
    numero_empleados = serializers.IntegerField(required=True, min_value=1, max_value=5, write_only=True)

    class Meta:
        model = User
        fields = (
            "email", "username", "nombre", "apellidos",
            "password1", "password2",
            "nombre_empresa", "numero_empleados"
        )


    def validate_email(self, email):
        if "@" not in email:
            raise serializers.ValidationError("El email no es válido.")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("El correo ya existe. Intente con otro.")
        return email

    def validate_numero_empleados(self, empleados):
        if empleados < 1 or empleados > 5:
            raise serializers.ValidationError("El número de empleados debe estar entre 1 y 5.")
        return empleados

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError({"password_mismatch": "Las contraseñas no coinciden."})
        return attrs


    def create(self, validated_data):
        password = validated_data.pop("password1")
        validated_data.pop("password2")
        nombre_emp = validated_data.pop("nombre_empresa")
        num_emp = validated_data.pop("numero_empleados")


        empresa_obj = Empresas.objects.create(
            nombre_empresa=nombre_emp,
            numero_empleados=num_emp
        )


        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=password,
            nombre=validated_data.get("nombre", ""),
            apellidos=validated_data.get("apellidos", ""),
            empresa=empresa_obj,
            rol='ADMIN'
        )

        return user


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'nombre', 'apellidos']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        jefe = self.context['request'].user


        empleado = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            nombre=validated_data.get('nombre', ''),
            apellidos=validated_data.get('apellidos', ''),
            empresa=jefe.empresa,
            rol='USER'
        )
        return empleado

from Users.models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria']

