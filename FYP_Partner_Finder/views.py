from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializer import UserDetailSerializer, UserProfileSerializer, AppUserSerializer, ConversationSerializer, \
    MessageListSerializer, MessageSerializer
from .models import AppUser, UserProfile, Conversation,Message
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

@api_view(["GET"])
def get_all_users_details(request):
    users =  AppUser.objects.all()
    serializer = UserDetailSerializer(users, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def get_specific_user_details(request,user_id):
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error":"User does not exist"},status=status.HTTP_404_NOT_FOUND)

    serializer = UserDetailSerializer(user)
    return Response(serializer.data)

@api_view(["POST"])
def create_user(request):
    serializer = AppUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(["POST"])
def update_user(request):
    user_id = request.data.get("user")
    if not user_id:
        return Response({"error": "user ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = int(user_id)
    except ValueError:
        return Response({"error": "user ID must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    # Get the user
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

    # Check if profile exists
    try:
        profile = UserProfile.objects.get(user=user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    except UserProfile.DoesNotExist:
        serializer = UserProfileSerializer(data=request.data)

    # Save profile (and nested skills/experiences)
    if serializer.is_valid():
        serializer.save(user=user)

        # Now return full user details with nested data
        full_serializer = UserDetailSerializer(user)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def send_invitation_email(request):
    sender_id = request.data.get("sender_id")
    recipient_email = request.data.get("recipient_email")
    recipient_name = request.data.get("recipient_name")

    if not recipient_email or not recipient_name:
        return Response({"error": "Recipient name and email are required."},status=status.HTTP_400_BAD_REQUEST)

    try:
        sender_id = int(sender_id)
        user = AppUser.objects.get(id=sender_id)
        sender_name = user.username
    except AppUser.DoesNotExist:
        return Response({"error": "User does not exist"},status=status.HTTP_404_NOT_FOUND)

    # Email subject and body
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
            settings.DEFAULT_FROM_EMAIL,  # Sender email from Django settings
            [recipient_email],
            fail_silently=False,
        )
        return Response({"success": f"Invitation sent to {recipient_email}"})
    except Exception as e:
        return Response({"error": f"Failed to send email: {str(e)}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def get_all_conversations(request,user_id):
    if not user_id:
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=400)
    conversations = (
            Conversation.objects.filter(user1=user) | Conversation.objects.filter(user2=user)
    ).order_by("created_at")
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def get_conversation_messages(request, user_id):
    current_user_id = request.data.get("current_user_id")
    if not current_user_id:
        return Response(
            {"error": "current_user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        current_user = AppUser.objects.get(id=current_user_id)
    except AppUser.DoesNotExist:
        return Response(
            {"error": "Current user not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    try:
        other_user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response(
            {"error": "Other user not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    user1, user2 = sorted([current_user, other_user], key=lambda u: u.id)

    conversation, _ = Conversation.objects.get_or_create(
        user1=user1,
        user2=user2
    )
    Message.objects.filter(
        conversation=conversation,
        receiver=current_user,
        is_read=False
    ).update(is_read=True)

    messages = Message.objects.filter(conversation=conversation).order_by("timestamp")
    serializer = MessageListSerializer(messages, many=True)

    return Response({
        "conversation_id": conversation.id,
        "messages": serializer.data
    })