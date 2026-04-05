from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Skill, Experience,Message,Conversation

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

class ExperienceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # <-- read-only
    class Meta:
        model = Experience
        fields = ["id", "user", "position", "title", "company", "duration"]

class UserProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, required=False)
    experiences = ExperienceSerializer(many=True, required=False)
    class Meta:
        model = UserProfile
        fields = [
                "id", "user", "gender", "role", "about",
                "section", "class_name", "program",
                "semester", "domain", "whatsapp_no", "passing_year",
                "pfp_path", "cv_path",
                "linked_in_link", "github_link", "portfolio_link",
                "skills", "experiences"
        ]
        read_only_fields = ["user"]
    def create(self, validated_data):
        skills_data = validated_data.pop("skills", [])
        experiences_data = validated_data.pop("experiences", [])

        profile = UserProfile.objects.create(**validated_data)
        user = profile.user

        # Add skills
        for skill in skills_data:
            Skill.objects.create(user=user, **skill)

        # Add experiences
        for exp in experiences_data:
            Experience.objects.create(user=user, **exp)

        return profile

    def update(self, instance, validated_data):
        skills_data = validated_data.pop("skills", [])
        experiences_data = validated_data.pop("experiences", [])

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        user = instance.user

        # Add new skills without deleting existing ones
        for skill in skills_data:
            Skill.objects.create(user=user, **skill)

        # Add new experiences without deleting existing ones
        for exp in experiences_data:
            Experience.objects.create(user=user, **exp)

        return instance

#-------------------Nested Serializer ------------------#
class SkillNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["name"]

class ExperienceNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ["position", "title", "company", "duration"]

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
            "whatsapp_no",
            "passing_year",
            "pfp_path",
            "cv_path",
            "linked_in_link",
            "github_link",
            "portfolio_link"
        ]

class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileNestedSerializer(source="userprofile", read_only=True)
    skills = SkillNestedSerializer(many=True, read_only=True)
    experiences = ExperienceNestedSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile", "skills", "experiences"]

#------------------Messenger-----------------------#
class MessageSerializer(serializers.ModelSerializer):
    sender = AppUserSerializer(read_only=True)
    receiver = AppUserSerializer(read_only=True)  # NEW

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "receiver",      # NEW
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