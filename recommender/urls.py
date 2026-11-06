from django.urls import path
from recommender.views import *

urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup_view, name='signup'),
    path('predict/', predict_view, name='predict'),
    path('logout/', logout_view, name='logout'),
    path('login/', login_view, name='login'),
    path('history/', user_history_view, name='user_history'), 
    path('delete_prediction/<int:id>/', user_delete_prediction, name='user_delete_prediction'),
    path('profile/',profile_view, name='profile'),
    path('change_password/',change_password_view, name='change_password'),
    path('admin_login/',admin_login_view, name='admin_login'),
    path('admin_dashboard/',admin_dashboard_view, name='admin_dashboard'),  
    path('admin_users_view/',admin_users_view, name='admin_users_view'),  
    path('admin_user_delete/<int:id>/',admin_users_view,name='admin_user_delete'),
    path('admin_view_predictions/',admin_view_predictions,name="admin_view_predictions"),
    path('admin_delete_prediction/<int:id>/',admin_delete_prediction, name='admin_delete_prediction'),
    path('admin_logout/',admin_logout, name='admin_logout'),  
]
