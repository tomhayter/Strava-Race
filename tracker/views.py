from django.shortcuts import render
from .models import Activity, BestEffort, Milestone, Trophy, User, UserMilestone
from stravalib.client import Client
from stravalib import unithelper
import time as t
from datetime import timedelta, date


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
                break
            running_total = 0
            for activity in activities:
                running_total += unithelper.meter(activity.total_elevation_gain).num
                if running_total > milestone_distance:
                    instance = UserMilestone.objects.get(user=user, milestone=milestone)
                    instance.dateAchieved = date(activity.start_date.year,
                                                activity.start_date.month,
                                                activity.start_date.day)
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
                break
            running_total = 0
            for activity in activities:
                running_total += unithelper.kilometer(activity.distance).num
                if running_total > milestone_distance:
                    instance = UserMilestone.objects.get(user=user, milestone=milestone)
                    instance.dateAchieved = date(activity.startDate.year,
                                                activity.startDate.month,
                                                activity.startDate.day)
                    instance.save()
                    break

def get_new_activities():
    for u in User.objects.all():
        client = get_client_for_user(u.id)
        activities = list(client.get_activities(limit=100, after=f"2023-08-24T00:00:00Z"))
        activities = sorted(activities, key=lambda x: x.start_date)

        stored_activities = Activity.objects.filter(user__id=u.id)
        stored_ids = [a.stravaID for a in stored_activities]
        for a in activities:
            if a.id in stored_ids:
                continue
            adb = Activity.objects.create(
                user=u,
                name=a.name,
                distance=unithelper.kilometer(a.distance).num,
                totalElevation=unithelper.meter(a.total_elevation_gain).num,
                highestPoint=a.elev_high,
                type=a.type,
                duration=a.moving_time,
                country=a.location_country or "United Kingdom",
                startDate=date(a.startDate.year,
                               a.startDate.month,
                               a.startDate.day),
                stravaID=a.id)
            if a.type == "Run":
                abe = client.get_activity(a.id, True)
                if abe.best_efforts:
                    for be in abe.best_efforts:
                        if be.name not in TRACKED_BEST_EFFORTS:
                            continue
                        BestEffort.objects.create(
                            activity=adb,
                            name=be.name,
                            time=be.elapsed_time
                        )

def get_client_for_user(userID):
    # Get the client for a user.
    user = User.objects.get(id=userID)

    # Strava authentication
    client = Client()

    if t.time() > user.expiresAt:
        print('Token has expired, will refresh')
        refresh_response = client.refresh_access_token(client_id=user.clientID, client_secret=user.clientSecret,
                                                    refresh_token=user.refreshToken)
        print('Refreshed token saved to file')
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']
        user.accessToken = refresh_response['access_token']
        user.refreshToken = refresh_response['refresh_token']
        user.expiresAt = refresh_response['expires_at']
    else:
        print('Token still valid, expires at {}'
            .format(t.strftime("%a, %d %b %Y %H:%M:%S %Z", t.localtime(user.expiresAt))))
        client.access_token = user.accessToken
        client.refresh_token = user.refreshToken
        client.token_expires_at = user.expiresAt

    user.save()
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
        rankings.append((user, total))
        cumulative += total
    rankings = sorted(rankings, key=lambda x: x[1])

    context = {
        "first": rankings[-1][0],
        "second" : rankings[-2][0],
        "third" : rankings[-3][0],
        "first_distance" : round(rankings[-1][1]),
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

    progress = 100 * (total - closest_below.distance)/(closest_above.distance - closest_below.distance)

    context = {
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
        "milestones": milestones,
        "arg_name": userID,
        "unit": "km"
    }
    return render(request, "tracker/milestones.html", context)

def trophies(request):
    trophies = get_trophies()
    context = {
        "trophies": trophies
    }
    return render(request, "tracker/trophies.html", context)

def altitude_milestones(request):
    userID = int(request.GET.get("name"))
    milestones = get_milestones_for_user(True, userID)
    context = {
        "milestones": milestones,
        "arg_name": userID,
        "unit": "m"
    }
    return render(request, "tracker/milestones.html", context)