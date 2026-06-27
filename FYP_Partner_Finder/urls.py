from django.urls import path
from .views import get_all_users_details, get_specific_user_details, update_user, create_user, send_invitation_email, \
    get_all_conversations, get_conversation_messages, create_team, add_member, get_team_details, get_all_teams, \
    EmailLoginView, get_current_user_details, get_my_team, delete_message, delete_conversation, remove_team_member, \
    request_exit_team, delete_team, download_db
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
    path("current_user_detail/", get_current_user_details, name="current_user-detail"),
    path("update-user/", update_user, name="update-user"),
    path("create-user/", create_user, name="create-user"),
    path("send_email/", send_invitation_email, name="send-invitation-email"),
    path('inbox/', get_all_conversations, name='get-all-conversations'),
    path('messages/<int:user_id>/', get_conversation_messages, name='get-conversation-messages'),
    path("teams/", get_all_teams),
    path("my_team/", get_my_team),
    path("create_team/", create_team),
    path("add_team_member/", add_member),
    path("team/delete/<int:team_id>/", delete_team, name="delete_team"),
    path("team/<int:team_id>/", get_team_details),
    path('admin/download-db/', download_db),
    path(
        "message/<int:message_id>/",
        delete_message,
        name="delete_message"
    ),

    path(
        "conversation/<int:conversation_id>/",
        delete_conversation,
        name="delete_conversation"
    ),

    path(
        "remove_team_member/",
        remove_team_member,
        name="remove_team_member"
    ),

    path(
        "request_exit_team/",
        request_exit_team,
        name="request_exit_team"
    ),
]
