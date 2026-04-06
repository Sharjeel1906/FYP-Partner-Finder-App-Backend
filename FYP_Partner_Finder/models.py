from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.BooleanField()
    role = models.BooleanField()
    about = models.TextField()

    qualifications = models.CharField(max_length=200)
    class_name = models.CharField(max_length=100)
    program = models.CharField(max_length=100)

    semester = models.PositiveSmallIntegerField()
    domain = models.CharField(max_length=100)
    whatsapp_no = models.CharField(max_length=20)
    passing_year = models.PositiveSmallIntegerField()

    pfp_path  = models.FileField(upload_to="profile_images/",blank=True)
    cv_path = models.FileField(upload_to="cvs/",blank =True)

    linked_in_link = models.URLField(blank=True)
    github_link = models.URLField(blank=True)
    portfolio_link = models.URLField(blank=True)

class Experience(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="experiences"
    )
    status = models.CharField(max_length=100,blank=True)
    title = models.CharField(max_length=150,blank=True)
    company = models.CharField(max_length=150,blank=True)
    duration = models.CharField(max_length=50,blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class Skill(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="skills"
    )
    name = models.CharField(max_length=100,blank=True)

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