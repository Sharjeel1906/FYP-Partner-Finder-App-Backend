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
    TeamMemberSerializer,
    TeamSerializer
)
from .models import UserProfile, Conversation, Message, Skill, Team, TeamMember


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
def update_user(request):
    try:
        user = request.user
        data = request.data.copy()
        try:
            profile = UserProfile.objects.get(user=user)
            # UPDATE EXISTING PROFILE
            serializer = UserProfileSerializer(
                profile,
                data=data,
                partial=True
            )
        except UserProfile.DoesNotExist:
            # CREATE NEW PROFILE FROM FORM DATA
            serializer = UserProfileSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
            skills = request.data.getlist("skills")
            if skills:
                Skill.objects.filter(user=user).delete()
                Skill.objects.bulk_create([
                    Skill(user=user, name=s)
                    for s in skills
                ])

            return Response(UserDetailSerializer(user).data)
        return Response(serializer.errors, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
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

# ------------------ Teams------------------ #
@extend_schema(
    responses={
        200: TeamSerializer(many=True),
    },
    description="Get all teams"
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_teams(request):
    teams = Team.objects.all()
    serializer = TeamSerializer(teams, many=True)
    return Response(serializer.data)

@extend_schema(
    request=TeamSerializer,
    responses={
        201: OpenApiResponse(description="Team created successfully"),
        403: OpenApiResponse(description="Only leaders can create teams"),
    },
    description="Create a new team"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_team(request):

    profile = UserProfile.objects.get(user=request.user)
    if profile.role != "Leader":
        return Response(
            {
                "message": "Change your role to Leader in profile to create a team"
            },
            status=403
        )
    team = Team.objects.create(
        team_name=request.data.get("team_name"),
        project_domain=request.data.get("project_domain"),
        req_role=request.data.get("req_role"),
        available_team_size=request.data.get("team_size"),
        group_lead=request.user.username,
    )
    TeamMember.objects.create(
        user=request.user,
        team=team,
        mem_role="leader"
    )
    return Response({
        "message": "Team created successfully",
        "team_id": team.id
    }, status=201)

@extend_schema(
    request=TeamMemberSerializer,
    responses={
        201: OpenApiResponse(description="Member added successfully"),
        400: OpenApiResponse(description="User already in team or team full"),
        404: OpenApiResponse(description="User or Team not found"),
    },
    description="Add member to team"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_member(request):
    try:
        user_to_be_mem = User.objects.get(id=request.data.get("mem_id"))
        team = Team.objects.get(id=request.data.get("team_id"))

        if TeamMember.objects.filter(user=user_to_be_mem, team=team).exists():
            return Response({"message": "You are already in the team already in team"}, status=400)

        if TeamMember.objects.filter(team=team).count() >= team.team_size:
            return Response({"message": "Team is full"}, status=400)

        member = TeamMember.objects.create(
            user=user_to_be_mem,
            team=team,
            mem_role=request.data.get("mem_role", "member")
        )
        return Response({
            "message": "Member added successfully",
            "member_id": member.id
        }, status=201)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=404)

@extend_schema(
    responses={
        200: TeamSerializer,
        404: OpenApiResponse(description="Team not found"),
    },
    description="Get team details with members"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_team_details(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
        members = TeamMember.objects.filter(team=team)

        data = {
            "id": team.id,
            "team_name": team.team_name,
            "project_domain": team.project_domain,
            "req_role": team.req_role,
            "available_team_size": team.team_size,
            "created_at": team.created_at,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "mem_role": m.mem_role,
                    "joined_at": m.joined_at
                }
                for m in members
            ]
        }
        return Response(data)

    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=404)