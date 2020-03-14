from sys import stderr

import discord
from discord.ext import commands
from threading import Thread
import asyncio

from env.environement import TALKING_ROLE_NAME, ASKING_ROLE_NAME, PROF_ROLE_NAME, ELEVE_ROLE_NAME, \
    ADMIN_ROLE_NAME, GUILD_NAME, SECURED_VOCAL_SERVER_NAMES, BOT_TOKEN, ALLOWED_ROLES, ALLOWED_CHANNELS

bot = commands.Bot(command_prefix='!')

asking_students = []


class ChannelConnectEvent(Thread):

    def __init__(self, bot, **kwargs):
        Thread.__init__(self)
        self._bot = bot
        self.kwargs = kwargs
        self.setDaemon(True)

    async def start(self):
        await self.run()

    async def run(self):
        channels = {}
        while True:

            for channel in [channel for channel in self._bot.get_all_channels()
                            if channel.type is discord.channel.ChannelType.voice]:
                if channel.name not in channels.keys():
                    channels[channel.name] = channel.members

                left_members = [member for member in channels[channel.name] if member not in channel.members]
                new_members = [member for member in channel.members if member not in channels[channel.name]]

                if self.kwargs['on_vocal_server_joined'] is not None:
                    for member in new_members:
                        await self.kwargs['on_vocal_server_joined'](member, channel)

                if self.kwargs['on_vocal_server_left'] is not None:
                    for member in left_members:
                        await self.kwargs['on_vocal_server_left'](member, channel)

                channels[channel.name] = channel.members

            await asyncio.sleep(0.1)


async def on_vocal_server_joined(member, channel):
    print(f"user @{member.name} connected to {channel.name}")
    #checks if the user is neither allowed to skeak not talking and trying to connect to secured server
    if channel.name in SECURED_VOCAL_SERVER_NAMES\
            and len(set(ALLOWED_ROLES).intersection([role.name for role in member.roles])) <= 0\
            and TALKING_ROLE_NAME not in [role.name for role in member.roles]:
        await mute(member)
    else:
        await unmute(member)


async def on_vocal_server_left(member, channel):
    print(f"user @{member.name} disconnected from {channel.name}")
    if channel.name in SECURED_VOCAL_SERVER_NAMES:
        await unmute(member)
    else:
        await mute(member)


async def is_authorized_channel(ctx):
    return ctx.channel.name in ALLOWED_CHANNELS


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
    for member in guild.members:
        if ELEVE_ROLE_NAME in [role.name for role in member.roles]:
            await mute(member)
        if ASKING_ROLE_NAME in [role.name for role in member.roles]:
            asking_students.append((member.id, member.name, ""))
        elif TALKING_ROLE_NAME in [role.name for role in member.roles]:
            await unmute(member)

    trigger = ChannelConnectEvent(bot, on_vocal_server_joined=on_vocal_server_joined,
                                  on_vocal_server_left=on_vocal_server_left)
    await trigger.start()


@bot.command(brief="lever la main",
             description="commande pour lever la main,\n"
                         "!ask pour connaitre le motif pour lequel on leve la main si l'on lève déjà la main",
             usage="[motif]")
@commands.check(is_authorized_channel)
async def ask(ctx, topic=""):
    if ELEVE_ROLE_NAME in [role.name for role in ctx.author.roles]:

        if ctx.author.id not in [student[0] for student in asking_students] and (TALKING_ROLE_NAME
                                                                                 not in [role.name for role in
                                                                                         ctx.author.roles] or ASKING_ROLE_NAME in [
                                                                                     role.name for role in
                                                                                     ctx.author.roles]):
            asking_students.append((ctx.author.id, ctx.author.name, topic))

            try:
                await add_role(ctx.author, ASKING_ROLE_NAME)
            except discord.errors.Forbidden as e:
                print(e, file=stderr)
            if topic is not "":
                await ctx.send(f"@{ctx.author.name}, vous avez levé la main pour motif : \"{topic}\"")
            else:
                await ctx.send(f"@{ctx.author.name}, vous avez levé la main")

        elif TALKING_ROLE_NAME in [role.name for role in ctx.author.roles]:
            await ctx.send(f"@{ctx.author.name}, vous avez déjà la parole")

        else:
            student = [student for student in asking_students if student[0] is ctx.author.id][0]
            index = asking_students.index(student)

            if topic is "" and student[2] is not "":
                await ctx.send(f"@{student[1]}, vous avez déjà levé la main pour le motif : \"{student[2]}\"")
            elif topic is not "" and student[2] is not "":
                new_student = (ctx.author.id, ctx.author.name, topic)
                asking_students[index] = new_student
                await ctx.send(
                    f"@{new_student[1]}, vous avez remplacé le motif \"{student[2]}\" par le nouveau motif \"{topic}\"")
            elif topic is not "" and student[2] is "":
                new_student = (ctx.author.id, ctx.author.name, topic)
                asking_students[index] = new_student
                await ctx.send(f"@{new_student[1]}, votre motif de prise de parole est \"{topic}\"")


@bot.command(brief="baisser la main",
             description="commande pour baisser la main",
             usage="")
@commands.check(is_authorized_channel)
async def cancel(ctx):
    student = [student for student in asking_students if student[0] is ctx.author.id]
    if len(student) < 1:
        await ctx.send(f"@{ctx.author.name}, vous n'avez pas la main levée")
    else:
        asking_students.remove(student[0])
        await remove_role(ctx.author, ASKING_ROLE_NAME)
        await ctx.send(f"@{ctx.author.name}, vous ne levez plus la main")


@bot.command(brief="liste des élèves levant la main",
             description="montre la liste des élèves levant la main",
             usage="")
@commands.check(is_authorized_channel)
async def list(ctx):
    if PROF_ROLE_NAME in [role.name for role in ctx.author.roles] \
            or ADMIN_ROLE_NAME in [role.name for role in ctx.author.roles]:

        if len(asking_students) is 0:
            await ctx.send("il n'y a aucun élève levant la main")
        else:
            msg = "liste des élèves levant la main: \n"
            for user_id, user_name, topic in asking_students:
                msg += user_name + ", motif: "
                if topic is not "":
                    msg += f"\"{topic}\""
                else:
                    msg += "aucun"
                msg += "\n"
            await ctx.send(msg)

    else:
        await ctx.send(
            f"@{ctx.author.name},vous n\'êtes pas autorisé à accéder à la liste des personnes levant la main")


@bot.command(brief="donner la parole",
             description="utilisez cette commande pour donner la parole à un élève levant la main\n"
                         "le paramètre \"override\" permet de retirer la parole à l'élève en"
                         " train de parler pour la donner à l'élève autorisé\n"
                         "si override vaut \"False\" l'élève ne sera pas "
                         "autorisé tant qu'un autre élève parlera",
             usage="<student_name> [override=False]")
@commands.check(is_authorized_channel)
async def allow(ctx, member_name: str, override=False):
    # checks if the author has an allowed role
    if len(set(ALLOWED_ROLES).intersection(set([role.name for role in ctx.author.roles]))) <= 0:
        await ctx.send("not allowed")
        return

    students = [student for student in asking_students if student[1] == member_name]
    guild = discord.utils.get(bot.guilds, name=GUILD_NAME)
    talking_student = [member for member in guild.members if TALKING_ROLE_NAME in [role.name for role in member.roles]]
    if not override and len(talking_student) is 1:
        await ctx.send(f"l'élève @{talking_student[0].name} est déjà en train de parler, "
                       f"faite \"!allow {member_name} true\" pour "
                       f"autoriser cet élève à parler à la place de {talking_student[0].name}")

    elif len(students) is 1:
        asking_students.pop(asking_students.index(students[0]))
        member = ctx.author.guild.get_member_named(member_name)
        if len(talking_student) is 1:
            talking_student = talking_student[0]

            await remove_role(talking_student, TALKING_ROLE_NAME)
            await mute(talking_student)
            await ctx.send(f"@{talking_student.name}, vous n'avez plus la parole")
        await remove_role(member, ASKING_ROLE_NAME)
        await add_role(member, TALKING_ROLE_NAME)
        await unmute(member)
        await ctx.send(f"@{member_name}, vous avez la parole")
    else:
        await ctx.send(f"{member_name} non trouvé dans la liste des personnes levant la main")


@bot.command(brief="retirer la parole à un élève",
             description="retire le droit de parler à l'élève qui parle",
             usage="")
@commands.check(is_authorized_channel)
async def disallow(ctx, member_name: str):
    if len(set(ALLOWED_ROLES).intersection(set([role.name for role in ctx.author.roles]))) <= 0:
        await ctx.send("not allowed")
        return

    member = ctx.author.guild.get_member_named(member_name)
    if member:
        await mute(member)
        await remove_role(member, TALKING_ROLE_NAME)
        await ctx.send(f"@{member_name}, vous n'avez plus la parole")
    else:
        await ctx.send(f"{member_name} non trouvé")


async def remove_role(member, role_name):
    role = discord.utils.get(member.guild.roles, name=role_name)
    try:
        await member.remove_roles(role)
    except discord.errors.Forbidden as e:
        print(e, file=stderr)


async def add_role(member, role_name):
    role = discord.utils.get(member.guild.roles, name=role_name)
    try:
        print(f"tried to mute {member.name}")
        await member.add_roles(role)
    except discord.errors.Forbidden as e:
        print(e, file=stderr)


async def mute(member):
    channels = [channel for channel in bot.get_all_channels() if channel.type == discord.channel.ChannelType.voice]
    member_in_voice = False
    for channel in channels:
        if member in channel.members:
            await member.edit(mute=True)
            return True

    return False


async def unmute(member):
    channels = [channel for channel in bot.get_all_channels() if channel.type == discord.channel.ChannelType.voice]
    member_in_voice = False
    for channel in channels:
        if member in channel.members:
            await member.edit(mute=False)
            return

    return False


bot.run(BOT_TOKEN)
