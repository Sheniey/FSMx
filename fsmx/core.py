
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Self
from collections.abc import Iterable
from collections import defaultdict
import inspect
from questionary import select

from .fsm_types import (
    Action,
    Guard,
    TransitionMap, Transition, TransitionModel,
    Hook, HookMap,
    VisualizePart,
    StateMachinePayload
)
from .exceptions import (
    InvalidTransitionError, InvalidStateError, InvalidEventError, InvalidTransitionFormatError,
    TransitionBlockedError, GuardRejectedError,
    TransitionRewriteError,
)
from .utils import always_true
from .tools import console

class Reactive[E: Enum]:
    """
    Base class for custom classes that require reactive capabilities.

    By inheriting from `Reactive`, a class gains support for the
    `>>` operator, allowing events to be handled in a fluent style.

    Example:
        >>> class MyClass(Reactive[MyEvent]):
        ... state: MyState = MyState.INITIAL
        ...
        ... def handle(self, event: MyEvent) -> None:
        ...     self.state = my_sm.dispatch(self, self.state, event)
        
        >>> my_object = MyClass()

        >>> my_object >> MyEvent.START >> MyEvent.PROCESS >> MyEvent.FINISH
    """

    def __rshift__(self, event: E) -> Self:
        """
        Handles an event using the right-shift operator.

        This enables fluent event chaining:

            obj >> Event.START >> Event.NEXT

        Args:
            event (E): The event to process.

        Returns:
            Self: The current instance for chaining.
        """

        self.handle(event)
        return self

    def handle(self, event: E, *args: Any, **kwargs: Any) -> None:
        """
        By default, when `Reactive` class is inherited this function is provided as a placeholder but **raises `NotImplementedError`** if not overridden.
        
        Please implement your `.handle()` method in your subclass to define how it should react to events.

        Example:
            >>> class MyClass(Reactive[MyEvent]):
            ... state: MyState = MyState.INITIAL
            ...
            ... def handle(self, event: MyEvent) -> None:
            ...     self.state = my_sm.dispatch(self, self.state, event)

        Args:
            event (E): The event to handle.

        Raises:
            NotImplementedError: If the method is not overridden in the subclass.
        """
        raise NotImplementedError(f'Reactive[{E.__name__}] subclasses must implement .handle() method.')

class StateMachineInstance[S: Enum, E: Enum, C](Reactive[E]):
    """
    *"Active session of a state machine."*

    Represents an active session of a state machine, maintaining the current state and context.
    
    This class allows for handling events and transitioning between states according to the defined state machine.
    
    Attributes:
        machine (StateMachine[S, E, C]): The state machine definition.
        context (C): The context object that can be used in guards and actions.
        current_state (S): The current state of the session.
        last_event (E | None): The last event that was handled, or None if no events have been handled yet.
    """

    def __init__(self, sm: StateMachine[S, E, C], ctx: C, initial_state: S) -> None:
        """
        *"Initializes a new state machine session."*

        Args:
            sm (StateMachine[S, E, C]): The state machine definition to use for this session.
            ctx (C): The context object that can be used in guards and actions.
            initial_state (S): The initial state of the session.
        """

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
        if isinstance(other, StateMachineInstance):
            return self.__state == other.current_state 
        raise NotImplemented
    
    def __ne__(self, other: object) -> bool:
        if isinstance(other, S):
            return self.__state != other
        if isinstance(other, StateMachineInstance):
            return self.__state != other.current_state
        raise NotImplemented

    # event handling

    def handle(self, event: E) -> S:
        """
        *"Handles an event synchronously, updating the current state accordingly."*

        Args:
            event (E): The event to handle.

        Returns:
            S: The new current state after handling the event.
        """

        self.__state = self.__sm.dispatch(self.__ctx, self.__state, event)
        self.__last_event = event
        return self.__state
    
    async def handle_async(self, event: E) -> S:
        """
        *"Handles an event asynchronously, updating the current state accordingly."*

        Args:
            event (E): The event to handle.

        Returns:
            S: The new current state after handling the event.
        """

        self.__state = await self.__sm.dispatch_async(self.__ctx, self.__state, event)
        self.__last_event = event
        return self.__state

    # aux functions

    @property
    def machine(self) -> StateMachine[S, E, C]:
        """
        *"Returns the state machine of the session."*

        Returns the state machine definition associated with this session.
        
        Returns:
            StateMachine[S, E, C]: The state machine definition.
        """
        return self.__sm

    @property
    def context(self) -> C:
        """
        *"Returns the context object of the session."*

        Returns the context object associated with this session.

        Returns:
            C: The context object.
        """
        return self.__ctx
    
    @property
    def current_state(self) -> S:
        """
        *"Returns the state of the session."*

        Returns the current state of the session.

        Returns:
            S: The current state.
        """
        return self.__state
    
    @property
    def last_event(self) -> E | None:
        """
        *"Returns the last event that was handled."*

        Returns the last event that was handled, or `None` if no events have been handled yet.

        Returns:
            E | None: The last event or None.
        """
        return self.__last_event

@dataclass
class StateMachine[S: Enum, E: Enum, C]:
    """
    *"Automat: Finite State Machine."*

    Represents a finite state machine definition, including its transitions and hooks.
    
    This class allows for defining transitions, registering hooks, and dispatching events to transition between states.
    
    Attributes:
        transitions (TransitionMap[S, E, C]): A mapping of state-event pairs to their corresponding transitions.
        on_enter_hooks (HookMap[S, C]): A mapping of states to their associated on-enter hooks.
        on_exit_hooks (HookMap[S, C]): A mapping of states to their associated on-exit hooks.
        before_hooks (list[Hook[C]]): A list of hooks to run before every transition.
        after_hooks (list[Hook[C]]): A list of hooks to run after every transition.
    
    Example:
        There are examples about how to use this class on:
        https://github.com/Sheniey/FSMx#samples
    """

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

    def export(self) -> None:
        raise NotImplementedError('Export functionality is not implemented yet.')

    # visualization

    def _use_plural(self, n: int, singular: str, plural: str | None = None, /) -> str:
        """
        *"Pluralizes a word based on the count."*

        An `protected` internal helper function to format a string with correct pluralization based on the count `n`.

        Example:
            >>> _use_plural(1, 'transition')
            '1 transition'
            >>> _use_plural(3, 'transition')
            '3 transitions'
            >>> _use_plural(1, 'child', 'children')
            '1 child'
            >>> _use_plural(5, 'child', 'children')
            '5 children'

        Args:
            n (int): The count to determine singular or plural form.
            singular (str): The singular form of the word.
            plural (str | None, optional): The plural form of the word. If not provided, it defaults to the singular form with an 's' appended.

        Returns:
            str: A formatted string with the count and the correct singular or plural form of the word.
        """
        if n == 1:
            return f'{n} {singular}'
        return f"{n} {plural or singular + 's'}"

    def visualize(self, include: list[VisualizePart] = ['transitions']) -> None:
        raise NotImplementedError('Visualization functionality is not implemented yet.')

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
        """Returns the number of transitions defined in the state machine."""
        return len(self.transitions)

    def __enter__(self) -> StateMachine[S, E, C]:
        """I don't know what the hell does this do but it seems like a good idea to have it."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """I don't know what the hell does this do but it seems like a good idea to have it."""
        if exc_type:
            console.print(f'[red]Error:[/red] {exc_val}')


    # transition registration

    def add_transition(self,
        from_state: S | Iterable[S], event: E, to_state: S,
        func: Action[C],
        guard: Guard[C] | None = None
    ) -> None:
        """
        *"Registers a transition in the state machine."*

        You could consider using `.transition()` instead, which is a decorator-based alternative to this method.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add a transition when in INITIAL state, on START event, go to STARTED state and execute start_action if the guard always_true is satisfied"
            >>> sm.add_transition(
            ...     from_state=MyState.INITIAL,
            ...     event=MyEvent.START,
            ...     to_state=MyState.STARTED,
            ...     func=start_action,
            ...     guard=always_true
            ... )

        Args:
            from_state (S | Iterable[S]): The state or states from which the transition originates.
            event (E): The event that triggers the transition.
            to_state (S): The state to which the transition leads.
            func (Action[C]): The action to execute when the transition occurs.
            guard (Guard[C] | None, optional): An optional guard function that determines whether the transition should occur based on the context. Defaults to None.
        
        Raises:
            TransitionRewriteError: If a transition from the same state on the same event already exists.
        """

        if isinstance(from_state, Iterable) and not isinstance(from_state, (str, bytes)):
            states = from_state
        else:
            states = (from_state,)

        for s in states:
            key: tuple[S, E] = (s, event)
            if key in self.transitions:
                raise TransitionRewriteError(
                    f'Transition from {s.name} on {event.name} already exists.'
                )
            self.transitions[key] = (to_state, func, guard)

    def transition(self,
        from_state: S | Iterable[S], event: E, to_state: S,
        guard: Guard[C] | None = None
    ) -> Callable[[Action[C]], Action[C]]:
        """
        *"Registers a transition in the state machine."*

        A decorator-based alternative to `add_transition` for registering transitions in a more fluent style.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add a transition when in INITIAL state, on START event, go to STARTED state and execute this function below if the guard always_true is satisfied"
            >>> @sm.transition(from_state=MyState.INITIAL, event=MyEvent.START, to_state=MyState.STARTED, guard=always_true)
            ... def start_action(context: MyContext):
            ...     pass

        Args:
            from_state (S | Iterable[S]): The state or states from which the transition originates.
            event (E): The event that triggers the transition.
            to_state (S): The state to which the transition leads.
            guard (Guard[C] | None, optional): An optional guard function that determines whether the transition should occur based on the context. Defaults to None.
        
        Returns:
            Callable[[Action[C]], Action[C]]: A decorator function that takes an action and registers the transition with that action.

        Raises:
            Anything: Raises the same exceptions as `add_transition` if the transition registration fails.
        """

        def decorator(func: Action[C]) -> Action[C]:
            self.add_transition(from_state, event, to_state, func, guard)
            return func

        return decorator

    def __add__(self, other: TransitionModel[S, E, C]) -> StateMachine[S, E, C]:
        """
        *"Registers a transition in the state machine using the `+` operator."*

        Allows adding a transition to the state machine using the `+` operator with a `TransitionModel` instance.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add a transition when in INITIAL state, on START event, go to STARTED state and execute start_action if the guard always_true is satisfied"
            >>> sm = sm + TransitionModel(
            ...     from_state=MyState.INITIAL,
            ...     event=MyEvent.START,
            ...     to_state=MyState.STARTED,
            ...     func=start_action,
            ...     guard=always_true
            ... )
        
        Args:
            other (TransitionModel[S, E, C]): A transition model containing the details of the transition to add.
        
        Returns:
            StateMachine[S, E, C]: The state machine instance with the new transition added.

        Raises:
            InvalidTransitionFormatError: If the provided `other` does not have the expected format of a `TransitionModel`.
            Anything: Raises the same exceptions as `add_transition` if the transition registration fails.
        """

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
            raise InvalidTransitionFormatError(
                'Invalid transition format : Expected sm_types.TransitionModel.'
            ) from e


    # hook registration

    def add_enter_hook(self, when: S, hook: Hook[C]) -> None:
        """
        *"Registers an on-enter hook for a specific state."*

        You could also use `.on_enter()` instead, which is a decorator-based alternative to this method.
        
        Mental Note:
        ```
            <before_each_transition_hooks>
            <on_exit_hooks[current_state]>

            <action>

            <ON_ENTER_HOOKS[NEXT_STATE]> # this is the one being registered here
            <after_each_transition_hooks>
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> def on_enter_started(context: MyContext):
            ...     pass
            >>>
            >>> # this reads like: "Add an on-enter hook for STARTED state that executes the function below when entering STARTED state"
            >>> sm.add_enter_hook(when=MyState.STARTED, hook=on_enter_started)

        Args:
            when (S): The state for which to register the on-enter hook.
            hook (Hook[C]): The hook function to execute when entering the specified state.
        """
        self.on_enter_hooks[when].append(hook)

    def add_exit_hook(self, when: S, hook: Hook[C]) -> None:
        """
        *"Registers an on-exit hook for a specific state."*

        You could also use `.on_exit()` instead, which is a decorator-based alternative to this method.

        Mental Note:
        ```
            <before_each_transition_hooks>
            <ON_EXIT_HOOKS[CURRENT_STATE]> # this is the one being registered here

            <action>

            <on_enter_hooks[next_state]>
            <after_each_transition_hooks>
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> def on_exit_initial(context: MyContext):
            ...     pass
            >>>
            >>> # this reads like: "Add an on-exit hook for INITIAL state that executes the function below when exiting INITIAL state"
            >>> sm.add_exit_hook(when=MyState.INITIAL, hook=on_exit_initial)
        
        Args:
            when (S): The state for which to register the on-exit hook.
            hook (Hook[C]): The hook function to execute when exiting the specified state.
        """
        self.on_exit_hooks[when].append(hook)

    def add_before_hook(self, hook: Hook[C]) -> None:
        """
        *"Registers a hook to be executed before every transition."*

        There's another method called `.before_each_transition()` that can be used as a decorator or as a direct method to register before-transition hooks, so you can choose the style you prefer.

        Mental Note:
        ```
            <BEFORE_EACH_TRANSITION_HOOKS> # this is the one being registered here
            <on_exit_hooks[current_state]>
            
            <action>
            
            <on_enter_hooks[next_state]>
            <after_each_transition_hooks>
        ```
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> def before_any_transition(context: MyContext):
            ...     pass
            >>>
            >>> # this reads like: "Add a hook that executes the function below before every transition"
            >>> sm.add_before_hook(before_any_transition)
        
        Args:
            hook (Hook[C]): The hook function to execute before every transition.
        """
        self.before_hooks.append(hook)

    def add_after_hook(self, hook: Hook[C]) -> None:
        """
        *"Registers a hook to be executed after every transition."*

        There's another method called `.after_each_transition()` that can be used as a decorator or as a direct method to register after-transition hooks, so you can choose the style you prefer.

        Mental Note:
        ```
            <before_each_transition_hooks>
            <on_exit_hooks[current_state]>
            
            <action>
            
            <on_enter_hooks[next_state]>
            <AFTER_EACH_TRANSITION_HOOKS> # this is the one being registered here
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> def after_any_transition(context: MyContext):
            ...     pass
            >>>
            >>> # this reads like: "Add a hook that executes the function below after every transition"
            >>> sm.add_after_hook(after_any_transition)

        Args:
            hook (Hook[C]): The hook function to execute after every transition.
        """
        self.after_hooks.append(hook)

    def on_enter(self, when: S) -> Callable[[Hook[C]], Hook[C]]:
        """
        *"Registers an on-enter hook for a specific state."*

        A decorator-based alternative to `add_enter_hook` for registering on-enter hooks in a more fluent style.
        
        Mental Note:
        ```
            <before_each_transition_hooks>
            <on_exit_hooks[current_state]>

            <action>

            <ON_ENTER_HOOKS[NEXT_STATE]> # this is the one being registered here
            <after_each_transition_hooks>
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add an on-enter hook for INITIAL state that executes the function below when entering INITIAL state"
            >>> @sm.on_enter(MyState.INITIAL)
            ... def on_enter_initial(context: MyContext):
            ...     pass
        
        Args:
            when (S): The state for which to register the on-enter hook.
        """

        def decorator(hook: Hook[C]) -> Hook[C]:
            self.add_enter_hook(when, hook)
            return hook
        return decorator

    def on_exit(self, when: S) -> Callable[[Hook[C]], Hook[C]]:
        """
        *"Registers an on-exit hook for a specific state."*

        A decorator-based alternative to `add_exit_hook` for registering on-exit hooks in a more fluent style.

        Mental Note:
        ```
            <before_each_transition_hooks>
            <ON_EXIT_HOOKS[CURRENT_STATE]> # this is the one being registered here

            <action>

            <on_enter_hooks[next_state]>
            <after_each_transition_hooks>
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add an on-exit hook for INITIAL state that executes the function below when exiting INITIAL state"
            >>> @sm.on_exit(MyState.INITIAL)
            ... def on_exit_initial(context: MyContext):
            ...     pass

        Args:
            when (S): The state for which to register the on-exit hook.
        """

        def decorator(hook: Hook[C]) -> Hook[C]:
            self.add_exit_hook(when, hook)
            return hook
        return decorator

    def before_each_transition(self, hook: Hook[C] | None = None):
        """
        *"Registers a hook to be executed before every transition."*
        
        Mental Note:
        ```
            <BEFORE_EACH_TRANSITION_HOOKS> # this is the one being registered here
            <on_exit_hooks[current_state]>
            
            <action>
            
            <on_enter_hooks[next_state]>
            <after_each_transition_hooks>
        ```

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add a hook that executes the function below before every transition"
            >>> @sm.before_each_transition()
            ... def before_any_transition(context: MyContext):
            ...     pass
        
        Args:
            hook (Hook[C] | None, optional): The hook function to execute before every transition. If not provided, the method can be used as a decorator. Defaults to None.
        """

        if hook is None:
            def decorator(hook):
                self.add_before_hook(hook)
                return hook
            return decorator

        self.add_before_hook(hook)
        return hook
    
    def after_each_transition(self, hook: Hook[C] | None = None):
        """
        *"Registers a hook to be executed after every transition."*
        
        Mental Note:
        ```
            <before_each_transition_hooks>
            <on_exit_hooks[current_state]>

            <action>
             
            <on_enter_hooks[next_state]>
            <AFTER_EACH_TRANSITION_HOOKS> # this is the one being registered here
        ```
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # this reads like: "Add a hook that executes the function below after every transition"
            >>> @sm.after_each_transition()
            ... def after_any_transition(context: MyContext):
            ...     pass

        Args:
            hook (Hook[C] | None, optional): The hook function to execute after every transition. If not provided, the method can be used as a decorator. Defaults to None.
        """

        if hook is None:
            def decorator(hook):
                self.add_after_hook(hook)
                return hook
            return decorator
        self.add_after_hook(hook)
        return hook


    # transition lookup and dumping

    def lookup_transition(self, state: S, event: E) -> Transition[S, C]:
        """
        *"Looks up the transition for a given state and event."*

        Internal purpose function to look up the transition for a given state and event.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # Assuming a transition from INITIAL state on START event is defined as follows:
            >>> sm.add_transition(
            ...     from_state=MyState.INITIAL,
            ...     event=MyEvent.START,
            ...     to_state=MyState.STARTED,
            ...     func=start_action,
            ...     guard=always_true
            ... )
            >>> # Then, looking up the transition for INITIAL state and START event would return:
            >>> sm.lookup_transition(MyState.INITIAL, MyEvent.START)
            (MyState.STARTED, start_action, always_true)
        
        Args:
            state (S): The current state for which to look up the transition.
            event (E): The event for which to look up the transition.
        
        Returns:
            Transition[S, C]: A tuple containing the next state, the action to execute, and the guard function (if any) for the transition corresponding to the given state and event.
        
        Raises:
            InvalidTransitionError: If no transition is defined for the given state and event.
        """
        try:
            return self.transitions[(state, event)]
        except KeyError as e:
            raise InvalidTransitionError(f'Cannot {event.name} when {state.name}.') from e

    def dump_transition(self,
        *,
        from_state: S | None = None,
        event: E | None = None,
        to_state: S | None = None,
        func: Action[C] | None = None,
        guard: Guard[C] | None = None
    ) -> list[TransitionModel[S, E, C]]:
        """
        *"Dumps the transitions based on the provided filters."*

        Args:
            from_state (S | None): Filter by the source state.
            event (E | None): Filter by the event.
            to_state (S | None): Filter by the destination state.
            func (Action[C] | None): Filter by the action function.
            guard (Guard[C] | None): Filter by the guard function.

        Returns:
            list[TransitionModel[S, E, C]]: A list of transition models matching the filters.
        """
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
        """
        *"Execute all hooks synchronously, not permitting async hooks in sync dispatch."*
        
        An `protected` internal function to run hooks synchronously, ensuring that if any hook returns an awaitable, a `TransitionBlocked` exception is raised to prevent asynchronous hooks from being run in a synchronous dispatch.

        Args:
            ctx (C): The context to pass to the hooks.
            hooks (list[Hook[C]]): The list of hooks to run.

        Raises:
            TransitionBlockedError: If any hook returns an awaitable, indicating that asynchronous hooks cannot be run in a synchronous dispatch.
        """

        for hook in hooks:
            response: Any = hook(ctx)
            if inspect.isawaitable(response):
                raise TransitionBlockedError(
                    f'Cannot run async hook {hook.__name__} in sync dispatch : Use dispatch_async instead.'
                )
    
    async def _run_hooks_async(self, ctx: C, hooks: list[Hook[C]]) -> None:
        """
        *"Execute all hooks asynchronously, awaiting any hook that returns an awaitable."*

        An `protected` internal function to run hooks asynchronously, awaiting any hook that returns an awaitable.

        Args:
            ctx (C): The context to pass to the hooks.
            hooks (list[Hook[C]]): The list of hooks to run.
        """

        for hook in hooks:
            response: Any = hook(ctx)
            if inspect.isawaitable(response):
                await response

    def _predispatch(self, ctx: C, state: S, event: E) -> Transition[S, C]:
        """
        *"Prepare for a state transition."*

        An `protected` internal helper to perform pre-dispatch checks and retrieve the transition details for a given state and event.
        
        This function looks up the transition for the given state and event, checks the guard condition (if any), and returns the next state, action, and guard for the transition. If the guard condition is not satisfied, a `GuardRejected` exception is raised.
        
        Args:
            ctx (C): The context to pass to the guard function.
            state (S): The current state for which to look up the transition.
            event (E): The event for which to look up the transition.
            
        Returns:
            Transition[S, C]: A tuple containing the next state, the action to execute, and the guard function (if any) for the transition corresponding to the given state and event.
        
        Raises:
            InvalidTransitionError: If no transition is defined for the given state and event.
            GuardRejectedError: If the guard condition for the transition is not satisfied.    
        """
        next_state, action, guard = self.lookup_transition(state, event)

        if guard and not guard(ctx):
            raise GuardRejectedError(f'Guard blocked; <{state.name}> =={event.name}==> ???')
        
        return next_state, action, guard
    
    def dispatch(self, ctx: C, state: S, event: E) -> S:
        """
        *"Handle an event synchronously, asynchrony is not allowed."*

        Dispatches an event synchronously, performing the state transition if the guard conditions are satisfied and executing the associated hooks and action.
        
        This function performs the following steps:
            1. Looks up the transition for the given state and event, and checks the guard condition (if any) using the `_predispatch` helper function.
            2. Executes the `before-transition` hooks.
            3. Executes the `on-exit` hooks for the current state.
            4. Executes the `main action` associated with the transition.
            5. Executes the `on-enter` hooks for the next state.
            6. Executes the `after-transition` hooks.
            7. Returns the next state after the transition.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # Assuming a transition from INITIAL state on START event is defined as follows:
            >>> sm.add_transition(
            ...     from_state=MyState.INITIAL,
            ...     event=MyEvent.START,
            ...     to_state=MyState.STARTED,
            ...     func=start_action,
            ...     guard=always_true
            ... )
            >>> # Then, dispatching the START event from INITIAL state with a context would execute the transition and return the next state:
            >>> sm.dispatch(context, MyState.INITIAL, MyEvent.START)
            MyState.STARTED

        Args:
            ctx (C): The context to pass to the guard, action, and hooks.
            state (S): The current state from which to transition.
            event (E): The event that triggers the transition.
            
        Returns:
            S: The next state after the transition.
            
        Raises:
            InvalidTransitionError: If no transition is defined for the given state and event.
            GuardRejectedError: If the guard condition for the transition is not satisfied.
            TransitionBlockedError: If any hook returns an awaitable, indicating that asynchronous hooks cannot be run in a synchronous dispatch.
        """

        next_state, action, _ = self._predispatch(ctx, state, event)

        self._run_hooks_sync(ctx, self.before_hooks)
        self._run_hooks_sync(ctx, self.on_exit_hooks[state])

        action(ctx) # synchronous

        self._run_hooks_sync(ctx, self.on_enter_hooks[next_state])
        self._run_hooks_sync(ctx, self.after_hooks)
        
        return next_state
    
    async def dispatch_async(self, ctx: C, state: S, event: E) -> S:
        """
        *"Handle an event asynchronously."*

        Dispatches an event asynchronously, performing the state transition if the guard conditions are satisfied and executing the associated hooks and action, awaiting any asynchronous hooks or actions as needed.

        This function performs the following steps:
            1. Looks up the transition for the given state and event, and checks the guard condition (if any) using the `_predispatch` helper function.
            2. Executes the `before-transition` hooks, awaiting any that are asynchronous.
            3. Executes the `on-exit` hooks for the current state, awaiting any that are asynchronous.
            4. Executes the `main action` associated with the transition, awaiting it if it is asynchronous.
            5. Executes the `on-enter` hooks for the next state, awaiting any that are asynchronous.
            6. Executes the `after-transition` hooks, awaiting any that are asynchronous.
            7. Returns the next state after the transition.
        
        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # Assuming a transition from INITIAL state on START event is defined as follows:
            >>> sm.add_transition(
            ...     from_state=MyState.INITIAL,
            ...     event=MyEvent.START,
            ...     to_state=MyState.STARTED,
            ...     func=start_action_async, # this action is asynchronous
            ...     guard=always_true
            ... )
            >>> # Then, dispatching the START event from INITIAL state with a context would execute the
            >>> # transition, awaiting the asynchronous action and hooks as needed, and return the next state:
            >>> await sm.dispatch_async(context, MyState.INITIAL, MyEvent.START)
            MyState.STARTED
        
        Args:
            ctx (C): The context to pass to the guard, action, and hooks.
            state (S): The current state from which to transition.
            event (E): The event that triggers the transition.
        
        Returns:
            S: The next state after the transition.

        Raises:
            InvalidTransitionError: If no transition is defined for the given state and event.
            GuardRejectedError: If the guard condition for the transition is not satisfied.
        """

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

    def session(self, ctx: C, initial_state: S) -> StateMachineInstance[S, E, C]:
        """
        *"Performs a long-running session with the state machine."*

        Creates a `StateMachineInstance` that maintains the current state and context for a long-running session and enables some extras utilities from `Reactive[C]`.

        So, ideally you would use this when you haven't a custom class to hold the context and the current state together, and you want to have some utilities to react to state changes and events without having to manage the current state yourself.

        Example:
            >>> sm = StateMachine[MyState, MyEvent, MyContext]()
            >>>
            >>> # Define transitions and hooks for the state machine...
            >>>
            >>> # Then, create a session with an initial context and state:
            >>> session = sm.session(ctx=MyContext(...), initial_state=MyState.INITIAL)
            >>> # Now you can use session.dispatch() and session.dispatch_async() or 'sm >> Event' syntax to handle events, and session.current_state to access the current state.

        Args:
            ctx (C): The initial context for the session.
            initial_state (S): The initial state for the session.

        Returns:
            StateMachineInstance[S, E, C]: An instance of `StateMachineInstance` that maintains the current state and context for a long-running session and provides utilities for reacting to state changes and events.

        Raises:
            Anything: Raises the same exceptions as `dispatch` and `dispatch_async` if event handling fails during the session.
        """
        return StateMachineInstance(self, ctx, initial_state)
