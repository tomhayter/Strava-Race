from django.shortcuts import render
from django.conf import settings
from .models import Activity, BestEffort, Milestone, Trophy, User, UserMilestone
from stravalib.client import Client
from stravalib import unithelper
import pickle
import time as t
from datetime import datetime, timedelta, date
import yaml

# Get config
config = yaml.safe_load(open(f"{settings.BASE_DIR}\\..\\Deployment\\config.yml"))

RACE_START = datetime(2023, 8, 24)

class Statistics:
    def __init__(self, client, activities):
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
        # self.best_marathon = timedelta()

        self.num_activities = 0
        self.longest_run = 0
        self.longest_cycle = 0
        self.longest_hike = 0
        self.largest_climb = 0
        self.highest_point = 0

        for activity in activities:
            dt = datetime(activity.start_date.year,
                        activity.start_date.month,
                        activity.start_date.day)
            if dt < RACE_START:
                continue
            self.total_distance += unithelper.kilometer(activity.distance).num
            self.total_elevation += unithelper.meter(activity.total_elevation_gain).num
            self.largest_climb = max(self.largest_climb, unithelper.meter(activity.total_elevation_gain).num)
            self.total_time += activity.moving_time
            self.num_activities += 1
            self.highest_point = max(self.highest_point, activity.elev_high)
            self.countries.add(activity.location_country)
            if activity.type == "Run":
                self.longest_run = max(self.longest_run, unithelper.kilometer(activity.distance).num)
                self.run_distance += unithelper.kilometer(activity.distance).num
                activity_with_be = client.get_activity(activity.id, True)
                if activity_with_be.best_efforts:
                    for effort in activity_with_be.best_efforts:
                        if effort.name == "5k":
                            self.best_5k = min(self.best_5k, effort.elapsed_time)
                        elif effort.name == "10k":
                            self.best_10k = min(self.best_10k, effort.elapsed_time)
                        elif effort.name == "Half-Marathon":
                            self.best_half = min(self.best_half, effort.elapsed_time)
            elif activity.type == "Ride":
                self.longest_cycle = max(self.longest_cycle, unithelper.kilometer(activity.distance).num)
                self.cycle_distance += unithelper.kilometer(activity.distance).num
            elif activity.type == "Hike" or activity.type == "Walk":
                self.longest_hike = max(self.longest_hike, unithelper.kilometer(activity.distance).num)
                self.hike_distance += unithelper.kilometer(activity.distance).num
                

class LocalUser:
    def __init__(self, user):
        self.client = get_client_for_user(User.objects.get(id=user).firstName.lower())
        self.activities = list(self.client.get_activities(limit=100, after="2023-08-24T00:00:00Z"))
        self.activities = sorted(self.activities, key=lambda x: x.start_date)
        self.stats = Statistics(self.client, self.activities)


class Cache:
    def __init__(self):
        # TODO: Update cache regularly using last updated time
        self.updated = datetime.now()
        self.users = {}

    def add_user(self, user):
        self.users[user] = LocalUser(user)

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

        if most_countries[1] < len(stats.countries):
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
                    instance.dateAchieved = date(activity.start_date.year,
                                                activity.start_date.month,
                                                activity.start_date.day)
                    instance.save()
                    break

def get_client_for_user(user):
    # Get the client for a user.
    CLIENT_ID = config[user]["client_id"]
    CLIENT_SECRET = config[user]["client_secret"]

    # Strava authentication
    client = Client()

    with open(f'{settings.BASE_DIR}\\..\\Deployment\\access_tokens\\{user}_access_token.pickle', 'rb') as f:
        access_token = pickle.load(f)

    if t.time() > access_token['expires_at']:
        print('Token has expired, will refresh')
        refresh_response = client.refresh_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    refresh_token=access_token["refresh_token"])
        access_token = refresh_response
        with open(f'{settings.BASE_DIR}\\..\\Deployment\\access_tokens\\{user}_access_token.pickle', 'wb') as f:
            pickle.dump(refresh_response, f)
        print('Refreshed token saved to file')
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']

    else:
        print('Token still valid, expires at {}'
            .format(t.strftime("%a, %d %b %Y %H:%M:%S %Z", t.localtime(access_token['expires_at']))))
        client.access_token = access_token['access_token']
        client.refresh_token = access_token['refresh_token']
        client.token_expires_at = access_token['expires_at']

    return client

def get_stats(user):
    if user not in CACHE.users:
        CACHE.add_user(user)
    return CACHE.users[user].stats

def get_activities(user):
    if user not in CACHE.users:
        CACHE.add_user(user)
    return CACHE.users[user].activities

def get_athlete(userID):
    return User.objects.get(id=userID)

def home(request):
    rankings = []

    cumulative = 0
    for user in User.objects.all():
        # Get distance data
        total = get_stats(user.id).total_distance
        rankings.append((user, total))
        cumulative += total

    rankings = sorted(rankings, key=lambda x: x[1])

    # TODO: Cron these
    update_milestones()
    update_altitude_milestones()
    update_trophy_winners()

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