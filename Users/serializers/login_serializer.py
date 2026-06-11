from rest_framework_simplejwt.serializers import (TokenObtainPairSerializer)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['rol'] = user.rol
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['rol'] = self.user.rol
        data['email'] = self.user.email
        data['username'] = self.user.username

        return data