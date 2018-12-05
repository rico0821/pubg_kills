# -*- coding: utf-8 -*-
"""
    pubgi.API.helper
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Module for PUBG API wrapper.
      
    :copyright: (c) 2018 by rico0821.
    
"""
import json, requests, time

from datetime import datetime

from pubg_python import Shard


def make_url(region, query_type, query_filter=None, query=None):
    """
    Make API request URL.
    
    ARGS: region, query_type, (query_filter), (query)
    
    """
    
    url = 'https://api.pubg.com/shards/' + region + '/' + query_type
    
    if query_filter:
        url = url + '?filter[' + query_filter + ']=' + query

    elif query:
        url = url + '/' + query

    return url

def getRequest(region, query_type, query_filter, query):
    """
    Use URL to send request to API.
    
    ARGS: region, query_type, query_filter, query
    
    """
    url = make_url(region, query_type, query_filter, query)
   
    headers = {
      "Authorization" : api_key,
      "Accept" : "application/vnd.api+json",
      "Accept-Encoding " : "gzip"
    }
    try:
        print('Sent API request to %s' % url)
        start_time = time.time()
        result = requests.get(url, headers=headers)
        print('Received API request %r: took %f sec' % (result, time.time()-start_time))
        result = result.json()
        
    except Exception as e:
        
        result = None
    
    return result
    
def getPlayerData(region, player):
    """
    Get player data from API.
    
    ARGS: region, player

    """
    
    query_type = 'players'
    query_filter = 'playerNames'
    
    result = getRequest(region, query_type, query_filter, player)
    
    return result

def processPlayerId(data):
    """
    Find player ID from player data.
    
    ARGS: data
    
    """
    
    try:
        player_id = data['data'][0]['id']

    except Exception as e:
        print(str(e))
        player_id = None
    
    return player_id

def processMatchIds(data):
    """
    Find match IDs from player data.
    
    ARGS: data
    
    """
    try: 
        matches = data['data'][0]['relationships']['matches']['data']
        for match in reversed(matches):
            yield match['id']
        else:
            return None

    except Exception as e:
        raise e
    
def getMatch(region, match_id):
    """
    Get match data from API.
    
    ARGS: region, match_id
    
    """
    
    query_type = 'matches'
    query_filter = None
    
    result = getRequest(region, query_type, query_filter, match_id)
    
    return result

def processParticipantData(match_data, player_id):
    """
    Find player's stats from match data.
    
    ARGS: match_data, player_id
    
    """
    
    try:
        participant_data = next(data['attributes']['stats']
                            for data in match_data['included']
                            if data['type']=='participant' and
                            data['attributes']['stats']['playerId'] == player_id)

    except Exception as e:
        raise e
        
    return participant_data

def processMatchData(match_data):
    """
    Find match info from match data.
    
    ARGS: match_data
    
    """
    
    try:
        match_info = match_data['data']['attributes']
        
    except Exception as e:
        raise e
    
    return match_info

def processRosterData(match_data, player_id):
    """
    Find roster data from match data.
    
    ARGS: match_data, player_id
    
    """
    
    try:
        participant_id = next(data['id'] for data in match_data['included'] 
                             if data['type']=='participant' and 
                             data['attributes']['stats']['playerId']==player_id)
        
        for data in match_data['included']:
            if data['type'] == 'roster':    
                for participant in data['relationships']['participants']['data']:
                    if participant['id'] == participant_id:
                        return data['id']

    except Exception as e:
        raise e

def processTelemetryURL(match_data):
    """
    Find telemetry URL from match data.
    
    ARGS: match_data
    
    """
    
    try: 
        url = next(data['attributes']['URL'] for data in match_data['included']
                      if data['type']=='asset')
        
    except Exception as e:
        raise e
        
    return url

def processWinnerIds(match_data):
    """
    Find winner ID from match data.

    ARGS: match_data

    """

    try:
        win_roster = next(roster['relationships']['participants']['data']
                                        for roster in match_data['included']
                                              if roster['type']=='roster'
                                    and roster['attributes']['won']=='true')

        winner_ids = [winner['id'] for winner in win_roster]

        return winner_ids

    except StopIteration:
        return []

def processWinParticipantData(match_data, participant_id):
    """
    Find participant's stats from match data using participant id.
    
    ARGS: match_data, participant_id
    
    """
    
    try:
        participant_data = next(data['attributes']['stats']
                            for data in match_data['included']
                            if data['id'] == participant_id)

    except Exception as e:
        raise e
        
    return participant_data

def getPlayerId(region, player):
    """
    Get a player's game id.
    
    ARGS: region, player
    
    """
    
    player_data = getPlayerData(region, player)
    player_id = processPlayerId(player_data)
    
    return player_id

def getPlayerStats(region, player, last_match_id):
    """
    Get a tuple containing player id, match id, match stats.
    
    ARGS: region, player, last_match_id
    
    """
    
    player_id = getPlayerId(region, player)
    player_data = getPlayerData(region, player)
    match_ids = list(processMatchIds(player_data))
    
    try:
        if last_match_id:
            try:
                upto = match_ids.index(last_match_id) + 1
            except:
                upto = 0
                print('Something went wrong with finding match index.')
        else: 
            upto = 0
            print('No recent matches were recorded for player %r [region: %r]' % (player, region))
            
        for match_id in match_ids[upto:]:
            match_data = getMatch(region, match_id)
            match_info = processMatchData(match_data)
            match_stats = processParticipantData(match_data, player_id)
            roster_data = processRosterData(match_data, player_id)
            telemetry_url = processTelemetryURL(match_data)
            yield (match_id, match_stats, match_info, roster_data, telemetry_url)
            
    except Exception as e:
        raise e
        print('Error finding matches found for player %r [region: %r]' % (player, region))
        return False
    
def getTelemetry(url):
    """
    Get telemetry data using asset URL.
    
    ARGS: url
    
    """
    
    headers = {
      "Accept" : "application/vnd.api+json",
      "Accept-Encoding" : "identity"
    }
    result = None

    try:
        print('Sent API request to %s' % url)
        start_time = time.time()
        result = requests.get(url, headers=headers)
        print('Received API request %r: took %f sec' % (result, time.time()-start_time))
        if result:
            result = result.json()
        
    except Exception as e:
        result = None
    
    return result

def filterTelemetry(telemetry, filters):
    try:
        filter_telemetry = [data for data in telemetry
                for filter in filters if data['_T'] == filter]

    except Exception as e:
        raise e

    return filter_telemetry


def getSampleTelemetry(region):
    """
    Get sample telemetry urls.

    ARGS: region

    """
    try:
        samples = getRequest(region, 'samples', None, None)
        matches = samples['data']['relationships']['matches']['data']
        match_ids = [match['id'] for match in matches]

        match_dataset = [getMatch(region, match_id) 
                                  for match_id in match_ids]

        url_list = [processTelemetryURL(match_data) for match_data in match_dataset]

        return url_list

    except Exception as e:
        raise e

def getWinnerData(region):
    """
    Get winner average data.

    ARGS: region

    """
    try:
        samples = getRequest(region, 'samples', None, None)
        matches = samples['data']['relationships']['matches']['data']
        match_ids = [match['id'] for match in matches]
        
        match_dataset = [getMatch(region, match_id) 
                                  for match_id in match_ids[:5]] #CHANGE!

        winner_data = [{**processWinParticipantData(match_data, winner_id),
                                        **processMatchData(match_data)}
                                            for match_data in match_dataset
                            for winner_id in processWinnerIds(match_data)
                                                             if winner_id]
        return winner_data

    except Exception as e:
        raise e

api_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIwYTc4ZDc4MC0yMjc3LTAxMzYtNzE5NS0wMGNmZGM1OWM4ZDYiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNTIzNzU0MzQxLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6InRlc3QtYWU4ZmU0MmMtMTNhYy00ODA1LWJjMTAtZTI1ZTI5NzYyYjQ3In0.mSBvC0byDeq8bxgtRYL-C7NYvDJv7jGIpPdKo_KprHg'
shardDict = {
    'pc-kakao' : Shard.PC_KAKAO,
    'pc-krjp' : Shard.PC_KRJP,
    'pc-eu' : Shard.PC_EU,
    'pc-na' : Shard.PC_NA,
    'pc-as' : Shard.PC_AS,
    'pc-oc' : Shard.PC_OC,
    'pc-sea' : Shard.PC_SEA,
    'pc-sa' : Shard.PC_SA,
    'pc-ru' : Shard.PC_RU,
    'pc-jp' : Shard.PC_JP
}