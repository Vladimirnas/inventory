from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
import json

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def login_api(request):
    """API для авторизации"""
    # Debug: вывод полученных данных
    print("Login attempt. Request data:", request.data)
    
    # Получение данных из запроса
    if isinstance(request.data, dict):
        username = request.data.get('username')
        password = request.data.get('password')
    else:
        try:
            # Если данные пришли в виде JSON-строки
            body_unicode = request.body.decode('utf-8')
            print("Request body:", body_unicode)
            body = json.loads(body_unicode)
            username = body.get('username')
            password = body.get('password')
        except Exception as e:
            print("Error parsing request body:", str(e))
            username = None
            password = None
    
    if not username or not password:
        error_response = {
            'error': 'Необходимо указать имя пользователя и пароль'
        }
        print("Error response:", error_response)
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        success_response = {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_staff or user.is_superuser
            }
        }
        print("Success response:", success_response)
        return Response(success_response)
    else:
        error_response = {
            'error': 'Неверное имя пользователя или пароль'
        }
        print("Error response:", error_response)
        return Response(error_response, status=status.HTTP_401_UNAUTHORIZED) 