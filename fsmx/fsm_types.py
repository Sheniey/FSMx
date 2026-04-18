
from typing import Literal, TypedDict, Iterable
from collections.abc import Callable
from enum import Enum

type Action[C] = Callable[[C], None]
type Guard[C] = Callable[[C], bool]

type Transition[S, C] = tuple[S, Action[C], Guard[C] | None]
type TransitionMap[S, E, C] = dict[
    tuple[
        S,
        E
    ],
    Transition[S, C]
]

type Hook[C] = Callable[[C], None]
type HookMap[S, C] = dict[S, list[Hook[C]]]

class TransitionModel[S: Enum, E: Enum, C](TypedDict):
    from_state: S | Iterable[S]
    event: E
    to_state: S
    func: Action[C]
    guard: Guard[C] | None

type VisualizePart = Literal['transitions', 'hooks']
type RequiredParts = VisualizePart | Literal['any'] | Literal['all']
class StateMachinePayload[S: Enum, E: Enum, C](TypedDict):
    class _HookSummary(TypedDict):
        on_enter: HookMap[S, C]
        on_exit: HookMap[S, C]
        before_each_transition: list[Hook[C]]
        after_each_transition: list[Hook[C]]

    transitions: TransitionMap[S, E, C]
    hooks: _HookSummary
