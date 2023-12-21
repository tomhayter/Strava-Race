from django.contrib import admin
from .models import Activity, BestEffort, Milestone, Trophy, UserMilestone, User
# Register your models here.

admin.site.register(Activity)
admin.site.register(BestEffort)
admin.site.register(Milestone)
admin.site.register(Trophy)
admin.site.register(User)
admin.site.register(UserMilestone)
