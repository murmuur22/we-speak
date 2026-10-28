from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from forum import views, attachments
from forum.operator import operator_login, dashboard, identity_action

urlpatterns = [
    path('healthz/', views.health, name='health'),
    path('', views.board, name='board'),
    path('new/', views.new_post, name='new'),
    path('thread/<int:pk>/', views.thread, name='thread'),
    path('guest/', views.guest, name='guest'),
    path('leave/', views.leave, name='leave'),
    path('thread/<int:pk>/comment/', views.comment, name='comment'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/edit/', views.edit, name='edit_post'),
    path('comment/<int:pk>/edit/', views.edit, {'kind': 'comment'}, name='edit_comment'),
    path('comment/<int:pk>/delete/', views.delete_post, {'kind': 'comment'}, name='delete_comment'),
    path('post/<int:pk>/react/', views.react, name='react_post'),
    path('comment/<int:pk>/react/', views.react, {'kind': 'comment'}, name='react_comment'),
    path('post/<int:pk>/attach/', attachments.attach, name='attach_post'),
    path('comment/<int:pk>/attach/', attachments.attach, {'kind': 'comment'}, name='attach_comment'),
    path('attachment/<uuid:pk>/', attachments.download, name='attachment'),
    path('maintenance/', dashboard, name='maintenance'),
    path('maintenance/identity/<int:pk>/', identity_action, name='identity_action'),
    path('admin/login/', operator_login),
    path('admin/', admin.site.urls),
    path('join/', views.join, name='join'),
    path('login/', views.sign_in, name='login'),
    path('history/', views.history, name='history'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
