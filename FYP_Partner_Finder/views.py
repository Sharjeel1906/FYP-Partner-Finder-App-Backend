from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse

from myproject import settings
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
from django.http import FileResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

# ------------------ Users ------------------ #
@api_view(["GET"])
@permission_classes([AllowAny])
def test_template(request):
    import os
    import django.template.loader as loader

    template_path = os.path.join(str(settings.BASE_DIR), 'templates', 'registration', 'password_reset_confirm.html')
    file_exists = os.path.exists(template_path)

    t = loader.get_template('registration/password_reset_confirm.html')

    return Response({
        "template_path": t.origin.name,
        "base_dir": str(settings.BASE_DIR),
        "file_exists_at": template_path,
        "file_exists": file_exists,
    })
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get("email", "").strip()
    if not email:
        return Response({"error": "Email is required"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return Response({"message": "Reset link sent"}, status=200)

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"https://fyp-partner-finder-app-backend-production.up.railway.app/FYP_Partner_Finder/reset/{uid}/{token}/"

    send_email_async(
        subject="Reset Your Password — dEVPartner App",
        body_text=f"Click to reset your password: {reset_link}",
        recipient_email=email,
        body_html=f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f0f2f5; font-family: 'Arial', sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f2f5; padding: 48px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.10);">

              <!-- Header -->
              <tr>
                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 44px 48px 36px 48px; text-align:center;">
                  <p style="color:rgba(255,255,255,0.75); margin:0 0 10px 0; font-size:12px; text-transform:uppercase; letter-spacing:2px;">
                    dEVPartner App
                  </p>
                  <h1 style="color:#ffffff; margin:0 0 8px 0; font-size:28px; font-weight:700; letter-spacing:0.3px;">
                    Password Reset
                  </h1>
                  <p style="color:rgba(255,255,255,0.80); margin:0; font-size:14px;">
                    Click below to set a new password
                  </p>
                </td>
              </tr>

              <!-- Sender Badge -->
              <tr>
                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0 48px 32px 48px; text-align:center;">
                  <table cellpadding="0" cellspacing="0" align="center">
                    <tr>
                      <td style="background-color:#ffffff; border-radius:50px; padding: 10px 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);">
                        <span style="color:#667eea; font-size:15px; font-weight:700;">
                          🔐 Password reset requested
                        </span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding: 44px 48px 12px 48px;">
                  <p style="color:#222222; font-size:17px; font-weight:600; margin:0 0 24px 0;">
                    Hello {user.username},
                  </p>
                  <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 18px 0;">
                    We received a request to reset your password. Click the button below to set a new one.
                    This link expires in <strong style="color:#333333;">1 hour</strong>.
                  </p>
                  <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 32px 0;">
                    If you didn't request this, you can safely ignore this email — your password won't change.
                  </p>

                  <!-- Reset Button -->
                  <table cellpadding="0" cellspacing="0" style="margin: 0 auto 32px;">
                    <tr>
                      <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:30px; padding:14px 36px; text-align:center;">
                        <a href="{reset_link}" style="color:#ffffff; font-size:16px; font-weight:700; text-decoration:none; letter-spacing:0.5px;">
                          RESET MY PASSWORD
                        </a>
                      </td>
                    </tr>
                  </table>

                  <!-- Note Box -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:36px;">
                    <tr>
                      <td style="background-color:#f8f9ff; border-left:4px solid #667eea; border-radius:8px; padding:18px 24px;">
                        <p style="margin:0 0 6px 0; color:#667eea; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">
                          🔒 Security tip
                        </p>
                        <p style="margin:0; color:#444444; font-size:14px; line-height:1.7;">
                          Never share this link with anyone. dEVPartner staff will never ask for your password.
                        </p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Signature -->
              <tr>
                <td style="padding: 0 48px 36px 48px;">
                  <hr style="border:none; border-top:1px solid #eeeeee; margin:0 0 24px 0;">
                  <p style="color:#555555; font-size:15px; line-height:1.8; margin:0 0 4px 0;">
                    Regards,
                  </p>
                  <table cellpadding="0" cellspacing="0" style="margin-top:12px;">
                    <tr>
                      <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:8px; padding:12px 28px;">
                        <span style="color:#ffffff; font-size:15px; font-weight:700;">
                          dEVPartner App
                        </span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color:#f8f9ff; padding:24px 48px; text-align:center; border-top:1px solid #eeeeee;">
                  <p style="color:#aaaaaa; font-size:12px; margin:0; line-height:1.8;">
                    This email was sent via <strong>dEVPartner App</strong>.<br>
                    If you did not request a password reset, please ignore this email.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """
    )

    return Response({"message": "Reset link sent"}, status=200)

def download_db(request):
    return FileResponse(
        open('/app/db.sqlite3', 'rb'),
        as_attachment=True,
        filename='db_production.sqlite3'
    )
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
    sender_email = user.email or ""
    subject = "Request to Join FYP Team — dEVPartner App"

    # Plain text fallback
    body_text = f"""Hello {recipient_name},

I hope you are doing well.

My name is {sender_name} ({sender_email}), and I recently came across your team profile on the dEVPartner App. I am very interested in your project and would like to request an opportunity to join your team.

I believe my skills, enthusiasm, and dedication would allow me to contribute positively to your project and collaborate effectively with the team. I am eager to learn, work on innovative ideas, and gain valuable experience throughout the FYP journey.

If you are open to adding new members to your team, I would be grateful for the opportunity to discuss further details with you.

Looking forward to your response.

Best regards,
{sender_name}
{sender_email}
"""

    body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f0f2f5; font-family: 'Arial', sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f2f5; padding: 48px 0;">
    <tr>
      <td align="center">

        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.10);">

          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 44px 48px 36px 48px; text-align:center;">
              <p style="color:rgba(255,255,255,0.75); margin:0 0 10px 0; font-size:12px; text-transform:uppercase; letter-spacing:2px;">
                dEVPartner App
              </p>
              <h1 style="color:#ffffff; margin:0 0 8px 0; font-size:28px; font-weight:700; letter-spacing:0.3px;">
                Team Join Request
              </h1>
              <p style="color:rgba(255,255,255,0.80); margin:0; font-size:14px;">
                Someone wants to collaborate with you
              </p>
            </td>
          </tr>

          <!-- Sender Badge -->
          <tr>
            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0 48px 32px 48px; text-align:center;">
              <table cellpadding="0" cellspacing="0" align="center">
                <tr>
                  <td style="background-color:#ffffff; border-radius:50px; padding: 10px 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);">
                    <span style="color:#667eea; font-size:15px; font-weight:700;">
                      ✉ Request from &nbsp;<strong style="color:#764ba2;">{sender_name}</strong>
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 44px 48px 12px 48px;">

              <p style="color:#222222; font-size:17px; font-weight:600; margin:0 0 24px 0;">
                Hello {recipient_name},
              </p>

              <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 18px 0;">
                I hope you are doing well.
              </p>

              <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 18px 0;">
                My name is <strong style="color:#333333;">{sender_name}</strong>
                (<a href="mailto:{sender_email}" style="color:#667eea; text-decoration:none;">{sender_email}</a>),
                and I recently came across your team profile on the
                <strong style="color:#667eea;">dEVPartner App</strong>.
                I am very interested in your project and would like to request an opportunity to join your team.
              </p>

              <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 18px 0;">
                I believe my skills, enthusiasm, and dedication would allow me to contribute positively
                to your project and collaborate effectively with the team. I am eager to learn, work on
                innovative ideas, and gain valuable experience throughout the FYP journey.
              </p>

              <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 32px 0;">
                If you are open to adding new members to your team, I would be grateful for the opportunity
                to discuss further details with you.
              </p>

              <!-- Highlighted Note Box -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:36px;">
                <tr>
                  <td style="background-color:#f8f9ff; border-left:4px solid #667eea; border-radius:8px; padding:18px 24px;">
                    <p style="margin:0 0 6px 0; color:#667eea; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">
                      📲 Next Step
                    </p>
                    <p style="margin:0; color:#444444; font-size:14px; line-height:1.7;">
                      Open the <strong>dEVPartner App</strong> to view
                      <strong>{sender_name}'s</strong> profile and respond to this request.
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Signature -->
          <tr>
            <td style="padding: 0 48px 36px 48px;">
              <hr style="border:none; border-top:1px solid #eeeeee; margin:0 0 24px 0;">

              <p style="color:#555555; font-size:15px; line-height:1.8; margin:0 0 4px 0;">
                Looking forward to your response.
              </p>
              <p style="color:#555555; font-size:15px; margin:0 0 20px 0;">
                Best regards,
              </p>

              <!-- Sender Card -->
              <table cellpadding="0" cellspacing="0" style="background-color:#f8f9ff; border-radius:10px; overflow:hidden; border:1px solid #e8eaf6;">
                <tr>
                  <td style="padding:16px 24px;">
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:50%; width:42px; height:42px; text-align:center; vertical-align:middle;">
                          <span style="color:#ffffff; font-size:18px; font-weight:700; line-height:42px;">
                            {sender_name[0].upper()}
                          </span>
                        </td>
                        <td style="padding-left:14px;">
                          <p style="margin:0 0 3px 0; color:#222222; font-size:15px; font-weight:700;">
                            {sender_name}
                          </p>
                          <p style="margin:0; font-size:13px;">
                            <a href="mailto:{sender_email}" style="color:#667eea; text-decoration:none;">
                              {sender_email}
                            </a>
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f8f9ff; padding:24px 48px; text-align:center; border-top:1px solid #eeeeee;">
              <p style="color:#aaaaaa; font-size:12px; margin:0; line-height:1.8;">
                This email was sent via <strong>dEVPartner App</strong>.<br>
                If you did not expect this message, you can safely ignore it.
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""

    try:
        send_email_async(subject, body_text, recipient_email, body_html=body_html)
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
        member_email = request.user.email or ""
        team_name = membership.team.team_name

        subject = f"Team Exit Request — {team_name} | dEVPartner"

        body_text = f"""Hello Team Leader,

{member_name} ({member_email}) has requested to leave the team "{team_name}".

Please review and take the necessary action by opening the dEVPartner App.

Regards,
dEVPartner App
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f0f2f5; font-family: 'Arial', sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f2f5; padding: 48px 0;">
    <tr>
      <td align="center">

        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.10);">

          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%); padding: 44px 48px 36px 48px; text-align:center;">
              <p style="color:rgba(255,255,255,0.75); margin:0 0 10px 0; font-size:12px; text-transform:uppercase; letter-spacing:2px;">
                dEVPartner App
              </p>
              <h1 style="color:#ffffff; margin:0 0 8px 0; font-size:28px; font-weight:700; letter-spacing:0.3px;">
                Team Exit Request
              </h1>
              <p style="color:rgba(255,255,255,0.80); margin:0; font-size:14px;">
                A team member has requested to leave
              </p>
            </td>
          </tr>

          <!-- Member Badge -->
          <tr>
            <td style="background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%); padding: 0 48px 32px 48px; text-align:center;">
              <table cellpadding="0" cellspacing="0" align="center">
                <tr>
                  <td style="background-color:#ffffff; border-radius:50px; padding: 10px 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);">
                    <span style="color:#f5576c; font-size:15px; font-weight:700;">
                      🚪 Exit request from &nbsp;<strong style="color:#c0392b;">{member_name}</strong>
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 44px 48px 12px 48px;">

              <p style="color:#222222; font-size:17px; font-weight:600; margin:0 0 24px 0;">
                Hello Team Leader,
              </p>

              <p style="color:#555555; font-size:15px; line-height:1.9; margin:0 0 18px 0;">
                A member of your team has submitted a request to leave. Please review the details below.
              </p>

              <!-- Info Card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                <tr>
                  <td style="background-color:#fff5f5; border-left:4px solid #f5576c; border-radius:8px; padding:20px 24px;">

                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding-bottom:12px;">
                          <p style="margin:0 0 4px 0; color:#aaaaaa; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Member Name</p>
                          <p style="margin:0; color:#222222; font-size:16px; font-weight:700;">{member_name}</p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding-bottom:12px;">
                          <p style="margin:0 0 4px 0; color:#aaaaaa; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Member Email</p>
                          <p style="margin:0; font-size:14px;">
                            <a href="mailto:{member_email}" style="color:#f5576c; text-decoration:none;">{member_email}</a>
                          </p>
                        </td>
                      </tr>
                      <tr>
                        <td>
                          <p style="margin:0 0 4px 0; color:#aaaaaa; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Team Name</p>
                          <p style="margin:0; color:#222222; font-size:16px; font-weight:700;">"{team_name}"</p>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>

              <!-- Action Note -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:36px;">
                <tr>
                  <td style="background-color:#f8f9ff; border-left:4px solid #667eea; border-radius:8px; padding:18px 24px;">
                    <p style="margin:0 0 6px 0; color:#667eea; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">
                      📲 Action Required
                    </p>
                    <p style="margin:0; color:#444444; font-size:14px; line-height:1.7;">
                      Please open the <strong>dEVPartner App</strong> to review this request and take the necessary action.
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Signature -->
          <tr>
            <td style="padding: 0 48px 36px 48px;">
              <hr style="border:none; border-top:1px solid #eeeeee; margin:0 0 24px 0;">
              <p style="color:#555555; font-size:15px; line-height:1.8; margin:0 0 4px 0;">
                Regards,
              </p>
              <table cellpadding="0" cellspacing="0" style="margin-top:12px;">
                <tr>
                  <td style="background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%); border-radius:8px; padding:12px 28px;">
                    <span style="color:#ffffff; font-size:15px; font-weight:700;">
                      dEVPartner App
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#fff5f5; padding:24px 48px; text-align:center; border-top:1px solid #eeeeee;">
              <p style="color:#aaaaaa; font-size:12px; margin:0; line-height:1.8;">
                This email was sent via <strong>dEVPartner App</strong>.<br>
                If you did not expect this message, you can safely ignore it.
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""

        send_email_async(subject, body_text, leader_email, body_html=body_html)
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