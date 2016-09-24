import json
import requests
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import generic
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import geograpy
from geotext import GeoText
import urllib2, urllib
# import urllib.request #3.5.1
# import urllib.parse   #3.5.1

verification_token = 'create this custom token for webhook verification'
page_access_token = ' get this token from FB Developer Site'

states_short = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

states_dict = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}
class weatherData:
    def __init__ (self, temp, condition, city, state):
        self.temp = temp
        self.condition = condition
        self.city = city
        self.state = state

class weatherBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET.get('hub.verify_token', False) == verification_token:
            return HttpResponse(self.request.GET['hub.challenge'])
        else :
            return HttpResponse('Error, invalid token')
# Create your views here.
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)


    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        incoming_message = json.loads(self.request.body.decode('utf-8'))
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events
                if 'message' in message:
                    # Print the message to the terminal
                    # print(message)
                    messageReceived(message)
        return HttpResponse()


def post_facebook_message(fbid, received_message):
    print("In postMessage function")
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=' + page_access_token
    response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":received_message}})
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
    print(status.json())


def prepare_response(weather, message):
    print("In prepare_resp function")
    print(message)
    id = message['sender']['id']
    response = "It's " + weather.temp + " degrees F and " + weather.condition + " in " + weather.city + ", " + weather.state
    post_facebook_message(id, response)


def extract_location(user_text):
    print("In extractLocation function")
    geoTextResult = (GeoText(user_text)).cities
    geograpyResult = (geograpy.get_place_context(text=user_text)).places
    print("geoTextResult - " + str(geoTextResult))
    print("geograpyResult - " + str(geograpyResult))
    city1 = geoTextResult[0] if geoTextResult else None
    city2 = geograpyResult[0] if geograpyResult else None
    state = getStateIfAvailable(user_text)

    if(city1 or city2):
        location = city1 if city1 else city2
        if(state):
            location += ', ' + state
            return location
    else:
        return None


def getStateIfAvailable(user_text):
    print("In getStateIfAvailable function")
    for short_state in states_dict:
        long_state = states_dict[short_state]
        if (short_state in user_text):
            return short_state
        elif (long_state in user_text):
            return short_state
    return None


def getWeatherData(location):
    print("In getWeatherData function")
    location = '"' + location + '"'
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = 'select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=' + location + ')'
    yql_url = baseurl + urllib.urlencode({'q':yql_query}) + "&format=json"
    result = urllib2.urlopen(yql_url).read().decode('utf8')
    data = json.loads(result)
    return data

def organizeWeatherData(data):
    print("In organizeWeatherData function")
    print (data['query']['results'])
    city = data['query']['results']['channel']['location']['city']
    state = data['query']['results']['channel']['location']['region']
    temp = data['query']['results']['channel']['item']['condition']['temp']
    condition = data['query']['results']['channel']['item']['condition']['text']
    weather_data = weatherData(temp, condition, city, state)
    return weather_data


def messageReceived(message):
    print("In messageReceived function")
    user_text = message['message']['text']
    print('User entered - ' + user_text)
    location = extract_location(user_text)
    if location:
        data = getWeatherData(location)
        weather_data = organizeWeatherData(data)
        prepare_response(weather_data, message)
    else:
        sendErrorResponse(message)


def sendErrorResponse(message):
    print("In sendErrorResponse function")
    print(message)
    id = message['sender']['id']
    response = "What's your location again?"
    post_facebook_message(id, response)