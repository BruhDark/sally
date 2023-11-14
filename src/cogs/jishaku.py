from discord.ext import commands

from jishaku.features.python import codeblock_converter, get_var_dict_from_ctx, ReplResponseReactor, AsyncCodeExecutor, AsyncSender, Flags
from jishaku.features.baseclass import Feature

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES


class CustomDebugCog(*STANDARD_FEATURES, *OPTIONAL_FEATURES):

    @Feature.Command(parent=None, name="eval", aliases=["e"])
    async def jsk_eval_python(self, ctx: commands.Context, *,
                              argument: codeblock_converter):
        """
            Direct evaluation of Python code.
            """

        arg_dict = get_var_dict_from_ctx(ctx, Flags.SCOPE_PREFIX)
        arg_dict["_"] = self.last_result

        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with self.submit(ctx):
                    executor = AsyncCodeExecutor(argument.content,
                                                 scope,
                                                 arg_dict=arg_dict)
                    async for send, result in AsyncSender(executor):
                        if result is None:
                            continue

                        self.last_result = result

                        send(await self.jsk_python_result_handling(ctx, result))

        finally:
            scope.clear_intersection(arg_dict)


def setup(bot: commands.Bot):
    bot.add_cog(CustomDebugCog(bot=bot))
