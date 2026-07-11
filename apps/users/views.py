from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserReadSerializer

User = get_user_model()


@extend_schema(
    summary="Register a new farm owner account",
    request=UserRegisterSerializer,
    responses={201: UserReadSerializer},
    tags=["Auth"],
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        # Write on input, read on response
        if self.request.method == "POST":
            return UserRegisterSerializer
        return UserReadSerializer


@extend_schema(summary="Login — obtain JWT access + refresh tokens", tags=["Auth"])
class LoginView(TokenObtainPairView):
    pass


@extend_schema(summary="Rotate JWT access token using refresh token", tags=["Auth"])
class TokenRefreshView(TokenRefreshView):
    pass
