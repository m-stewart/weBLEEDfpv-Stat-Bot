#!/usr/bin/env python3
import os
import discord
from dotenv import load_dotenv
import requests
import pandas as pd
from discord.ext import commands
from fuzzywuzzy import process
from wb_leaderboard import get_leaderboard, get_track_id, update_track_id
import wb_google_sheet as wbsheet


#use dotenv to store discord token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#Set track id
try:
  track_id = dotenv_values(".env.trackid")['TRACK_ID']
except:
  track_id = '18755'

#leaderboard = get_leaderboard(track_id)

teams={
  'Sim Simps': ['NeonFPV','Goatro','Kent FPV','GreasySlimebag','ironicallytasty.tv','ZOETEK','Derpy Hooves','Hendosaurr'],
  'Tiny Warp Speeds': ['TDog_','DayLight FPV','J4y','Lounds','Radioactiv3','carlosecaceres2093','Greenhorn_FPV','jrice'],
  'eMax': ['Orangestuff','TiltedFPV','GetSum','ProDangles','TMAD','AZ Cruz', 'TRASHBISS', 'Solenya'],
  'FlyVibes': ['eedok','Phobos','Huff-19','John E Fly','stewydB','Crusher72','ToxicFPV','blam'],
  'Whooping Wizards': ['Leviticus 113', 'SHEESHfpv', 'Solace', 'Vanadium','Axxion','flightning', 'Bondo_FPV', 'Kbar'],
  '1s Finesse': ['MrChaus','QF1 QTFPV','WILDTYPE', 'Chet Mac', 'XaeroFPV', 'Dinglez', 'RushFPV', 'Farmers'],
  'Quality Control': ['AyyyKayyy', 'ZDZ', 'MrE.', 'FPV_Cam', 'NightwingFPV', 'FPVSkittles', 'BellaCiao', 'iridium239']
}


def code_block(string):
  output = "```\n{}\n```".format(string)
  return output

def match_name(name,namelist):
  match = process.extractOne(name,namelist)
  return match

def authUser(user):
  admin_users = ['StewydB#9027']
  if str(user) in admin_users:
    return True
  else:
    return False

def restart_bot():
  cmd = 'systemctl restart discobot'
  try: 
    os.popen(cmd)
    result = 'Bot Restarted'
  except:
    result = 'Problem restarting bot'


def get_standings(command):
  tiers = {
    '1': [],
    '2': [],
    '3': [],
    '4': [],
    '5': [],
    '6': [],
    '7': [],
    '8': []
  }
  standings = {}
  team_standings = pd.DataFrame()
  final_tiers = {}

  export = get_leaderboard(track_id)
  if command == 'lb':
    return export
  #Fuzzy match pilot names to leaderboard names
  lb_indices = export.index.to_list()
  #remove spaces from pilot names for fuzzy matching
  lb_indices_no_spaces = []
  for pilot in range(len(lb_indices)):
    lb_indices_no_spaces.append(lb_indices[pilot].replace(" ",""))
  
  for team in teams:
    for i in range(len(teams[team])):
      t = match_name(teams[team][i],lb_indices_no_spaces)
      if t[1] > 80:
        teams[team][i] = lb_indices[lb_indices_no_spaces.index(t[0])]
  for team in teams:
    #for member in teams[team]:
      #member = match_name(member,teams[team])
    standings[team] = export.iloc[export.index.isin(teams[team])].copy()
    for member in teams[team]:
      try:
        standings[team].loc[member]
      except KeyError:
        standings[team].loc[member] = 1000
    standings[team].loc['Total'] = standings[team].sum(numeric_only=True)

    #Add to tiers:
    i = 0
    for tier in tiers:
      tiers[tier].append(standings[team].iloc[i])
      i += 1

  for tier in tiers:
    tiersdf = pd.DataFrame(tiers[tier]).sort_values('Lap Time')
    tiersdf['Diff'] = tiersdf.diff().fillna(0)
    tiersdf['From 1st'] = tiersdf['Lap Time'] - tiersdf['Lap Time'].iloc[0]
    final_tiers[tier] = tiersdf

  for team in teams:
    current_team = {team: standings[team].loc['Total', 'Lap Time']}
    current_team = pd.Series(data=current_team)
    team_standings = pd.concat([team_standings, current_team])
  team_standings.columns =['Total']
  team_standings = team_standings.sort_values('Total')
  team_standings['Diff'] = team_standings.diff().fillna(0)
  team_standings['From 1st'] = team_standings['Total'] - team_standings['Total'].iloc[0]

  #Overall Team Standings:  team_standings
  #Tiers: final_tiers[tier]
  #Standings: standings[team]
  
  if command == 'tiersdf':
    return final_tiers
  if command == 'teamsdf':
    return team_standings
  if command == 'standings':
    return standings


#Bot Stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!',intents = intents)

@bot.command(name='season', aliases=['overall'], help='Shows overall season standings')
async def get_season(ctx):
  output = ""
  output = wbsheet.get_season_standings()
  output = code_block(output)
  await ctx.send(content=output)

#tiers
@bot.command(name='tiers', help='Shows current tiers')
async def get_tiers(ctx):
  output = ""
  tiers_df = get_standings('tiersdf')
  for tier in tiers_df:
    output = output+"!tier "+tier+"\n"
  output = code_block(output)
  await ctx.send(content=output)

@bot.command(name='tier', help="Shows the tier specified. ex: !tier 1")
async def get_tier(ctx, tier: str):
  tiers_df = get_standings('tiersdf')
  try:
    output = tiers_df[tier]
  except KeyError:
    output = "{} not found.  Type !tiers to see a list of available commands".format(tier)
  output = code_block(output)
  await ctx.send(output)

#Overall Standings
@bot.command(name='standings', aliases=['teamtotals'],help='Shows team totals')
async def get_team_totals(ctx):
  teams_df = get_standings('teamsdf')
  output = "```\n{}\n```".format(teams_df.to_string())
  await ctx.send(output)

#teams
#team <teamname>
@bot.command(name='team', help="Shows the team's current times")
async def get_team(ctx, teamname):
  teams_df = get_standings('standings')
  teamname = match_name(teamname, teams.keys())[0]
  try:
    output = teams_df[teamname].to_string()
  except KeyError:
    output = "{} not found.  Type !teams to see a list of possible team names".format(teamname)
  output = code_block(output)
  await ctx.send(output)
@bot.command(name='teams', help='Shows each team')
async def get_teams(ctx):
  output = ""
  for team in teams:
    output = output+team+"\n"
  output = code_block(output)
  await ctx.send(output)

#leaderboard - returns top 15 from leaderboard
#leaderboard, lb
@bot.command(name='leaderboard',aliases=['lb'],help='Shows first page of leaderboard')
async def get_lb(ctx):
  await ctx.send(code_block(get_standings('lb').head(25)))

#Update - updates the track ID
@bot.command(name='newtrack',help='Updates the track ID.  Requires admin')
@commands.has_any_role('Sim Race Managers','Stat Bot Managers')
async def newtrack(ctx):
  #if authUser(ctx.message.author):
  track = get_track_id('webleed')
  if track['id'] is not None:
    await ctx.send(update_track_id(track))
    await ctx.send(restart_bot())
  else:
    await ctx.send("Problem getting new track info")
  #else:
    #await ctx.send("Not Authorized")

@bot.event
async def on_command_error(ctx,error):
  if isinstance(error, commands.errors.CheckFailure):
    await ctx.send("You do not have the correct role for this command")

bot.run(TOKEN)
