from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
    team_name = models.CharField(max_length=100)
    team_description = models.TextField(default="")
    project_domain = models.CharField(max_length=100)
    available_team_size = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    group_lead = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.team_name

class TeamRole(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="roles"
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class TeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    mem_role = models.CharField(max_length=50, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "team")


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    role = models.CharField(max_length=20)
    semester = models.CharField(max_length=20)
    about = models.TextField(max_length=500)
    section = models.CharField(max_length=200)
    class_name = models.CharField(max_length=100)
    program = models.CharField(max_length=100)

    domain = models.CharField(max_length=100)
    experience = models.CharField(max_length=100)

    pfp_path = models.FileField(upload_to="profile_images/", blank=True)
    cv_path = models.FileField(upload_to="cvs/", blank=True)

    linked_in_link = models.URLField(blank=True)
    github_link = models.URLField(blank=True)
    portfolio_link = models.URLField(blank=True)
    is_online = models.BooleanField(default=False)


class Skill(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="skills"
    )
    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Conversation(models.Model):
    user1 = models.ForeignKey(
        User,
        related_name="conversation_user1",
        on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        User,
        related_name="conversation_user2",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")  # ensures 1-to-1 chat only

    def __str__(self):
        return f"{self.user1} <-> {self.user2}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content}"
