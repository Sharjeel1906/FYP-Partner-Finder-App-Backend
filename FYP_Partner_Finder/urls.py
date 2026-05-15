from django.urls import path
from .views import get_all_users_details, get_specific_user_details, update_user, create_user, send_invitation_email, \
    get_all_conversations, get_conversation_messages, create_team, add_member, get_team_details, get_all_teams, \
    EmailLoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", get_all_users_details, name="all-users"),
    path("users/<int:user_id>/", get_specific_user_details, name="user-detail"),
    path("update-user/", update_user, name="update-user"),
    path("create-user/", create_user, name="create-user"),
    path("send_email/", send_invitation_email, name="send-invitation-email"),
    path('inbox/', get_all_conversations, name='get-all-conversations'),
    path('messages/<int:user_id>/', get_conversation_messages, name='get-conversation-messages'),
    path("teams/", get_all_teams),
    path("create_team/", create_team),
    path("add_team_member/", add_member),
    path("team/<int:team_id>/", get_team_details),
]
