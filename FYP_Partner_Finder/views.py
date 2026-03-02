from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializer import UserDetailSerializer, UserProfileSerializer, AppUserSerializer, ConversationSerializer,MessageSerializer
from .models import AppUser, UserProfile, Conversation,Message
from django.core.mail import send_mail
from django.conf import settings

def get_or_create_conversation(user1, user2):
    conversation = Conversation.objects.filter(
        user1=user1, user2=user2
    ).first() or Conversation.objects.filter(
        user1=user2, user2=user1
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            user1=user1,
            user2=user2
        )
    return conversation

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
def get_conversation_messages(request, conversation_id):
    user_id = request.data.get("user_id")
    if not user_id:
        return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Only fetch messages if user belongs to conversation
    messages = Message.objects.filter(
        conversation_id=conversation_id,
        conversation__in=Conversation.objects.filter(user1=user) |Conversation.objects.filter(user2=user)
    ).order_by("timestamp")
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def send_message(request, user_id):
    receiver_id = request.data.get("receiver_id")
    content = request.data.get("content")

    if not receiver_id or not content:
        return Response({"error": "sender_id and content are required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        sender = AppUser.objects.get(id=user_id)
        receiver = AppUser.objects.get(id=receiver_id)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    conversation = get_or_create_conversation(sender, receiver)
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=content
    )
    serializer = MessageSerializer(message)
    return Response(serializer.data, status=status.HTTP_201_CREATED)