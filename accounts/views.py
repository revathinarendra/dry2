from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Account
from .serializers import AccountSerializer, LoginSerializer,UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Account
from .serializers import UserProfileSerializer
from utils.encryption import encrypt_id, decrypt_id


@api_view(['POST'])
def register(request):
    data = request.data
    user_serializer = AccountSerializer(data=data)
    print(user_serializer.data)

    if user_serializer.is_valid():
        # Check if user with the same email already exists
        if not Account.objects.filter(email=data['email']).exists():
            user = user_serializer.save()
            # Set the password field to a hashed value
            user.set_password(data['password'])
            user.is_active = True  # Activate user by default
            user.save()  # Save the updated is_active field
            
            return Response({'message': 'User registered and activated successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def user_profile(request):
    if request.user.is_authenticated:
        try:
            # Retrieve the user's profile using the logged-in user
            profile = Account.objects.get(id=request.user.id)
            serializer = UserProfileSerializer(profile)

            # Encrypt the user ID before sending it to the frontend
            data = serializer.data
            data['encrypted_id'] = encrypt_id(profile.id)

            return Response(data, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
@api_view(['POST'])
def update_user_profile(request):
    if request.user.is_authenticated:
        try:
            # Decrypt the encrypted ID received from the frontend
            encrypted_id = request.data.get('encrypted_id')
            user_id = decrypt_id(encrypted_id)

            # Update the user's profile
            profile = Account.objects.get(id=user_id)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Account.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:  # Check if the user's account is active
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'email': user.email,
                    
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
