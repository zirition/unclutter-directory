
import click


class UnclutterClickGroup(click.Group):
    def __init__(self, *args, **kwargs):
        self._aliases = {}
        self._valid_commands = {}
        self._default_command = None

        super().__init__(*args, **kwargs)

    def add_command(self, *args, **kwargs) -> None:
        super().add_command(*args, **kwargs)

    # Needed to override the command and group methods to process the aliases parameter
    def command(self, *args, **kwargs):
        aliases = kwargs.pop("aliases", [])
        default_command = kwargs.pop("default_command", False)
        default_decorator = super().command(*args, **kwargs)

        def decorator(f):
            cmd = default_decorator(f)

            # Default command
            if default_command:
                if self._default_command is not None:
                    raise ValueError(
                        f"Multiple default commands specified: {cmd.name}, {self._default_command}"
                    )

                self._default_command = cmd.name

            # Aliases
            self._aliases[cmd.name] = aliases
            if cmd.name in self._valid_commands:
                raise ValueError(f"Duplicate command: {cmd.name}")
            self._valid_commands[cmd.name] = cmd.name

            for alias in aliases:
                if alias in self._valid_commands:
                    raise ValueError(f"Duplicate command alias: {alias}")
                self._valid_commands[alias] = cmd.name

            return cmd

        return decorator

    def get_command(self, ctx, cmd_name):
        # Check for an exact match first
        command = super().get_command(ctx, cmd_name)
        if command is not None:
            return command

        # Check for alias
        if cmd_name in self._valid_commands:
            return super().get_command(ctx, self._valid_commands[cmd_name])

        # Check for unique prefixes
        matches = [
            alias for alias in self._valid_commands if alias.startswith(cmd_name)
        ]

        if len(matches) == 1:
            return super().get_command(ctx, self._valid_commands[matches[0]])
        elif len(matches) > 1:
            ctx.fail(
                f"Ambiguous command or alias: '{cmd_name}'. Possible matches: {', '.join(matches)}"
            )

        # Check for default command
        if self._default_command is not None:
            ctx._used_default_command = True
            return super().get_command(ctx, self._default_command)

    def resolve_command(self, ctx, args):
        base = super()
        resolved_cmd_name, resolved_cmd, resolved_args = base.resolve_command(ctx, args)

        # if resolved_cmd_name is not in valid commands, then it is the default command
        if hasattr(ctx, '_used_default_command') and ctx._used_default_command:
            resolved_cmd_name = self._default_command
            resolved_args = args

        return resolved_cmd_name, resolved_cmd, resolved_args

    def format_commands(self, ctx, formatter) -> None:
        rows = []

        sub_commands = self.list_commands(ctx)

        max_len = 0
        if len(sub_commands) > 0:
            max_len = max(len(cmd) for cmd in sub_commands)

        limit = formatter.width - 6 - max_len

        for sub_command in sub_commands:
            cmd = self.get_command(ctx, sub_command)
            if cmd is None:
                continue
            if hasattr(cmd, "hidden") and cmd.hidden:
                continue
            
            aliases = self._aliases[sub_command]
            generated_sub_command = sub_command
            if sub_command == self._default_command:
                generated_sub_command = f"{sub_command} (*)"

            if aliases:
                str_aliases = ", ".join(sorted(aliases))
                generated_sub_command = f"{generated_sub_command} ({str_aliases})"

            cmd_help = cmd.get_short_help_str(limit)
            rows.append((generated_sub_command, cmd_help))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)
