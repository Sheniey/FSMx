
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from collections.abc import Iterable
from collections import defaultdict
import inspect

from .fsm_types import (
    Action,
    Guard,
    TransitionMap, Transition, TransitionModel,
    Hook, HookMap,
    RenderMethod
)
from .exceptions import (
    InvalidTransition, InvalidState, InvalidEvent, InvalidTransitionFormat,
    TransitionBlocked, GuardRejected,
    TransitionRewriteAttempt
)
from .utils import console, always_true

class _Mapper[S: Enum, E: Enum, C]:
    def __init__(self, transitions: TransitionMap[S, E, C], render: RenderMethod) -> None:
        self.__transitions: TransitionMap[S, E, C] = transitions
        self.__render: RenderMethod = render

    def json(self, indent: int = 4) -> None:
        formatted_transitions: list[dict[str, str]] = []
        for (state, event), (next_state, func, guard) in self.__transitions.items():
            formatted_transitions.append({
                "from": state.name,
                "event": event.name,
                "to": next_state.name,
                "action": f"{func.__name__}()",
                "guard": f"{guard.__name__}()" if guard else "always_true()"
            })
        console.print_json(data=formatted_transitions, indent=indent)

    def tree(self) -> None:
        match self.__render:
            case 'console':
                for (state, event), (next_state, _, guard) in self.__transitions.items():
                    console.print(f'   [purple]<[/purple][green]{state.name}[/green][purple]> ==[/purple][yellow]{event.name}[/yellow][purple]==> <[/purple][green]{next_state.name}[/green][purple]> : [/purple][cyan]{guard.__name__ if guard else "always_true"}[/cyan]()')

class StateMachineSession[S: Enum, E: Enum, C]:
    def __init__(self, sm: StateMachine[S, E, C], ctx: C, initial_state: S) -> None:
        self.__sm: StateMachine[S, E, C] = sm
        self.__ctx: C = ctx
        self.__state: S = initial_state
        self.__last_event: E | None = None

    # visualization

    def __str__(self) -> str:
        return f'StateMachineSession( current_state:"{self.__state.name}" )'

    def __repr__(self) -> str:
        formatted_repr: str = repr(self.__sm).replace('\n', '\n    ')
        return \
f'''StateMachineSession(
    current_state:"{self.__state.name}",
    context:{self.__ctx!r},
    machine:{formatted_repr}
)'''

    # logic

    def __eq__(self, other: object) -> bool:
        if isinstance(other, S):
            return self.__state == other
        if isinstance(other, StateMachineSession):
            return self.__state == other.current_state 
        raise NotImplemented
    
    def __ne__(self, other: object) -> bool:
        if isinstance(other, S):
            return self.__state != other
        if isinstance(other, StateMachineSession):
            return self.__state != other.current_state
        raise NotImplemented

    # event handling

    def handle(self, event: E) -> S:
        self.__state = self.__sm.dispatch(self.__ctx, self.__state, event)
        self.__last_event = event
        return self.__state
    
    async def handle_async(self, event: E) -> S:
        self.__state = await self.__sm.dispatch_async(self.__ctx, self.__state, event)
        self.__last_event = event
        return self.__state

    def __rshift__(self, event: E) -> StateMachineSession[S, E, C]:
        self.handle(event)
        return self
    
    def __rlshift__(self, event: E) -> StateMachineSession[S, E, C]:
        self.handle(event)
        return self
    

    # aux functions

    @property
    def machine(self) -> StateMachine[S, E, C]:
        return self.__sm

    @property
    def context(self) -> C:
        return self.__ctx
    
    @property
    def current_state(self) -> S:
        return self.__state
    
    @property
    def last_event(self) -> E | None:
        return self.__last_event

@dataclass
class StateMachine[S: Enum, E: Enum, C]:
    transitions: TransitionMap[S, E, C] = field(
        default_factory=dict[
            tuple[S, E],
            Transition[S, C]
        ]
    )
    on_enter_hooks: HookMap[S, C] = field(
        default_factory=lambda: defaultdict(list)
    )
    on_exit_hooks: HookMap[S, C] = field(
        default_factory=lambda: defaultdict(list)
    )
    before_hooks: list[Hook[C]] = field(default_factory=list)
    after_hooks: list[Hook[C]] = field(default_factory=list)

    # visualization

    def _use_plural(self, n: int, singular: str, plural: str | None = None, /) -> str:
        if n == 1:
            return f'{n} {singular}'
        return f"{n} {plural or singular + 's'}"

    def map(self, *, render: RenderMethod = 'console') -> _Mapper[S, E, C]:
        return _Mapper(
            transitions = self.transitions,
            render      = render
        )

    def __str__(self) -> str:
        total_hooks: int = \
            sum(len(hooks) for hooks in self.on_enter_hooks.values()) + \
            sum(len(hooks) for hooks in self.on_exit_hooks.values()) + \
            len(self.before_hooks) + \
            len(self.after_hooks)
        return f'StateMachine( {self._use_plural(len(self), "transition")}, {self._use_plural(total_hooks, "hook")} )'
    
    def __repr__(self) -> str:
        return \
f'''StateMachine(
    {self._use_plural(len(self), "transition")},
    {sum(len(hooks) for hooks in self.on_enter_hooks.values())} hooks::on_enter,
    {sum(len(hooks) for hooks in self.on_exit_hooks.values())} hooks::on_exit,
    {len(self.before_hooks)} hooks::before_each_transition,
    {len(self.after_hooks)} hooks::after_each_transition
)'''


    # meta-methods

    def __len__(self) -> int:
        return len(self.transitions)

    def __enter__(self) -> StateMachine[S, E, C]:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            console.print(f'[red]Error:[/red] {exc_val}')


    # transition registration

    def add_transition(self,
        from_state: S | Iterable[S], event: E, to_state: S,
        func: Action[C],
        guard: Guard[C] | None = None
    ) -> None:
        if isinstance(from_state, Iterable) and not isinstance(from_state, (str, bytes)):
            states = from_state
        else:
            states = (from_state,)

        for s in states:
            key: tuple[S, E] = (s, event)
            if key in self.transitions:
                raise TransitionRewriteAttempt(
                    f'Transition from {s.name} on {event.name} already exists.'
                )
            self.transitions[key] = (to_state, func, guard)

    def transition(self,
        from_state: S | Iterable[S], event: E, to_state: S,
        guard: Guard[C] | None = None
    ) -> Callable[[Action[C]], Action[C]]:
        def decorator(func: Action[C]) -> Action[C]:
            self.add_transition(from_state, event, to_state, func, guard)
            return func

        return decorator

    def __add__(self, other: TransitionModel[S, E, C]) -> StateMachine[S, E, C]:
        try:
            self.add_transition(
                from_state=other['from_state'],
                event=other['event'],
                to_state=other['to_state'],
                func=other['func'],
                guard=other['guard']
            )
            return self
        except KeyError as e:
            raise InvalidTransitionFormat(
                'Invalid transition format : Expected sm_types.TransitionModel.'
            ) from e


    # hook registration

    def add_enter_hook(self, when: S, hook: Hook[C]) -> None:
        self.on_enter_hooks[when].append(hook)

    def add_exit_hook(self, when: S, hook: Hook[C]) -> None:
        self.on_exit_hooks[when].append(hook)

    def add_before_hook(self, hook: Hook[C]) -> None:
        self.before_hooks.append(hook)

    def add_after_hook(self, hook: Hook[C]) -> None:
        self.after_hooks.append(hook)

    def on_enter(self, when: S) -> Callable[[Hook[C]], Hook[C]]:
        def decorator(hook: Hook[C]) -> Hook[C]:
            self.add_enter_hook(when, hook)
            return hook
        return decorator

    def on_exit(self, when: S) -> Callable[[Hook[C]], Hook[C]]:
        def decorator(hook: Hook[C]) -> Hook[C]:
            self.add_exit_hook(when, hook)
            return hook
        return decorator

    def before_each_transition(self, hook: Hook[C] | None = None):
        if hook is None:
            def decorator(hook):
                self.add_before_hook(hook)
                return hook
            return decorator

        self.add_before_hook(hook)
        return hook
    
    def after_each_transition(self, hook: Hook[C] | None = None):
        if hook is None:
            def decorator(hook):
                self.add_after_hook(hook)
                return hook
            return decorator
        self.add_after_hook(hook)
        return hook


    # transition lookup and dumping

    def lookup_transition(self, state: S, event: E) -> Transition[S, C]:
        try:
            return self.transitions[(state, event)]
        except KeyError as e:
            raise InvalidTransition(f'Cannot {event.name} when {state.name}.') from e

    def dump_transition(self,
        from_state: S | None = None,
        event: E | None = None,
        to_state: S | None = None,
        func: Action[C] | None = None,
        guard: Guard[C] | None = None
    ) -> list[TransitionModel[S, E, C]]:
        dumped: list[TransitionModel[S, E, C]] = []
        for (from_, evt), (to_, fx, g) in self.transitions.items():
            if from_state and from_ != from_state:
                continue
            if event and evt != event:
                continue
            if to_state and to_ != to_state:
                continue
            if func and fx != func:
                continue
            if guard and g != guard:
                continue
            dumped.append(TransitionModel(
                from_state=from_,
                event=evt,
                to_state=to_,
                func=fx,
                guard=g if g else always_true
            ))
        return dumped


    # event dispatchers

    def _run_hooks_sync(self, ctx: C, hooks: list[Hook[C]]) -> None:
        for hook in hooks:
            response: Any = hook(ctx)
            if inspect.isawaitable(response):
                raise TransitionBlocked(
                    f'Cannot run async hook {hook.__name__} in sync dispatch : Use dispatch_async instead.'
                )
    
    async def _run_hooks_async(self, ctx: C, hooks: list[Hook[C]]) -> None:
        for hook in hooks:
            response: Any = hook(ctx)
            if inspect.isawaitable(response):
                await response

    def _predispatch(self, ctx: C, state: S, event: E) -> Transition[S, C]:
        next_state, action, guard = self.lookup_transition(state, event)

        if guard and not guard(ctx):
            raise GuardRejected(f'Guard blocked; <{state.name}> =={event.name}==> ???')
        
        return next_state, action, guard
    
    def dispatch(self, ctx: C, state: S, event: E) -> S:
        next_state, action, _ = self._predispatch(ctx, state, event)

        self._run_hooks_sync(ctx, self.before_hooks)
        self._run_hooks_sync(ctx, self.on_exit_hooks[state])

        action(ctx) # syncronous

        self._run_hooks_sync(ctx, self.on_enter_hooks[next_state])
        self._run_hooks_sync(ctx, self.after_hooks)
        
        return next_state
    
    async def dispatch_async(self, ctx: C, state: S, event: E) -> S:
        next_state, action, _ = self._predispatch(ctx, state, event)
    
        await self._run_hooks_async(ctx, self.before_hooks)
        await self._run_hooks_async(ctx, self.on_exit_hooks[state])

        response: Any = action(ctx) # async | sync
        if inspect.isawaitable(response):
            await response

        await self._run_hooks_async(ctx, self.on_enter_hooks[next_state])
        await self._run_hooks_async(ctx, self.after_hooks)
        
        return next_state


    # to be used in a long-running session

    def session(self, ctx: C, initial_state: S) -> StateMachineSession[S, E, C]:
        return StateMachineSession(self, ctx, initial_state)
