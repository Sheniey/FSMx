
class FSMXException(Exception):
    """
    Base exception for all FSMX-related errors.

    All custom FSM exceptions should inherit from this class so users
    can catch every library-specific error with:

        except FSMXException:
            ...
    """
    pass

class InvalidTransitionError(FSMXException):
    """
    Raised when a transition is requested but no valid transition
    is defined for the given state and event.

    Example:
        Current state: `RUNNING`
        Event: `STOP`

        If no transition exists for (`RUNNING`, `STOP`), then
        this exception is raised.
    """
    pass


class InvalidStateError(FSMXException):
    """
    Raised when an invalid, unknown, or unsupported state is used.

    This usually happens when:
    - a state is not registered in the state machine
    - a transition returns an invalid state
    - the current state becomes inconsistent
    """
    pass


class InvalidEventError(FSMXException):
    """
    Raised when an event is invalid or cannot be handled.

    This may happen when:
    - the event is not part of the expected Enum
    - no handler exists for the event
    - the event type is unsupported

    Example:
        >>> sm.handle("invalid_event")
        InvalidEventError: Event 'invalid_event' is not valid for this state machine.
    """
    pass


class TransitionBlockedError(FSMXException):
    """
    Raised when a transition is intentionally blocked and
    cannot continue.

    This is commonly caused by:
    - guard conditions
    - before_transition hooks
    - validation rules
    """
    pass


class GuardRejectedError(TransitionBlockedError):
    """
    Raised when a guard condition explicitly rejects
    a transition.

    This is a more specific form of TransitionBlockedError
    used when the rejection comes directly from a guard.

    Example:
        def always_false(context):
            return False  # Guard condition fails

        TransitionModel(
            from_state=State.A,
            event=Event.X,
            to_state=State.B,
            func=action,
            guard=always_false
        )

        When Event.X is handled in State.A, this guard will reject the transition,
        resulting in a GuardRejectedError.
    """
    pass


class TransitionRewriteError(FSMXException):
    """
    Raised when a transition attempts to mutate or overwrite
    the current state directly instead of returning a new state.

    Transitions should return the next state rather than
    modifying the current one in-place.

    Example:
        >>> def invalid_transition(context):
        ...     context.state = State.B  # Invalid: directly mutating state
        ...     return context.state
        ...
        >>> TransitionModel(
        ...     from_state=State.A,
        ...     event=Event.X,
        ...     to_state=State.B,
        ...     func=invalid_transition,
        ...     guard=None
        ... )
        When Event.X is handled in State.A, this will raise a TransitionRewriteError
        because the transition function is directly mutating the state instead of returning a new state.
    """
    pass


class InvalidTransitionFormatError(FSMXException):
    """
    Raised when a transition definition provided through the
    '+' operator does not match the expected format.

    Example:
        >>> sm + "invalid transition"

        Instead of the expected structured transition definition of `sm_types.TransitionModel`.
    """
    pass