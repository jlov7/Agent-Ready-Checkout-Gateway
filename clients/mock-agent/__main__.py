from .mock_agent.workflow import run_demo


if __name__ == "__main__":
    import asyncio

    state = asyncio.run(run_demo())
    print("Fulfilment complete:", state.get("fulfilment"))
