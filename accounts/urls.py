from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginPage.as_view(), name="login"),
    path("signup/", views.SignupPage.as_view(), name="signup"),
    path("logout/", views.LogoutPage.as_view(), name="logout"),
    path("login/api/", views.LoginApiView.as_view(), name="login_api"),
    path("signup/api/", views.SignupApiView.as_view(), name="signup_api"),
    path("logout/api/", views.LogoutApiView.as_view(), name="logout_api"),
]
