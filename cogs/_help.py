from discord.ext import commands
import discord

import itertools
import datetime


class Help(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(verify_checks=True, **options)

    def embedify(self, title: str, description: str) -> discord.Embed:
        """Returns the default embed used for our HelpCommand"""
        embed = self.context.bot.embed(title=title, description=description)
        embed.set_author(name=self.context.bot.user, icon_url=self.context.bot.user.avatar_url)
        return embed

    def command_not_found(self, string: str) -> str:
        return f"Command or category `{self.clean_prefix}{string}` not found. Try again..."

    def subcommand_not_found(self, command: commands.Command, string) -> str:
        ret = f"Command `{self.context.prefix}{command.qualified_name}` has no subcommands."
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return ret[:-2] + f" named {string}"
        return ret

    @property
    def get_opening_note(self) -> str:
        return f"""Discord bot for the CodinGame API support server.
                   Use **`{self.clean_prefix}help "command name"`** for more info on a command
                   You can also use **`{self.clean_prefix}help "category name"`** for more info on a category
                """

    @staticmethod
    def command_or_group(*obj):
        obj = list(obj)
        cmds = []
        groups = {}

        for command in filter(lambda cmd: isinstance(cmd, commands.Group), obj):
            groups[command.name] = ", ".join(f"*{cmd.name}*" for cmd in command.commands)
            obj.remove(command)

        for command in obj:
            cmds.append(f"*{command.name}*")

        return cmds, groups

    def full_command_path(self, command: commands.Command, include_prefix: bool = True):
        string = f"`{command.qualified_name} {command.signature}`"

        if any(command.aliases):
            string += " | Aliases: "
            string += ", ".join(f"`{alias}`" for alias in command.aliases)

        if include_prefix:
            string = "`" + self.clean_prefix + string[1:]

        return string

    async def send_bot_help(self, mapping):
        embed = self.embedify(title="**General Help**", description=self.get_opening_note)

        no_category = "\u200bNo category"

        def get_category(command, *, no_cat=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_cat

        filtered = await self.filter_commands(self.context.bot.commands, sort=True, key=get_category)
        for category, cmds in itertools.groupby(filtered, key=get_category):
            if cmds:
                cmd_names, group_names = self.command_or_group(*cmds)
                embed.add_field(
                    name=f"**{category}**",
                    value=("**Commands: **" + ", ".join(cmd_names) + "\n") * bool(cmd_names) +
                    ("**Groups: **\n" + "\n".join(
                        f"{group}: {names}" for group, names in group_names.items()
                    )) * bool(group_names),
                    inline=False
                )

        await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = self.embedify(
            title=self.full_command_path(group), description=group.short_doc or "*No special description*"
        )

        filtered = await self.filter_commands(group.commands, sort=True, key=lambda c: c.name)
        if filtered:
            for command in filtered:
                name = self.full_command_path(command)
                if isinstance(command, commands.Group):
                    name = "Group: " + name

                embed.add_field(name=name, value=command.help or "*No specified command description.*", inline=False)

        if len(embed.fields) == 0:
            embed.add_field(name="No commands", value="This group has no commands?")

        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = self.embedify(title=cog.qualified_name, description=cog.description or "*No special description*")

        filtered = await self.filter_commands(cog.get_commands())
        if filtered:
            for command in filtered:
                name = self.full_command_path(command)
                if isinstance(command, commands.Group):
                    name = "Group: " + name

                embed.add_field(name=name, value=command.help or "*No specified command description.*", inline=False)

        await self.context.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = self.embedify(
            title=self.full_command_path(command, include_prefix=True),
            description=command.help or "*No specified command description.*",
        )

        # Testing purposes only.
        try:
            await command.can_run(self.context)
        except Exception as error:
            error = getattr(error, "original", error)

            if isinstance(error, commands.MissingPermissions):
                missing_permissions = error.missing_perms
            elif isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
                missing_permissions = error.missing_roles or [error.missing_role]
            else:
                error_embed = discord.Embed(
                    title="Error you didn't think of",
                    description=f"{self.context.author} raised this error that you didnt think of.",
                    colour=0xFF0000,
                    timestamp=datetime.datetime.utcnow(),
                )
                error_embed.set_author(name="send_command_help")
                error_embed.add_field(name="Type", value=type(error).__name__)
                error_embed.add_field(name="Error", value=str(error))
                error_embed.add_field(name="Channel", value=self.context.channel.mention)
                error_embed.add_field(
                    name="Message", value=f"[{self.context.message.id}]({self.context.message.jump_url})"
                )
                await self.context.bot.get_user(self.context.bot.owner_id).send(embed=error_embed)
                missing_permissions = None

            if missing_permissions is not None:
                embed.add_field(
                    name="You are missing these permissions to run this command:",
                    value=self.list_to_string(missing_permissions),
                )

        await self.context.send(embed=embed)

    @staticmethod
    def list_to_string(_list):
        return ", ".join([obj.name if isinstance(obj, discord.Role) else str(obj).replace("_", " ") for obj in _list])


class NewHelp(commands.Cog, name="Help Command"):
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = Help()
        bot.help_command.cog = self
        bot.get_command("help").hidden = True
        self.bot = bot

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(NewHelp(bot))
