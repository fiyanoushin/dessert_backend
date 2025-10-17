from rest_framework import viewsets, status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import User, Product, CartItem, WishlistItem, Order
from .serializers import (
    UserSerializer, RegisterSerializer,
    ProductSerializer, CartItemSerializer,
    WishlistItemSerializer, OrderSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]  

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
  
    username_or_email = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')

    if not username_or_email or not password:
        return Response({"detail": "Please provide username/email and password"}, status=status.HTTP_400_BAD_REQUEST)

    
    user = authenticate(request, username=username_or_email, password=password)
    if not user:
       
        try:
            user_obj = User.objects.get(username=username_or_email)
            user = authenticate(request, username=user_obj.email, password=password)
        except User.DoesNotExist:
            user = None

    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data
    })



class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = Product.objects.filter(active=True)
        q = self.request.query_params.get('q')
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__iexact=category)
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save()


from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes

@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def cart_items(request):
    user = request.user

    if request.method == 'GET':
        items = CartItem.objects.filter(user=user).select_related('product')
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
       
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    if request.method == 'PATCH':
       
        item_id = request.data.get('id')
        item = get_object_or_404(CartItem, id=item_id, user=user)
        serializer = CartItemSerializer(item, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CartItemSerializer(item).data)

    if request.method == 'DELETE':
       
        item_id = request.data.get('id')
        if item_id:
            item = get_object_or_404(CartItem, id=item_id, user=user)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        product_id = request.data.get('product')
        if product_id:
            CartItem.objects.filter(user=user, product_id=product_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Provide id or product id"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_items(request):
    user = request.user

    if request.method == 'GET':
        items = WishlistItem.objects.filter(user=user).select_related('product')
        serializer = WishlistItemSerializer(items, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = WishlistItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(WishlistItemSerializer(item).data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        product_id = request.data.get('product')
        if not product_id:
            return Response({"detail": "product id required"}, status=status.HTTP_400_BAD_REQUEST)
        item = get_object_or_404(WishlistItem, user=user, product_id=product_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all().order_by('-date')
        return Order.objects.filter(user=user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Successfully logged out."})
    except Exception:
        return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
