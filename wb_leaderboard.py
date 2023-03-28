#!/usr/bin/env python3
#This is a module meant to be imported
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import quote, unquote
import base64
import requests
from requests import Request, Session
import json
import pandas as pd
from dotenv import dotenv_values

def velo_api(url,data):
  #Create Cipher
  key = 'BatCaveGGevaCtaB'.encode('utf-8')
  cipher = AES.new(key, AES.MODE_ECB)
  #Encrypt the utf encoded data string
  msg_en = cipher.encrypt(pad(data.encode('utf-8'),16))
  #base64 encode the encrypted string
  output = quote(base64.b64encode(msg_en),safe='')
  #add prefix to encrypted string
  payload = "post_data={}".format(str(output))
  #Standard Headers
  headers = {
  'User-Agent': 'UnityPlayer/2020.3.8f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)',
  'Accept': '*/*',
  'Accept-Encoding': 'identity',
  'Connection': 'Keep-Alive',
  'Content-Type': 'application/x-www-form-urlencoded',
  'X-Unity-Version': '2020.3.8f1'
  }
  try:
    #make api call
    s = Session()
    req = Request('POST', url, data=payload, headers=headers)
    prepped = req.prepare()
    response = s.send(prepped)
    #base64 decode and then decrypt the response
    decipher = AES.new(key, AES.MODE_ECB)
    result = decipher.decrypt(base64.b64decode(response.text))
    result = unpad(result, 16)
    #decode decrypted response
    result = result.decode('utf-8').strip()
    #convert to json object
    final = json.loads(result)
  except:
    print('Problem with api call')
    quit(1)
  return final

# @input: track_id
# @output: leaderboard results in pandas dataframe
def get_leaderboard(track_id):
  payload = "track_id={}&sim_version=1.16&offset=0&count=200&protected_track_value=2&race_mode=6".format(track_id)
  url = 'http://www.velocidrone.com/api/leaderboard/getLeaderBoard'
  final = velo_api(url,payload)
  if not final['tracktimes']:
    print('Invalid track_id')
    quit(1)
  final_df = pd.json_normalize(final, record_path =['tracktimes'])
  final_df = final_df[['playername', 'lap_time']]
  final_df['lap_time'] = pd.to_numeric(final_df['lap_time'])
  final_df = final_df.rename({'playername': 'Player Name', 'lap_time': 'Lap Time'}, axis='columns')
  return(final_df.set_index('Player Name'))

def get_track_id(trackname):
  payload = "scenery_id=&playername=&track_name={}&track_type=&order_by_date=True&order_by_rating=True&show_beginner=True&show_intermediate=True&show_advanced=True".format(trackname)
  url = 'http://www.velocidrone.com/api/v1/private/user/rated_tracks_list'
  tracklist = velo_api(url,payload)
  t = {}
  t['id'] = None
  t['name'] = None
  t['name'] = unquote(tracklist['user_tracks'][0]['track_name']).replace('+', ' ')
  t['id'] = tracklist['user_tracks'][0]['id']
  return t

def update_track_id(newtrack):
  trackfile = '.env.trackid'
  try:
    #oldtrack = dotenv_values(trackfile)
    with open(trackfile,'w+') as f:
      f.write('# .env\n')
      f.write('TRACK_ID="{}"'.format(newtrack['id'])+'\n')
      f.write('TRACK_NAME="{}"'.format(newtrack['name'])+'\n')
    result = "Track updated to '{}'.  New ID: '{}'".format(newtrack['name'],newtrack['id'])
  except:
    result = "Problem updating track info"
  return result
