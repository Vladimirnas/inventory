from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_home, name='inventory_home'),
    path('planned/', views.planned_inventory, name='planned_inventory'),
    path('unplanned/', views.unplanned_inventory, name='unplanned_inventory'),
    path('current/', views.current_inventory, name='current_inventory'),
    path('current/departments/', views.admin_departments_inventory, name='admin_departments_inventory'),
    path('scan-asset/', views.scan_asset, name='scan_asset'),
    path('update-status/', views.update_status, name='update_status'),
    path('complete/<int:pk>/', views.complete_inventory, name='complete_inventory'),
    path('history/', views.inventory_history, name='inventory_history'),
    path('detail/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inv1/<int:pk>/', views.generate_inv1, name='generate_inv1'),
    path('inv1/<int:pk>/<str:format_type>/', views.generate_inv1, name='generate_inv1_format'),
    path('inv18/<int:pk>/', views.generate_inv18, name='generate_inv18'),
    path('inv18/<int:pk>/<str:format_type>/', views.generate_inv18, name='generate_inv18_format'),
    path('check_active/', views.check_active_inventory, name='check_active_inventory'),
    
    # Перенаправляем закрытые административные URL на главную страницу
    path('departments/', views.admin_redirect, name='department_list'),
    path('departments/create/', views.admin_redirect, name='department_create'),
    path('departments/<int:pk>/update/', views.admin_redirect, name='department_update'),
    path('departments/<int:pk>/delete/', views.admin_redirect, name='department_delete'),
    # path('positions/', views.admin_redirect, name='position_list'),
    # path('positions/create/', views.admin_redirect, name='position_create'),
    # path('positions/<int:pk>/update/', views.admin_redirect, name='position_update'),
    # path('positions/<int:pk>/delete/', views.admin_redirect, name='position_delete'),
    path('users/', views.admin_redirect, name='user_list'),
    path('users/create/', views.admin_redirect, name='user_create'),
    path('users/<int:pk>/', views.admin_redirect, name='user_detail'),
    path('users/<int:pk>/update/', views.admin_redirect, name='user_update'),
    path('users/<int:pk>/delete/', views.admin_redirect, name='user_delete'),
    
    # Оригинальные закомментированные маршруты
    # # URL-маршруты для подразделений
    # path('departments/', views.department_list, name='department_list'),
    # path('departments/create/', views.department_create, name='department_create'),
    # path('departments/<int:pk>/update/', views.department_update, name='department_update'),
    # path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # # URL-маршруты для должностей
    # path('positions/', views.position_list, name='position_list'),
    # path('positions/create/', views.position_create, name='position_create'),
    # path('positions/<int:pk>/update/', views.position_update, name='position_update'),
    # path('positions/<int:pk>/delete/', views.position_delete, name='position_delete'),
    
    # # URL-маршруты для пользователей
    # path('users/', views.user_list, name='user_list'),
    # path('users/create/', views.user_create, name='user_create'),
    # path('users/<int:pk>/', views.user_detail, name='user_detail'),
    # path('users/<int:pk>/update/', views.user_update, name='user_update'),
    # path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    
    # Маршрут для административной функциональности
    path('admin/', views.admin_redirect, name='inventory_admin_redirect'),
    path('admin/<int:pk>/', views.admin_redirect, name='inventory_admin_redirect_with_pk'),
] 