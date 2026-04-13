
class InvalidTransition(Exception):
    pass

class InvalidState(Exception):
    pass

class InvalidEvent(Exception):
    pass


class TransitionBlocked(Exception):
    pass

class GuardRejected(TransitionBlocked):
    pass


class TransitionRewriteAttempt(Exception):
    pass


class InvalidTransitionFormat(Exception):
    pass
