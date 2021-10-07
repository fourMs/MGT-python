def show_async(command):
    """Helper function to show ffplay windows asynchronously"""
    import asyncio

    async def run_cmd(command):
        process = await asyncio.create_subprocess_shell(command)
        await process.communicate()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # if cleanup: 'RuntimeError: There is no current event loop..'
        loop = None

    if loop and loop.is_running():
        tsk = loop.create_task(run_cmd(command))
    else:
        asyncio.run(run_cmd(command))