
from typing import Literal, TypedDict, Iterable
from collections.abc import Callable

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

type RenderMethod = Literal['console', 'file', 'diagram']

class TransitionModel[S, E, C](TypedDict):
    from_state: S | Iterable[S]
    event: E
    to_state: S
    func: Action[C]
    guard: Guard[C] | None
