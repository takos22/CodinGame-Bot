import discord
from discord.ext import commands

import itertools
import logging

from core import Bot
from utils import color


class Help(commands.HelpCommand):
    context: commands.Context

    def __init__(self, logger: logging.Logger, **options):
        super().__init__(verify_checks=True, **options)
        self.logger = logger

    # ---------------------------------------------------------------------------------------------
    # Methods

    def embedify(self, title: str, description: str) -> discord.Embed:
        """Returns the default embed used for our HelpCommand"""
        embed: discord.Embed = self.context.bot.embed(
            ctx=self.context, title=title, description=description
        )
        embed.set_author(name=self.context.bot.user, icon_url=self.context.bot.user.avatar_url)
        return embed

    def command_not_found(self, command: str) -> str:
        return f"Command or category `{self.clean_prefix}{command}` not found. Try again..."

    def subcommand_not_found(self, command: commands.Command, string) -> str:
        ret = f"Command `{self.context.prefix}{command.qualified_name}` has no subcommands."
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return ret[:-2] + f" named {string}"
        return ret

    def full_command_path(self, command: commands.Command, include_prefix: bool = True):
        string = f"`{command.qualified_name} {command.signature}`"

        if any(command.aliases):
            string += " | Aliases: "
            string += ", ".join(f"`{alias}`" for alias in command.aliases)

        if include_prefix:
            string = "`" + self.clean_prefix + string[1:]

        return string

    @property
    def opening_note(self) -> str:
        return (
            f"Discord bot for the CodinGame API support server.\n"
            f"Use `{self.clean_prefix}help [command name]` for more info on a command.\n"
            f"Use `{self.clean_prefix}help [category name]` for more info on a category.\n"
        )

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

    @staticmethod
    def list_to_string(_list: list) -> str:
        return ", ".join(
            [
                obj.name if isinstance(obj, discord.Role) else str(obj).replace("_", " ")
                for obj in _list
            ]
        )

    # ---------------------------------------------------------------------------------------------
    # Help commands

    async def send_bot_help(self, mapping):
        embed = self.embedify(title="**General Help**", description=self.opening_note)

        no_category = "\u200bNo category"

        def get_category(command, *, no_cat=no_category):
            cog: commands.Cog = command.cog
            return cog.qualified_name if cog else no_cat

        filtered = await self.filter_commands(
            self.context.bot.commands, sort=True, key=get_category
        )
        for category, cmds in itertools.groupby(filtered, key=get_category):
            if cmds:
                cmd_names, group_names = self.command_or_group(*cmds)
                embed.add_field(
                    name=f"**{category}**",
                    value=("**Commands:** " + ", ".join(cmd_names) + "\n") * bool(cmd_names)
                    + (
                        "**Groups: **\n"
                        + "\n".join(
                            f"{group}: {names}" for group, names in group_names.items()
                        )
                    )
                    * bool(group_names),
                    inline=False,
                )

        self.logger.info("general help sent")
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
                await self.context.bot.handle_error(error, ctx=self.context)
                missing_permissions = None

            if missing_permissions is not None:
                embed.add_field(
                    name="You are missing these permissions to run this command:",
                    value=self.list_to_string(missing_permissions),
                )

        self.logger.info(f"command `{command.name}` help sent")
        await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = self.embedify(
            title=self.full_command_path(group),
            description=group.short_doc or "*No special description*",
        )

        filtered = await self.filter_commands(group.commands, sort=True, key=lambda c: c.name)
        if filtered:
            for command in filtered:
                name = self.full_command_path(command)
                if isinstance(command, commands.Group):
                    name = "Group: " + name

                embed.add_field(
                    name=name,
                    value=command.help or "*No specified command description.*",
                    inline=False,
                )

        if not embed.fields:
            embed.add_field(name="No commands", value="This group has no commands?")

        self.logger.info(f"group `{group.name}` help sent")
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = self.embedify(
            title=cog.qualified_name, description=cog.description or "*No special description*"
        )

        filtered = await self.filter_commands(cog.get_commands())
        if filtered:
            for command in filtered:
                name = self.full_command_path(command)
                if isinstance(command, commands.Group):
                    name = "Group: " + name

                embed.add_field(
                    name=name,
                    value=command.help or "*No specified command description.*",
                    inline=False,
                )

        self.logger.info(f"cog `{cog.qualified_name}` help sent")
        await self.context.send(embed=embed)


class NewHelp(commands.Cog, name="Help Command"):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.logger = self.bot.logger.getChild("help")

        self._original_help_command: commands.HelpCommand = bot.help_command
        bot.help_command = Help(logger=self.logger)
        bot.help_command.cog = self
        bot.get_command("help").hidden = True

        self.logger.info(color("cog `Help Command` loaded", "blue"))

    def cog_unload(self):
        self.bot.help_command = self._original_help_command
        self.logger.info(color("cog `Help Command` unloaded", "yellow"))


def setup(bot: Bot):
    bot.add_cog(NewHelp(bot))
