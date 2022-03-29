#!/usr/bin/env python3
import os
import discord
from dotenv import load_dotenv
import requests
import pandas as pd
from discord.ext import commands
from wb_leaderboard import get_leaderboard

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
leaderboard = get_leaderboard('15208')

teams={
  'Fatstraps': ['Orangestuff','NightwingFPV','SHEESHfpv','Crusher72','WinsonFPV'],
  'Tinywhoop': ['Leviticus 113','j4y','Axxion','GetSum','iridium239'],
  'WeBleed': ['QF1 QTFPV','Nitr0 FPV','Huff-19','Baconninja87','Farmers'],
  'Sendit': ['EzR4cer','Tasty','stewydB','XaeroFPV','Lounds'],
  #'Prop Fathers': ['AyyyKayy','Slappy','BellaCiao','Sharks','DirtyMcStinky']
  'IGOW Whoopouts': ['gMan','TMAD','Chewie','Trashbiss','LankyFPV'],
  # 'REDiRacers': ['Potayto','ZOETEK','Mayan_Hawk','JHow.FPV','da_bits'],
  # 'LOS Amigos': ['BrighFive','SchwiftyFPV','MrE','TRIM','Kbar'],
  # 'Mandel-brats': ['TiltedFPV','ItsBlunty','Radioactiv3','PRESSURE','RibbitFPV'],
  # 'Orqs': ['eedok','Tux-Rich','Tyrant','Solenya','double_action_FPV'],
  # 'Bees Knees': ['OGDrLove','ZDZ','Claud','Onoteis','SGT FELIX'],
  'Beta Bros': ['NeonFPV','VIPERX','BRDSRTRL','Syrus','ZeroVoltzFPV']
  # 'AngelMode': ['Smeland_FPV','Jaysus','_ZAR_','FreedomFPV','Pinhead21']
}


def code_block(string):
  output = "```\n{}\n```".format(string)
  return output

def get_standings(command):
  tiers = {
    'Captains': [],
    'Tier 1': [],
    'Tier 2': [],
    'Tier 3': [],
    'Tier 4': []
  }
  standings = {}
  team_standings = pd.DataFrame()
  final_tiers = {}

  export = get_leaderboard('15208')

  for team in teams:
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
  output = "```\n"
  tiers_df = get_standings('tiersdf')
  for tier in tiers_df:
    output = output+"{}:\n{}\n\n".format(tier,tiers_df[tier].to_string())
  output = output+"\n```"
  await ctx.send(content=output)

#teams
@bot.command(name='standings', aliases=['teamtotals'],help='Shows team totals')
async def get_team_totals(ctx):
  teams_df = get_standings('teamsdf')
  output = "```\n{}\n```".format(teams_df.to_string())
  await ctx.send(output)

@bot.command(name='teams', help='Shows each team')
async def get_teams(ctx):
  output = ""
  teams_df = get_standings('standings')
  for team in teams:
    output = output+"{}:\n{}\n\n".format(team,teams_df[team].to_string())
  output = code_block(output)
  await ctx.send(output)
bot.run(TOKEN)