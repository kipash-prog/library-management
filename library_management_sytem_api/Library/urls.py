from django.urls import path,include
from rest_framework import routers
from .views import BookView, UserView, BookCheckoutView,UserBorrowingHistoryView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register('books',BookView)
router.register('users',UserView)
router.register('bookcheckout',BookCheckoutView)
router.register(r'checkout', BookCheckoutView, basename='checkout')

urlpatterns = [
    path('',include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/borrowing-history/', UserBorrowingHistoryView.as_view({'get': 'borrowing_history'}), name='borrowing_history'),
]
 