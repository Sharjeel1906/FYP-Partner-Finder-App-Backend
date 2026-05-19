from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Skill, Message, Conversation, TeamMember, Team, TeamRole
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"error": "Invalid email or password"}
            )
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"error": "Invalid email or password"}
            )
        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }


class AppUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("app user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SkillSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # <-- read-only

    class Meta:
        model = Skill
        fields = ["id", "user", "name"]


class UserProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            "id", "user", "gender", "role", "about",
            "section", "class_name", "program",
            "semester", "domain",
            "pfp_path", "cv_path",
            "linked_in_link", "github_link", "portfolio_link",
            "skills"
        ]
        read_only_fields = ["user"]

    def create(self, validated_data):
        skills_data = validated_data.pop("skills", [])

        profile = UserProfile.objects.create(**validated_data)

        for skill in skills_data:
            Skill.objects.create(user=profile.user, name=skill["name"])

        return profile

    def update(self, instance, validated_data):
        skills_data = validated_data.pop("skills", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        Skill.objects.filter(user=instance.user).delete()

        for skill in skills_data:
            Skill.objects.create(user=instance.user, name=skill["name"])

        return instance


# -------------------Nested Serializer ------------------#
class SkillNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["name"]


class UserProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "gender",
            "role",
            "about",
            "section",
            "class_name",
            "program",
            "semester",
            "domain",
            "pfp_path",
            "cv_path",
            "linked_in_link",
            "github_link",
            "portfolio_link",
            "experience"
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileNestedSerializer(source="userprofile", read_only=True)
    skills = SkillNestedSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile", "skills"]


# ------------------Messenger-----------------------#
class MessageSerializer(serializers.ModelSerializer):
    sender = AppUserSerializer(read_only=True)
    receiver = AppUserSerializer(read_only=True)  # NEW

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "receiver",  # NEW
            "content",
            "timestamp",
            "is_read"
        ]


class MessageListSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id")
    receiver_id = serializers.IntegerField(source="receiver.id")

    class Meta:
        model = Message
        fields = [
            "id",
            "sender_id",
            "receiver_id",
            "content",
            "timestamp",
            "is_read",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    user1 = AppUserSerializer(read_only=True)
    user2 = AppUserSerializer(read_only=True)

    class Meta:
        unique_together = ("user1", "user2")
        model = Conversation
        fields = [
            "id",
            "user1",
            "user2",
            "created_at",
        ]

        # -------------------Teams Serializer ------------------#


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "user", "mem_role", "joined_at"]


class TeamRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamRole
        fields = ["id", "name"]

class TeamSerializer(serializers.ModelSerializer):

    members = TeamMemberSerializer(
        source="team_member_set",
        many=True,
        read_only=True
    )

    roles = TeamRoleSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Team

        fields = [
            "id",
            "team_name",
            "project_domain",
            "available_team_size",
            "created_at",
            "members",
            "group_lead",
            "roles",
        ]