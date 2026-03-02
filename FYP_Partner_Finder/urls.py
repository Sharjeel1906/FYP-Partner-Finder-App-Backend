from django.urls import path
from .views import get_all_users_details, get_specific_user_details,update_user,create_user,send_invitation_email,get_all_conversations,get_conversation_messages

urlpatterns = [
    path("users/", get_all_users_details, name="all-users"),
    path("users/<int:user_id>/", get_specific_user_details, name="user-detail"),
    path("update-user/", update_user, name="update-user"),
    path("create-user/", create_user, name="create-user"),
    path("send_email/", send_invitation_email, name="send-invitation-email"),
    path('inbox/<int:user_id>/',get_all_conversations, name='get-all-conversations'),
    path('messages/<int:user_id>/', get_conversation_messages,name='get-conversation-messages')
]