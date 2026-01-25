from django.db import models
from django.contrib.auth.models import User as WebUser

class User(models.Model):
    webuser = models.OneToOneField(WebUser, on_delete=models.CASCADE, null=True)
    strava_id = models.IntegerField()
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    accessToken = models.CharField(max_length=300)
    refreshToken = models.CharField(max_length=300)
    code = models.CharField(max_length=300)
    expiresAt = models.IntegerField()

    def __str__(self):
        return self.firstName + " " + self.lastName
    

class Trophy(models.Model):
    name = models.CharField(max_length=300)
    value = models.CharField(max_length=100, null=True, blank=True)
    unit = models.CharField(max_length=10, null=True, blank=True)
    holder = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Milestone(models.Model):
    name = models.CharField(max_length=300)
    distance = models.IntegerField()
    imageFile = models.CharField(max_length=100, null=True)
    altitude = models.BooleanField(default=False)
    
    def __str__(self):
        if self.altitude:
            return "Altitude: " + self.name
        return "Distance: " + self.name

class UserMilestone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    dateAchieved = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{str(self.user)} - {str(self.milestone)}"


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    distance = models.FloatField()
    totalElevation = models.FloatField()
    highestPoint = models.FloatField()
    type = models.CharField(max_length=25)
    duration = models.DurationField()
    country = models.CharField(max_length=100)
    startDate = models.DateField()
    stravaID = models.IntegerField()

    def __str__(self):
        return f"{str(self.user)} - {self.name}"

class BestEffort(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    time = models.DurationField()

    def __str__(self):
        return f"{str(self.activity.user)} - {self.name}"