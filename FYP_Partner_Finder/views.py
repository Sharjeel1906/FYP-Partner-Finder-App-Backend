from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializer import (
    UserDetailSerializer,
    UserProfileSerializer,
    AppUserSerializer,
    ConversationSerializer,
    MessageListSerializer,
)
from .models import UserProfile, Conversation, Message

# ------------------ Users ------------------ #

@extend_schema(
    responses=UserDetailSerializer(many=True)
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_users_details(request):
    users = User.objects.all()
    serializer = UserDetailSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses=UserDetailSerializer
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_specific_user_details(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User does not exist"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserDetailSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=AppUserSerializer,
    responses=OpenApiResponse(description="User created successfully")
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    data = request.data.copy()
    if "password" not in data:
        return Response(
            {"error": "Password is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = AppUserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserProfileSerializer,
    responses=UserDetailSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    if request.user.id != user_id:
        return Response(
            {"error": "You can only update your own profile"},
            status=status.HTTP_403_FORBIDDEN
        )
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User does not exist"},
            status=status.HTTP_404_NOT_FOUND
        )
    try:
        profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    except UserProfile.DoesNotExist:
        serializer = UserProfileSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=user)
        full_serializer = UserDetailSerializer(user)
        return Response(full_serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------ Email ------------------ #

@extend_schema(
    request=None,
    responses=OpenApiResponse(description="Invitation email sent successfully")
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_invitation_email(request):
    recipient_email = request.data.get("recipient_email")
    recipient_name = request.data.get("recipient_name")

    if not recipient_email or not recipient_name:
        return Response(
            {"error": "Recipient name and email are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = request.user
    sender_name = user.username or user.email or "A user"
    subject = "Invitation from FYP Partner Finder App"
    body = f"""
    Hello {recipient_name},
    
    I hope this message finds you well.
    
    My name is {sender_name}, and I am currently looking for talented and enthusiastic team members to collaborate on a Final Year Project (FYP). 
    I came across your profile and believe your skills would be a great addition to my team.
    
    You are officially invited to join my team for building an innovative project using the FYP Partner Finder App. 
    This project aims to create a meaningful impact while providing an excellent opportunity to enhance your technical and collaborative skills.
    
    If you are interested in joining, please reply to this email, and we can discuss the project details further.
    
    Looking forward to collaborating with you!
    
    Best regards,
    {sender_name}
"""
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        return Response(
            {"success": f"Invitation sent to {recipient_email}"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to send email: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ------------------ Conversations ------------------ #

@extend_schema(
    responses=ConversationSerializer(many=True)
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_all_conversations(request):
    user = request.user
    conversations = (
        Conversation.objects.filter(user1=user) |
        Conversation.objects.filter(user2=user)
    ).order_by("created_at")

    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses=OpenApiResponse(
        response=MessageListSerializer(many=True),
        description="List of messages in conversation"
    )
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, user_id):
    current_user = request.user
    if current_user.id == user_id:
        return Response(
            {"error": "Cannot start conversation with yourself"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "Other user not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    user1, user2 = sorted([current_user, other_user], key=lambda u: u.id)
    conversation, _ = Conversation.objects.get_or_create(user1=user1, user2=user2)
    Message.objects.filter(conversation=conversation, receiver=current_user, is_read=False).update(is_read=True)
    messages = Message.objects.filter(conversation=conversation).order_by("timestamp")
    serializer = MessageListSerializer(messages, many=True)
    return Response({
        "conversation_id": conversation.id,
        "messages": serializer.data
    }, status=status.HTTP_200_OK)