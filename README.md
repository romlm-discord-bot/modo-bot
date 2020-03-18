# modo-bot

## HOW TO USE
1. create a discord bot user at discord.gg
2. connect your bot to the required server
3. add your bot token as an environement variable called DISCORD_BOT_TOKEN
4. specify your server/guild name in GUID_NAME
5. on your discord server create roles Asking, Talking and one or more allowed roles and put them in env/environment.py
6. specify one or more text channels where the commands can be executed in ALLOWED_CHANNELS
7. specify voice channels where the bot will mute/unmute sudents in SECURED_VOCAL_SERVER_NAMES

## COMMANDS
### the bot prefix is specified in env/environment.py BOT_PREFIX (default is "!")

- help:
  - help: shows all the available commands for the bot
  - help \<command_name\>: shows the help for the specified command
- ask:
  - ask: gives the student the asking student role
  - ask \<reason\>: same as ask but stores the reason
  - nb: there cannot be more than one ask request by person
- cancel: cancels the ask request
- allow:
  - allow \<username\>: only works on students with Asking role and if no student is talking, unmute the student, gives the Talking role and unmute student
  - allow \<username\> \[command: add/replace\]: if a student is already talking.
  - allow \<username\> add: to unmute a member alongwith the other talking students
  - allow \<username\> replace: to mute all talking students and unmute the username student
 
- disallow:
  - disallow \<username\>: only works on Talking students, mute the student and removes his Talking role
