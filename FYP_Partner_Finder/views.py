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
    TeamSerializer,
    EmailTokenObtainPairSerializer
)
from django.db.models import Count, Max, Prefetch
from .models import UserProfile, Conversation, Message, Skill, Team, TeamMember, TeamRole
from rest_framework_simplejwt.views import TokenObtainPairView
from .email_utils import send_email_async

class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

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
    responses=UserDetailSerializer
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user_details(request):
    try:
        current_id = request.user.id
        user = User.objects.get(id=current_id)
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
        data = request.data

        try:
            profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(
                profile,
                data=data,
                partial=True
            )
        except UserProfile.DoesNotExist:
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
    subject = "Request to Join FYP Team from(FYP Partner Finder App)"
    body = f"""Hello {recipient_name},

    I hope you are doing well.

    My name is {sender_name}, and I recently came across your team profile on the FYP Partner Finder App. I am very interested in your project and would like to request an opportunity to join your team.

    I believe my skills, enthusiasm, and dedication would allow me to contribute positively to your project and collaborate effectively with the team. I am eager to learn, work on innovative ideas, and gain valuable experience throughout the FYP journey.

    If you are open to adding new members to your team, I would be grateful for the opportunity to discuss further details with you.

    Looking forward to your response.

    Best regards,
    {sender_name}
    """
    try:
        send_email_async(subject, body, recipient_email)
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
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_conversations(request):
    user = request.user
    latest_messages = Prefetch(
        "messages",
        queryset=Message.objects.order_by("-timestamp")[:1],
        to_attr="latest_message_list",
    )
    conversations = (
        Conversation.objects.filter(user1=user)
        | Conversation.objects.filter(user2=user)
    ).select_related(
        "user1", "user2", "user1__userprofile", "user2__userprofile"
    ).prefetch_related(
        latest_messages
    ).annotate(
        last_msg_time=Max("messages__timestamp")
    ).order_by("-last_msg_time", "-created_at")

    serializer = ConversationSerializer(
        conversations,
        many=True,
        context={"request": request},
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    responses=OpenApiResponse(
        response=MessageListSerializer(many=True),
        description="List of messages in conversation"
    )
)
@api_view(["GET"])
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

    # ❌ FIX: DO NOT create conversation in GET API
    conversation = Conversation.objects.filter(
        user1=min(current_user, other_user, key=lambda u: u.id),
        user2=max(current_user, other_user, key=lambda u: u.id),
    ).first()

    # If no conversation exists → return empty chat (DO NOT CREATE)
    if not conversation:
        return Response({
            "conversation_id": None,
            "messages": []
        }, status=status.HTTP_200_OK)

    # mark messages as read
    Message.objects.filter(
        conversation=conversation,
        receiver=current_user,
        is_read=False
    ).update(is_read=True)

    # fetch messages
    messages = Message.objects.filter(
        conversation=conversation
    ).order_by("timestamp")

    serializer = MessageListSerializer(
        messages,
        many=True,
        context={"request": request},
    )

    return Response({
        "conversation_id": conversation.id,
        "messages": serializer.data
    }, status=status.HTTP_200_OK)

# ------------------ Chat Delete APIs ------------------ #

@extend_schema(
    responses={
        200: OpenApiResponse(description="Message deleted successfully"),
        404: OpenApiResponse(description="Message not found"),
    }
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id)

        if request.user not in [message.sender, message.receiver]:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        message.delete()

        return Response(
            {"message": "Message deleted successfully"},
            status=status.HTTP_200_OK
        )

    except Message.DoesNotExist:
        return Response(
            {"error": "Message not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    responses={
        200: OpenApiResponse(description="Conversation deleted successfully"),
        404: OpenApiResponse(description="Conversation not found"),
    }
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)

        if request.user not in [conversation.user1, conversation.user2]:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        conversation.delete()

        return Response(
            {"message": "Conversation deleted successfully"},
            status=status.HTTP_200_OK
        )

    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversation not found"},
            status=status.HTTP_404_NOT_FOUND
        )


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
    total_teams = teams.count()
    total_open_spots = 0
    teams_with_open_spots = 0
    for team in teams:
        members_count = TeamMember.objects.filter(team=team).count()
        open_spots = team.available_team_size - members_count
        if open_spots > 0:
            teams_with_open_spots += 1
            total_open_spots += open_spots
    serializer = TeamSerializer(teams, many=True)
    return Response({
        "summary": {
            "total_teams": total_teams,
            "teams_with_open_spots": teams_with_open_spots,
            "total_open_spots": total_open_spots
        },
        "teams": serializer.data
    })

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
    existing_member = TeamMember.objects.filter(user=request.user).first()
    if existing_member:
        return Response(
            {
                "message": "You already have a team and cannot create another one",
                "team_id": existing_member.team.id
            },
            status=400
        )

    team = Team.objects.create(
        team_name=request.data.get("team_name"),
        team_description=request.data.get("team_description"),
        project_domain=request.data.get("project_domain"),
        available_team_size=request.data.get("team_size"),
        group_lead=request.user,
    )
    roles = request.data.get("req_role", [])
    if roles:
        TeamRole.objects.bulk_create([
            TeamRole(team=team, name=r)
            for r in roles
        ])
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
        if TeamMember.objects.filter(user=user_to_be_mem).exists():
            return Response(
                {"message": "User already belongs to a team"},
                status=400
            )
        if TeamMember.objects.filter(user=user_to_be_mem, team=team).exists():
            return Response({"message": "You are already in the team"}, status=400)

        if TeamMember.objects.filter(team=team).count() >= team.available_team_size:
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
            "team_description":team.team_description,
            "project_domain": team.project_domain,
            "roles": [
                {
                    "id": r.id,
                    "name": r.name
                }
                for r in team.roles.all()
            ],
            "available_team_size": team.available_team_size-members.count(),
            "created_at": team.created_at,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "mem_role": m.mem_role,
                    "joined_at": m.joined_at,
                    "domain": (
                        UserProfile.objects.filter(user=m.user)
                        .first()
                        .domain
                        if UserProfile.objects.filter(user=m.user).exists()
                        else ""
                    )
                }
                for m in members
            ],
            "group_lead_name": team.group_lead.username,
            "group_lead_email": team.group_lead.email,
        }
        return Response(data)

    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=404)

@extend_schema(
    responses={
        200: OpenApiResponse(description="User team fetched successfully"),
        404: OpenApiResponse(description="User is not in any team"),
    },
    description="Get current logged-in user's team"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_team(request):
    try:
        membership = (
            TeamMember.objects
            .select_related("team")
            .filter(user=request.user)
            .order_by("-id")
            .first()
        )

        if not membership:
            return Response(
                {"message": "You are not part of any team"},
                status=404
            )
        team = membership.team
        members = TeamMember.objects.filter(team=team)

        return Response({
            "id": team.id,
            "team_name": team.team_name,
            "team_description": team.team_description,
            "project_domain": team.project_domain,
            "roles": [
                {
                    "id": r.id,
                    "name": r.name
                }
                for r in team.roles.all()
            ],
            "available_team_size": team.available_team_size - members.count(),
            "group_lead": team.group_lead.username,
            "created_at": team.created_at,
            "my_role": membership.mem_role,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "mem_role": m.mem_role,
                    "joined_at": m.joined_at,
                    "domain": (
                        UserProfile.objects.filter(user=m.user)
                        .first()
                        .domain
                        if UserProfile.objects.filter(user=m.user).exists()
                        else ""
                    )
                }
                for m in members
            ],
            "leader_name": team.group_lead.username,
            "leader_email": team.group_lead.email,
        }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
@extend_schema(
    responses={
        200: OpenApiResponse(description="Member removed successfully"),
        400: OpenApiResponse(description="Invalid request"),
        404: OpenApiResponse(description="Member not found"),
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_team_member(request):
    user_id = request.data.get("user_id")
    team_id = request.data.get("team_id")

    if not user_id or not team_id:
        return Response(
            {"error": "user_id and team_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        member = TeamMember.objects.select_related("team").get(
            user_id=user_id,
            team_id=team_id
        )

        if member.team.group_lead != request.user:
            return Response(
                {"error": "Only team leader can remove members"},
                status=status.HTTP_403_FORBIDDEN
            )

        if member.user == request.user:
            return Response(
                {"error": "Leader cannot remove himself"},
                status=status.HTTP_400_BAD_REQUEST
            )

        member.delete()
        return Response({"message": "Member removed successfully"})

    except TeamMember.DoesNotExist:
        return Response(
            {"error": "Member not found"},
            status=status.HTTP_404_NOT_FOUND
        )

@extend_schema(
    responses={
        200: OpenApiResponse(description="Exited team successfully"),
        400: OpenApiResponse(description="Invalid request"),
        404: OpenApiResponse(description="Team membership not found"),
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_exit_team(request):
    try:
        membership = TeamMember.objects.get(user=request.user)

        if membership.mem_role.lower() == "leader":
            return Response(
                {"error": "Team leader cannot request to leave the team"},
                status=status.HTTP_400_BAD_REQUEST
            )

        leader_email = membership.team.group_lead.email
        member_name = request.user.username

        subject = "Team Exit Request"
        body = f"""
       Hello Team Leader,

       {member_name} has requested to leave the team "{membership.team.team_name}".

       Please review and take the necessary action.

       Regards,
       FYP Partner Finder
"""
        send_email_async(subject, body, leader_email)
        return Response(
            {"success": "Exit request sent successfully"},
            status=status.HTTP_200_OK
        )

    except TeamMember.DoesNotExist:
        return Response(
            {"error": "You are not part of any team"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to send request: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    responses={
        200: OpenApiResponse(description="Team deleted successfully"),
        403: OpenApiResponse(description="Only team leader can delete the team"),
        404: OpenApiResponse(description="Team not found"),
    },
    description="Delete a team (only by team leader)"
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_team(request, team_id):
    try:
        team = Team.objects.get(id=team_id)

        # check permission
        if team.group_lead != request.user:
            return Response(
                {"error": "Only team leader can delete the team"},
                status=status.HTTP_403_FORBIDDEN
            )

        TeamMember.objects.filter(team=team).delete()
        TeamRole.objects.filter(team=team).delete()

        # delete team
        team.delete()

        return Response(
            {"message": "Team deleted successfully"},
            status=status.HTTP_200_OK
        )

    except Team.DoesNotExist:
        return Response(
            {"error": "Team not found"},
            status=status.HTTP_404_NOT_FOUND
        )