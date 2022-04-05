#!/usr/bin/env python3
import os
import discord
from dotenv import load_dotenv
import requests
import pandas as pd
from discord.ext import commands
from wb_leaderboard import get_leaderboard
from fuzzywuzzy import process

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
leaderboard = get_leaderboard('15208')

teams={
  'Fatstraps': ['Orangestuff','NightwingFPV','SHEESHfpv','Crusher72','WinsonFPV'],
  'Tinywhoop': ['Leviticus 113','j4y','Axxion','GetSum','iridium239'],
  'WeBleed': ['QF1 QTFPV','Nitr0 FPV','Huff-19','Baconninja87','Farmers'],
  'Sendit': ['EzR4cer','Tasty','stewydB','XaeroFPV','Lounds'],
  'Prop_Fathers': ['AyyyKayy','Slappy','BellaCiao','Sharks','DirtyMcStinky'],
  'IGOW_Whoopouts': ['gMan','TMAD','Chewie','Trashbiss','LankyFPV'],
  'REDiRacers': ['Potayto','ZOETEK','Mayan_Hawk','JHow.FPV','da_bits'],
  'LOS_Amigos': ['BrighFive','SchwiftyFPV','MrE','TRIM','Kbar'],
  'Mandel-brats': ['TiltedFPV','ItsBlunty','Radioactiv3','PRESSURE','RibbitFPV'],
  'Orqs': ['eedok','Tux-Rich','Tyrantt','_Solenya_','double_action_FPV'],
  'Bees_Knees': ['OGDrLove','ZDZ','Claud','Onoteis','SGT FELIX'],
  'Beta_Bros': ['NeonFPV','VIPERX','BRDSRTRL','Syrus','ZeroVoltzFPV'],
  'AngelMode': ['Smeland_FPV','Jaysus','_ZAR_','FreedomFPV','Pinhead21'],
  'Hawks': ['J0se', 'FPVSkittles', 'Rekt_Less', 'Bonebear', 'Gruver']
}


def code_block(string):
  output = "```\n{}\n```".format(string)
  return output

def match_name(name,namelist):
  match = process.extractOne(name,namelist)
  return match


def get_standings(command):
  tiers = {
    'Captains': [],
    '1': [],
    '2': [],
    '3': [],
    '4': []
  }
  standings = {}
  team_standings = pd.DataFrame()
  final_tiers = {}

  export = get_leaderboard('15208')
  #Fuzzy match pilot names to leaderboard names
  lb_indices = export.index.to_list()
  for team in teams:
    for i in range(len(teams[team])):
      t = match_name(teams[team][i],lb_indices)
      if t[1] > 80:
        teams[team][i] = t[0]
  for team in teams:
    for member in teams[team]:
      member = match_name(member,teams[team])
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
    final_tiers[tier] = tiersdf

  for team in teams:
    current_team = {team: standings[team].loc['Total', 'Lap Time']}
    current_team = pd.Series(data=current_team)
    team_standings = pd.concat([team_standings, current_team])
  team_standings.columns =['Total']
  team_standings = team_standings.sort_values('Total')
  team_standings['diff'] = team_standings.diff().fillna(0)

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
bot = commands.Bot(command_prefix='!')

#tiers
@bot.command(name='tiers', help='Shows current tiers')
async def get_tiers(ctx):
  output = ""
  #output = "```\n"
  tiers_df = get_standings('tiersdf')
  for tier in tiers_df:
    output = output+"!tier "+tier+"\n"
    #output = output+"{}:\n{}\n\n".format(tier,tiers_df[tier].to_string())
  #output = output+"\n```"
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
bot.run(TOKEN)
