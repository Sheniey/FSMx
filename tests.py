
from enum import Enum, auto
from dataclasses import dataclass, field

from fsmx.core import StateMachine, StateMachineSession
from fsmx.fsm_types import TransitionModel

class PayState(Enum):
    NEW = auto()
    AUTHORIZED = auto()
    CAPTURED = auto()
    FAILED = auto()
    REFUNDED = auto()


class PayEvent(Enum):
    AUTHORIZE = auto()
    CAPTURE = auto()
    FAIL = auto()
    REFUND = auto()


@dataclass
class PaymentCtx:
    payment_id: str
    audit: list[str] = field(default_factory=list)


# Create an instance: this is "the machine"
pay_sm: StateMachine[PayState, PayEvent, PaymentCtx] = StateMachine()

@pay_sm.after_each_transition
def log_transition(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"{ctx.payment_id}: transition complete")

# using decotated method
@pay_sm.transition(PayState.NEW, PayEvent.AUTHORIZE, PayState.AUTHORIZED)
def authorize(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"{ctx.payment_id}: authorized")


def fail(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"{ctx.payment_id}: failed")
# using __add__ method with a TransitionModel dict
pay_sm + TransitionModel(
    from_state=(PayState.NEW, PayState.AUTHORIZED),
    event=PayEvent.FAIL,
    to_state=PayState.FAILED,
    func=fail,
    guard=None
)


def capture(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"{ctx.payment_id}: captured")
# using __add__ method with a simple dict
pay_sm + {
    'from_state': PayState.AUTHORIZED,
    'event': PayEvent.CAPTURE,
    'to_state': PayState.CAPTURED,
    'func': capture,
    'guard': None
}


def refund(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"{ctx.payment_id}: refunded")
# using manual method 
pay_sm.add_transition(
    from_state=(PayState.AUTHORIZED, PayState.CAPTURED),
    event=PayEvent.REFUND,
    to_state=PayState.REFUNDED,
    func=refund,
    guard=None
)

@dataclass
class Payment:
    ctx: PaymentCtx
    state: PayState = PayState.NEW

    def handle(self, event: PayEvent) -> None:
        self.state = pay_sm.dispatch(self.ctx, self.state, event)


def main():
    p1: Payment = Payment(ctx=PaymentCtx("p1"))
    print(pay_sm)

    p1.handle(PayEvent.AUTHORIZE)
    p1.handle(PayEvent.CAPTURE)
    p1.handle(PayEvent.REFUND)

    print("state:", p1.state)
    print("audit:", p1.ctx.audit)

    # p2: StateMachineSession[PayState, PayEvent, PaymentCtx] = pay_sm.session(ctx=PaymentCtx("p2"), initial_state=PayState.NEW)
    # p2 >> PayEvent.AUTHORIZE >> PayEvent.REFUND
    # print(f'{p2!r}')

if __name__ == "__main__":
    main()