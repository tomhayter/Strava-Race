from django.shortcuts import render, redirect
from .models import Activity, BestEffort, Milestone, Trophy, User, UserMilestone
from stravalib.client import Client
from stravalib import unit_helper
import time as t
from datetime import timedelta
from django.conf import settings
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as WebUser
from  django.contrib.auth.forms import UserCreationForm
from .forms import LoginForm

TRACKED_BEST_EFFORTS = ["5k", "10k", "Half-Marathon", "Marathon"]

class Statistics:
    def __init__(self, userID):
        self.total_distance = 0
        self.run_distance = 0
        self.cycle_distance = 0
        self.hike_distance = 0
        self.total_elevation = 0
        self.total_time = timedelta()
        self.countries = set()
        self.best_5k = timedelta.max
        self.best_10k = timedelta.max
        self.best_half = timedelta.max
        # self.best_marathon = timedelta.max

        self.num_activities = 0
        self.longest_run = 0
        self.longest_cycle = 0
        self.longest_hike = 0
        self.largest_climb = 0
        self.highest_point = 0

        for activity in Activity.objects.filter(user__id=userID):
            self.total_distance += activity.distance
            self.total_elevation += activity.totalElevation
            self.largest_climb = max(self.largest_climb, activity.totalElevation)
            self.total_time += activity.duration
            self.num_activities += 1
            self.highest_point = max(self.highest_point, activity.highestPoint)
            self.countries.add(activity.country)
            if activity.type == "Run":
                self.longest_run = max(self.longest_run, activity.distance)
                self.run_distance += activity.distance      
            elif activity.type == "Ride":
                self.longest_cycle = max(self.longest_cycle, activity.distance)
                self.cycle_distance += activity.distance
            elif activity.type == "Hike" or activity.type == "Walk":
                self.longest_hike = max(self.longest_hike, activity.distance)
                self.hike_distance += activity.distance

        for effort in BestEffort.objects.filter(activity__user__id=userID):
            if effort.name == "5k":
                self.best_5k = min(self.best_5k, effort.time)
            elif effort.name == "10k":
                self.best_10k = min(self.best_10k, effort.time)
            elif effort.name == "Half-Marathon":
                self.best_half = min(self.best_half, effort.time) 


class Cache:
    def __init__(self):
        # TODO: Update cache regularly using last updated time
        self.users = {}

    def add_user(self, user):
        self.users[user] = Statistics(user)

CACHE = Cache()

def get_trophies():        
    return Trophy.objects.all()

def get_trophies_for_user(userID):
    return Trophy.objects.filter(holder__id=userID)

def get_milestones(altitudeBool):
    return Milestone.objects.filter(altitude=altitudeBool)

def get_milestones_for_user(altitudeBool, userID):
    return UserMilestone.objects.filter(user__id=userID, milestone__altitude=altitudeBool)

def get_nearest_milestones(milestones, total_distance):
    # Get closest and completed milestones
    closest_below = Milestone(name="", distance=0)
    closest_above = Milestone(name="", distance=50000)
    completed = []

    for m in milestones:
        if m.milestone.distance < total_distance:
            completed.append(m)
            if m.milestone.distance > closest_below.distance:
                closest_below = m.milestone
        else:
            if m.milestone.distance < closest_above.distance:
                closest_above = m.milestone

    return closest_below, closest_above, completed

def update_trophy(trophy_name, tuple):
    trophy = Trophy.objects.get(name=trophy_name)
    trophy.holder = tuple[0]
    trophy.value = tuple[1]
    trophy.save()

def update_trophy_winners():
    most_activities = (None, 0)
    most_running = (None, 0)
    most_cycling = (None, 0)
    most_hiking = (None, 0)
    longest_run = (None, 0)
    longest_cycle = (None, 0)
    longest_hike = (None, 0)
    largest_climb = (None, 0)
    most_climbing = (None, 0)
    most_time = (None, timedelta())
    highest_point = (None, 0)
    most_countries = (None, 0)
    fastest_5k = (None, timedelta.max)
    fastest_10k = (None, timedelta.max)
    fastest_half = (None, timedelta.max)
    for user in User.objects.all():
        stats = get_stats(user.id)
        if most_activities[1] < stats.num_activities:
            most_activities = (user, stats.num_activities)

        if most_running[1] < stats.run_distance:
            most_running = (user, round(stats.run_distance, 2))

        if most_cycling[1] < stats.cycle_distance:
            most_cycling = (user, round(stats.cycle_distance, 2))

        if most_hiking[1] < stats.hike_distance:
            most_hiking = (user, round(stats.hike_distance, 2))

        if longest_run[1] < stats.longest_run:
            longest_run = (user, round(stats.longest_run, 2))

        if longest_cycle[1] < stats.longest_cycle:
            longest_cycle = (user, round(stats.longest_cycle, 2))

        if longest_hike[1] < stats.longest_hike:
            longest_hike = (user, round(stats.longest_hike, 2))

        if largest_climb[1] < stats.largest_climb:
            largest_climb = (user, round(stats.largest_climb))

        if most_climbing[1] < stats.total_elevation:
            most_climbing = (user, round(stats.total_elevation))

        if most_time[1] < stats.total_time:
            most_time = (user, stats.total_time)

        if highest_point[1] < stats.highest_point:
            highest_point = (user, round(stats.highest_point))

        if most_countries[1] <= len(stats.countries):
            most_countries = (user, len(stats.countries))

        if fastest_5k[1] > stats.best_5k:
            fastest_5k = (user, stats.best_5k)

        if fastest_10k[1] > stats.best_10k:
            fastest_10k = (user, stats.best_10k)

        if fastest_half[1] > stats.best_half:
            fastest_half = (user, stats.best_half)

    update_trophy("Most Elevation Gained", most_climbing)
    update_trophy("Longest Run", longest_run)
    update_trophy("Longest Ride", longest_cycle)
    update_trophy("Longest Hike", longest_hike)
    update_trophy("Biggest Climb", largest_climb)
    update_trophy("Most Activities", most_activities)
    update_trophy("Most Time Recorded", most_time)
    update_trophy("Most Running Distance", most_running)
    update_trophy("Most Cycling Distance", most_cycling)
    update_trophy("Most Hiking Distance", most_hiking)
    update_trophy("Most Countries Visited", most_countries)
    update_trophy("Fastest 5k", fastest_5k)
    update_trophy("Fastest 10k", fastest_10k)
    update_trophy("Fastest Half Marathon", fastest_half)
    update_trophy("Highest Point", highest_point)

def update_altitude_milestones():
    users = User.objects.all()
    altitude_milestones = Milestone.objects.filter(altitude=True)
    for user in users:
        activities = get_activities(user.id)
        total = get_stats(user.id).total_elevation
        for milestone in altitude_milestones:
            milestone_distance = milestone.distance
            if milestone_distance > total:
                instance = UserMilestone.objects.get(user=user, milestone=milestone)
                instance.dateAchieved = None
                instance.save()
                continue
            running_total = 0
            for activity in activities:
                running_total += activity.totalElevation
                if running_total > milestone_distance:
                    instance = UserMilestone.objects.get(user=user, milestone=milestone)
                    instance.dateAchieved = activity.startDate
                    instance.save()
                    break

def update_milestones():
    # Update the milestone dates achieved
    users = User.objects.all()
    altitude_milestones = Milestone.objects.filter(altitude=False)
    for user in users:
        activities = get_activities(user.id)
        total = get_stats(user.id).total_distance
        for milestone in altitude_milestones:
            milestone_distance = milestone.distance
            if milestone_distance > total:
                instance = UserMilestone.objects.get(user=user, milestone=milestone)
                instance.dateAchieved = None
                instance.save()
                continue
            running_total = 0
            for activity in activities:
                running_total += activity.distance
                if running_total > milestone_distance:
                    instance = UserMilestone.objects.get(user=user, milestone=milestone)
                    instance.dateAchieved = activity.startDate
                    instance.save()
                    break

def get_new_activities():
    for u in User.objects.all():
        client = get_client_for_user(u.id)
        try:
            activities = list(client.get_activities(limit=100, after=f"2023-08-24T00:00:00Z"))
        except:
            return
        activities = sorted(activities, key=lambda x: x.start_date)

        stored_activities = Activity.objects.filter(user__id=u.id)
        stored_ids = [a.stravaID for a in stored_activities]
        for a in activities:
            if a.id in stored_ids:
                continue
            adb = Activity.objects.create(
                user=u,
                name=a.name,
                distance=unit_helper.kilometer(a.distance).magnitude,
                totalElevation=unit_helper.meter(a.total_elevation_gain).magnitude,
                highestPoint=a.elev_high,
                type=a.type,
                duration=a.moving_time.timedelta(),
                country=a.location_country or "United Kingdom",
                startDate=a.start_date,
                stravaID=a.id)
            # if a.type == "Run":
            #     abe = client.get_activity(a.id, True)
            #     if abe.best_efforts:
            #         for be in abe.best_efforts:
            #             if be.name not in TRACKED_BEST_EFFORTS:
            #                 continue
            #             BestEffort.objects.create(
            #                 activity=adb,
            #                 name=be.name,
            #                 time=be.elapsed_time
            #             )

def get_client_for_user(userID):
    # Get the client for a user.
    user = User.objects.get(id=userID)

    # Strava authentication
    client = Client()

    if t.time() > user.expiresAt:
        print('Token has expired, will refresh')
        refresh_response = client.refresh_access_token(client_id=settings.STRAVA_CLIENT_ID, client_secret=settings.STRAVA_CLIENT_SECRET,
                                                    refresh_token=user.refreshToken)
        print('Refreshed token saved to file')
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']
        user.accessToken = refresh_response['access_token']
        user.refreshToken = refresh_response['refresh_token']
        user.expiresAt = refresh_response['expires_at']
        user.save()
    else:
        print('Token still valid, expires at {}'
            .format(t.strftime("%a, %d %b %Y %H:%M:%S %Z", t.localtime(user.expiresAt))))
        client.access_token = user.accessToken
        client.refresh_token = user.refreshToken
        client.token_expires_at = user.expiresAt

    return client

def get_stats(user):
    if user not in CACHE.users:
        CACHE.add_user(user)
    return CACHE.users[user]

def get_activities(userID):
    return Activity.objects.filter(user__id=userID)

def get_athlete(userID):
    return User.objects.get(id=userID)

def home(request):
    # TODO: Cron these
    get_new_activities()
    update_milestones()
    update_altitude_milestones()
    update_trophy_winners()

    rankings = []
    cumulative = 0
    for user in User.objects.all():
        # Get distance data
        total = get_stats(user.id).total_distance
        rankings.append((user.firstName, user.id, total))
        cumulative += total
    
    if len(rankings) < 3:
        for _ in range(3-len(rankings)):
            rankings.append(("", 0 ,0))

    rankings = sorted(rankings, key=lambda x: x[1])
    
    context = {
        "logged_in": request.user.is_authenticated,
        "first": rankings[-1][0],
        "second" : rankings[-2][0],
        "third" : rankings[-3][0],
        "first_id": rankings[-1][1],
        "second_id": rankings[-2][1],
        "third_id": rankings[-3][1],
        "first_distance" : round(rankings[-1][2]),
        "second_distance" : round(rankings[-2][1]),
        "third_distance" : round(rankings[-3][1]),
        "cumulative_distance" : round(cumulative)
    }
    return render(request, "tracker/home.html", context)

def user(request):
    userID = int(request.GET.get("name"))
    milestones = get_milestones_for_user(False, userID)
    altitude_milestones = get_milestones_for_user(True, userID)
    # Get distance data
    athlete = get_athlete(userID)
    stats = get_stats(userID)
    total = stats.total_distance
    run = stats.run_distance
    cycle = stats.cycle_distance
    hike = stats.hike_distance
    altitude = stats.total_elevation
    completed_altitudes = [a for a in altitude_milestones if a.dateAchieved]

    my_trophies = get_trophies_for_user(userID)

    closest_below, closest_above, completed = get_nearest_milestones(milestones, total)
    completed.reverse()
    completed_altitudes.reverse()

    progress = 100 * (total - closest_below.distance)/(closest_above.distance - closest_below.distance)

    context = {
        "logged_in": request.user.is_authenticated,
        "name": athlete.firstName + " " + athlete.lastName,
        "total_distance" : round(total, 2),
        "run_distance" : round(run, 2),
        "cycle_distance" : round(cycle, 2),
        "hike_distance" : round(hike, 2),
        "altitude": round(altitude, 1),
        "last_milestone" : closest_below,
        "next_milestone": closest_above,
        "progress": round(progress),
        "trophies" : my_trophies,
        "completed_milestones": completed,
        "completed_altitude_milestones": completed_altitudes,
        "arg_name": userID
    }
    return render(request, "tracker/user.html", context)

def milestones(request):
    userID = int(request.GET.get("name"))
    milestones = get_milestones_for_user(False, userID)
    context = {
        "logged_in": request.user.is_authenticated,
        "milestones": milestones,
        "arg_name": userID,
        "unit": "km"
    }
    return render(request, "tracker/milestones.html", context)

def trophies(request):
    trophies = get_trophies()
    context = {
        "logged_in": request.user.is_authenticated,
        "trophies": trophies
    }
    return render(request, "tracker/trophies.html", context)

def altitude_milestones(request):
    userID = int(request.GET.get("name"))
    milestones = get_milestones_for_user(True, userID)
    context = {
        "logged_in": request.user.is_authenticated,
        "milestones": milestones,
        "arg_name": userID,
        "unit": "m"
    }
    return render(request, "tracker/milestones.html", context)

def link_strava(request):
    strava_auth_url = (
        "https://www.strava.com/oauth/authorize"
        "?client_id={client_id}"
        "&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&approval_prompt=auto"
        "&scope=activity:read_all"
    ).format(
        client_id=settings.STRAVA_CLIENT_ID,
        redirect_uri=request.build_absolute_uri("/tracker/strava_callback/")
    )

    return redirect(strava_auth_url)

def unlink_strava(request):
    user_id = request.GET.get("user")
    if request.user.is_authenticated and request.user.id == user_id:
        u = User.objects.get(id = user_id)
        u.delete()

    return redirect("/account/")

def delete_account(request):
    user_id = request.GET.get("user")
    if request.user.is_authenticated and request.user.id == user_id:
        try:
            u = WebUser.objects.get(id = user_id)
            u.delete()
            err = "The user is deleted"

        except Exception as e: 
            return render(request, 'front.html',{'err':e.message})

        return render(request, 'front.html') 
        

    return redirect("/tracker/")

def load_signup(request):
    error_message = ""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = WebUser.objects.create_user(username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            login(request, user)
            return redirect("/tracker/account")
        else:
            error_message = form.errors.as_ul
    signup_form = UserCreationForm()
    context = {
        "error_message": error_message,
        "logged_in": request.user.is_authenticated,
        "sign_up_form": signup_form
    }
    return render(request, "tracker/signup.html", context)


def load_login(request):
    error_message = ""
    if request.method == "POST":
        user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
        if user is None:
            # Failed
            error_message = "Username or password incorrect."
        else:
            login(request, user)
            return redirect("/tracker/account")
    
    login_form = LoginForm()
    context = {
        "error_message": error_message,
        "logged_in": request.user.is_authenticated,
        "login_form": login_form
    }
    return render(request, "tracker/login.html", context)
     

def attempt_logout(request):
    logout(request)
    return redirect("/tracker/")
    

def strava_callback(request):
    auth_code = request.GET.get('code')

    if auth_code:
        response = requests.post(
            settings.AUTH_URL,
            data={
                'client_id': settings.STRAVA_CLIENT_ID,
                'client_secret': settings.STRAVA_CLIENT_SECRET,
                'code': auth_code,
                'grant_type': 'authorization_code'
            }
        )

        if response.status_code == 200:
            data = response.json()
            athlete_data = data.get("athlete")
            if athlete_data is None:
                return redirect('home')

            user_id = athlete_data.get("id")
            existing_athlete = User.objects.filter(strava_id=user_id).first()

            if existing_athlete:
                existing_athlete.refresh_token = data.get("refresh_token")
                existing_athlete.access_token = data.get("access_token")
                existing_athlete.expires_at = data.get("expires_at")
                existing_athlete.save()
            else:
                # New User
                u = User.objects.create(
                    webuser=request.user,
                    strava_id=user_id,
                    firstName=athlete_data.get("firstname"),
                    lastName=athlete_data.get("lastname"),
                    accessToken=data.get("access_token"),
                    refreshToken=data.get("refresh_token"),
                    expiresAt=data.get("expires_at"),
                    code="abc"
                )
                milestones = Milestone.objects.all()
                for m in milestones:
                    UserMilestone.objects.create(
                        user=u,
                        milestone=m
                    )
            return redirect("/tracker/")
        return redirect("/tracker/")
    return redirect("/tracker/")

def account(request):
    if request.user.is_authenticated:
        user = request.user
        athlete = User.objects.filter(webuser=user).first()

        context = {
            "logged_in": request.user.is_authenticated,
            "user": user,
            "strava_linked": athlete != None,
            "athlete": athlete
        }
        return render(request, "tracker/account.html", context)
    else:
        return redirect("/tracker/")

def leaderboard_page(request):
    rankings = []
    for user in User.objects.all():
        # Get distance data
        total = get_stats(user.id).total_distance
        rankings.append((user, round(total)))

    rankings = sorted(rankings, key=lambda x: x[1], reverse=True)

    context = {
        "logged_in": request.user.is_authenticated,
        "unit": "km",
        "users": rankings
    }
    return render(request, "tracker/leaderboard.html", context)

def stats(request):
    # userID = int(request.GET.get("name"))
    nb_element = 100
    xdata = range(nb_element)
    ydata = [1, 2, 3, 4, 5, 6, 7, 8]
    ydata2 = [1, 3, 2, 5, 4, 7, 6, 9, 8]

    tooltip_date = "%d %b %Y %H:%M:%S %p"
    extra_serie = {"tooltip": {"y_start": "", "y_end": " cal"},
                   "date_format": tooltip_date}
    chartdata = {'x': xdata,
                 'name1': 'Tom', 'y1': ydata, 'extra1': extra_serie,
                 'name2': 'Ben', 'y2': ydata2, 'extra2': extra_serie}
    charttype = "lineChart"
    context = {
        "logged_in": request.user.is_authenticated,
        'charttype': charttype,
        'chartdata': chartdata
    }
    return render(request, "tracker/stats.html", context)

def about(request):
    return render(request, "tracker/about.html")