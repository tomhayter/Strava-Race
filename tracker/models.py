from django.db import models

class User(models.Model):
    fullName = models.CharField(max_length=100)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    clientID = models.IntegerField()
    clientSecret = models.CharField(max_length=300)
    accessToken = models.CharField(max_length=300)
    refreshToken = models.CharField(max_length=300)
    code = models.CharField(max_length=300)
    expiresAt = models.IntegerField()

    def __str__(self):
        return self.fullName


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
        return f"{self.user.fullName} - {str(self.milestone)}"


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
        return f"{self.user.fullName} - {self.name}"

class BestEffort(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    time = models.DurationField()

    def __str__(self):
        return f"{self.activity.user.fullName} - {self.name}"