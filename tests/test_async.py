
from fsmx import StateMachine
from enum import Enum, auto
from dataclasses import dataclass, field
import asyncio

class CPUPipeState(Enum):
    FETCHING = auto()
    DECODING = auto()
    EXECUTING = auto()

class CPUPipeEvent(Enum):
    FETCH = auto()
    DECODE = auto()
    EXECUTE = auto()

@dataclass
class CPUPipeCtx:
    cycle_count: int = 0



pipeline_sm: StateMachine[CPUPipeState, CPUPipeEvent, CPUPipeCtx] = StateMachine()


@pipeline_sm.after_each_transition
async def log_cycle(ctx: CPUPipeCtx) -> None:
    ctx.cycle_count += 1
    print(f"Cycle {ctx.cycle_count} complete")

@pipeline_sm.transition(CPUPipeState.FETCHING, CPUPipeEvent.FETCH, CPUPipeState.DECODING)
def fetch(ctx: CPUPipeCtx) -> None:
    print('Fetching instruction')

@pipeline_sm.transition(CPUPipeState.DECODING, CPUPipeEvent.DECODE, CPUPipeState.EXECUTING)
def decode(ctx: CPUPipeCtx) -> None:
    print('Decoding instruction')

@pipeline_sm.transition(CPUPipeState.EXECUTING, CPUPipeEvent.EXECUTE, CPUPipeState.FETCHING)
def execute(ctx: CPUPipeCtx) -> None:
    print('Executing instruction')



@dataclass
class CPU:
    ctx: CPUPipeCtx
    state: CPUPipeState = CPUPipeState.FETCHING
    last_event: CPUPipeEvent = CPUPipeEvent.FETCH

    async def do_cycle(self) -> None:
        self.state = await pipeline_sm.dispatch_async(self.ctx, self.state, self.last_event)
        self.last_event = pipeline_sm.dump_transition(
            from_state=self.state,
            event=self.last_event
        )[-1]['event']

async def main() -> None:
# ===================================
    cpu: CPU = CPU(ctx=CPUPipeCtx())
    for _ in range(3):
        await cpu.do_cycle()
# ===================================


if __name__ == '__main__':
    asyncio.run(main())
