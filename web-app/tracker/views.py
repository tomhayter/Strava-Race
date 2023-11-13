from django.shortcuts import render
from django.conf import settings
from stravalib.client import Client
from stravalib import unithelper
import pickle
import time
from datetime import datetime
import yaml
import openpyxl

# Get config
config = yaml.safe_load(open(f"{settings.BASE_DIR}\\..\\..\\Deployment\\config.yml"))

USERS = ["tom", "ben", "justin"]

RACE_START = datetime(2023, 8, 24)

class Milestone:
    def __init__(self, name, distance, date_achieved, link):
        self.name = name
        self.distance = distance
        if date_achieved is None:
            self.date_achieved = ""
        else:
            self.date_achieved = datetime.date(date_achieved)
        if link is None:
            self.link = ""
        else: 
            self.link = link

    def dictionary(self):
        return {"name": self.name,
                "distance": self.distance,
                "date_achieved": self.date_achieved,
                "link": self.link}


def get_milestones():
    # Get Milestones
    spreadsheet = openpyxl.load_workbook(f"{settings.BASE_DIR}\\..\\..\\Deployment\\Running Milestones.xlsx")
    spreadsheet1 = spreadsheet["Distance"]

    milestones = {}
    for row in range(2, spreadsheet1.max_row+1):
        milestones[spreadsheet1.cell(row, 1).value] = spreadsheet1.cell(row, 2).value
    return milestones

def get_detailed_milestones(user):
    # Get Milestones
    spreadsheet = openpyxl.load_workbook(f"{settings.BASE_DIR}\\..\\..\\Deployment\\Running Milestones.xlsx")
    spreadsheet1 = spreadsheet["Distance"]

    user_column = 3
    if user == "ben":
        user_column = 4
    if user == "justin":
        user_column = 5
        

    milestones = []
    for row in range(3, spreadsheet1.max_row+1):
        milestones.append(
            Milestone(
            spreadsheet1.cell(row, 1).value,
            spreadsheet1.cell(row, 2).value,
            spreadsheet1.cell(row, user_column).value,
            spreadsheet1.cell(row, 6).value))
    return milestones


def get_nearest_milestones(milestones, total_distance):
    # Get closest and completed milestones
    closest_below = (None, -1)
    closest_above = (None, 50000)
    completed = []

    for milestone, distance in milestones.items():
        if distance < total_distance:
            completed.append((milestone, distance))
            if distance > closest_below[1]:
                closest_below = (milestone, distance)
        elif distance > total_distance:
            if distance < closest_above[1]:
                closest_above = (milestone, distance)

    return closest_below, closest_above, completed


def get_total_distance(activities):
    total_distance = 0

    for activity in activities:
        dt = datetime(activity.start_date.year,
                      activity.start_date.month,
                      activity.start_date.day)
        if dt > RACE_START:
            total_distance += unithelper.kilometer(activity.distance).num

    return total_distance

def get_total_altitude(activities):
    total_altitude = 0
    for activity in activities:
        dt = datetime(activity.start_date.year,
                      activity.start_date.month,
                      activity.start_date.day)
        if dt > RACE_START:
            total_altitude += unithelper.meter(activity.total_elevation_gain).num
    return total_altitude

def get_distance_stats(activities):
    total_distance = 0
    run_distance = 0
    cycle_distance = 0
    hike_distance = 0

    for activity in activities:
        dt = datetime(activity.start_date.year,
                      activity.start_date.month,
                      activity.start_date.day)
        if dt > RACE_START:
            total_distance += unithelper.kilometer(activity.distance).num
            if activity.type == "Run":
                run_distance += unithelper.kilometer(activity.distance).num
            elif activity.type == "Ride":
                cycle_distance += unithelper.kilometer(activity.distance).num
            elif activity.type == "Hike" or activity.type == "Walk":
                hike_distance += unithelper.kilometer(activity.distance).num

    return total_distance, run_distance, cycle_distance, hike_distance

def get_client_for_user(user):
    CLIENT_ID = config[user]["client_id"]
    CLIENT_SECRET = config[user]["client_secret"]
    CODE = config[user]["code"]

    # Strava authentication
    client = Client()

    with open(f'{settings.BASE_DIR}\\..\\..\\Deployment\\{user}_access_token.pickle', 'rb') as f:
        access_token = pickle.load(f)

    if time.time() > access_token['expires_at']:
        print('Token has expired, will refresh')
        refresh_response = client.refresh_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                                    refresh_token=access_token["refresh_token"])
        access_token = refresh_response
        with open(f'{settings.BASE_DIR}\\..\\..\\Deployment\\{user}_access_token.pickle', 'wb') as f:
            pickle.dump(refresh_response, f)
        print('Refreshed token saved to file')
        client.access_token = refresh_response['access_token']
        client.refresh_token = refresh_response['refresh_token']
        client.token_expires_at = refresh_response['expires_at']

    else:
        print('Token still valid, expires at {}'
            .format(time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(access_token['expires_at']))))
        client.access_token = access_token['access_token']
        client.refresh_token = access_token['refresh_token']
        client.token_expires_at = access_token['expires_at']

    return client


def home(request):
    rankings = []

    for user in USERS:
        client = get_client_for_user(user)
    
        # Get distance data
        athlete = client.get_athlete()
        activities = client.get_activities(limit=100)
        total = get_total_distance(activities)
        rankings.append((athlete.firstname, total))

    print(rankings)
    rankings = sorted(rankings, key=lambda x: x[1])
    print(rankings)

    context = {
        "first": rankings[-1][0],
        "second" : rankings[-2][0],
        "third" : rankings[-3][0],
        "first_distance" : rankings[-1][1],
        "second_distance" : rankings[-2][1],
        "third_distance" : rankings[-3][1]
    }
    return render(request, "tracker/home.html", context)


def user(request):

    user = request.GET.get("name").lower()
    milestones = get_milestones()
    client = get_client_for_user(user)
        
    # Get distance data
    athlete = client.get_athlete()
    activities = client.get_activities(limit=100)
    total, run, cycle, hike = get_distance_stats(activities)
    altitude = get_total_altitude(activities)

    closest_below, closest_above, completed = get_nearest_milestones(milestones, total)

    progress = 100 * (total - closest_below[1])/(closest_above[1] - closest_below[1])

    context = {
        "name": athlete.firstname + " " + athlete.lastname,
        "total_distance" : round(total, 2),
        "run_distance" : round(run, 2),
        "cycle_distance" : round(cycle, 2),
        "hike_distance" : round(hike, 2),
        "altitude": round(altitude, 1),
        "last_milestone_name" : closest_below[0],
        "last_milestone_distance": closest_below[1],
        "next_milestone_name": closest_above[0],
        "next_milestone_distance": closest_above[1],
        "progress": round(progress),
        "arg_name": user
    }
    return render(request, "tracker/user.html", context)

def milestones(request):
    user = request.GET.get("name").lower()
    milestones = get_detailed_milestones(user)
    context = {
        "milestones": [i.dictionary() for i in milestones],
        "arg_name": user
    }
    return render(request, "tracker/milestones.html", context)
