
<h1 align="center">Finite State Machine eXtended (FSMX)</h1>

[![PyPI version][fsmx.version.badge]][fsmx.project] 

[fsmx.project]: https://pypi.org/project/fsmx/
[fsmx.version.badge]: https://badge.fury.io/py/fsmx.svg

---

## Table of Contents

- [Description](#what-is-it)
- [Features](#features)
- [Installation](#how-to-start)
- [Dependencies](#dependencies)
- [Samples](#samples)
- [License](#license)

---

## What is it?

<p style="text-align: justify;"> 
<strong>FSMx</strong> is a Python library for building finite state machines with a focus on flexibility, extensibility, and ease of use. FSMX provides a simple and intuitive API for defining states, transitions, and actions, while also supporting advanced features like custom contexts, hooks, and visualization.
<p>

---

## Features

- [x] Async/Sync support.
- [x] Custom context support.
- [x] Event driven.
- [x] Flowchart visualization w/Graphviz.
- [x] FSM Private sessions API.
- [ ] Full documentation.
- [x] Hooks support.
- [ ] Multiple export formats.
- [x] Multiple visualization styles.
- [ ] < Python 3.14 support.
- [x] Scalable.
- [x] Type hints.

---

## How to start?

> Makes sure you have `Python 3.14` or higher installed.

```bash
# PyPi
pip install fsmx
```

[( See quickstart >> )](#samples)

---

## Dependencies

- [`rich`][rich.project] - for pretty printing and syntax highlighting.
- [`graphviz`][graphviz.project] *(optional)* - for visualization and export features.

[rich.project]: https://pypi.org/project/rich/
[graphviz.project]: https://pypi.org/project/graphviz/

---

## Samples

<details>
<summary>Quick Start</summary>

```python
print("Hello, World!")
```

</details>

<br>

<details>
<summary>Showcase</summary>

```python
from typing import Literal
from dataclasses import dataclass, field
from enum import Enum, auto
from rich.console import Console
from rich.syntax import Syntax
import datetime as dt

from fsmx import StateMachine
from fsmx.fsm_types import TransitionModel
from fsmx.core import StateMachineSession
from fsmx.exceptions import InvalidTransition

console: Console = Console()
ROSE_COLOR = "#ff80bf"
GREEN_COLOR = "#80ffb9"
BLUE_COLOR = "#93aaff"
FAIL_COLOR = "#ff9191"
SUCCESS_COLOR = "#80ff80"
ERROR_COLOR = "#ff4d4d"
WARNING_COLOR = "#ffb380"
INFO_COLOR = "#80b3ff"

# posible states
class PayState(Enum):
    NEW = auto()
    AUTHORIZED = auto()
    CAPTURED = auto()
    FAILED = auto()
    REFUNDED = auto()

# triggering events
class PayEvent(Enum):
    AUTHORIZE = auto()
    CAPTURE = auto()
    FAIL = auto()
    REFUND = auto()


@dataclass
class PaymentCtx:
    payment_id: str
    audit: list[str] = field(default_factory=list)


# ========== DEFINING THE STATE MACHINE ========== #
pay_sm: StateMachine[PayState, PayEvent, PaymentCtx] = StateMachine()
# ========== DEFINING THE STATE MACHINE ========== #



# ========== DEFINING HOOKS ========== #
@pay_sm.after_each_transition # this is a hook that will run after every transition
def log_transition(ctx: PaymentCtx) -> None:
    right_now: str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f" [{ROSE_COLOR}]\\[{ctx.payment_id}][/{ROSE_COLOR}] : [{SUCCESS_COLOR} bold]transition executed!![/{SUCCESS_COLOR} bold] [{INFO_COLOR} bold]<{right_now}>[/{INFO_COLOR} bold]")
# ========== DEFINING HOOKS ========== #


# ========== DEFINING TRANSITIONS ========== #
@pay_sm.transition(PayState.NEW, PayEvent.AUTHORIZE, PayState.AUTHORIZED)
def authorize(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"[{GREEN_COLOR}]{ctx.payment_id} has been authorized.[/{GREEN_COLOR}]")

@pay_sm.transition((PayState.NEW, PayState.AUTHORIZED), PayEvent.FAIL, PayState.FAILED)
def fail(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"[{FAIL_COLOR}]{ctx.payment_id} has failed.[/{FAIL_COLOR}]")

@pay_sm.transition(PayState.AUTHORIZED, PayEvent.CAPTURE, PayState.CAPTURED)
def capture(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"[{BLUE_COLOR}]{ctx.payment_id} has been captured.[/{BLUE_COLOR}]")

# you can also define a transition "manually" without using the decorator
def refund(ctx: PaymentCtx) -> None:
    ctx.audit.append(f"[{GREEN_COLOR}]{ctx.payment_id} has been refunded.[/{GREEN_COLOR}]") 
pay_sm.add_transition(
    from_state=(PayState.AUTHORIZED, PayState.CAPTURED),
    event=PayEvent.REFUND,
    to_state=PayState.REFUNDED,
    func=refund,
    guard=None
)
# ========== DEFINING TRANSITIONS ========== #

# ========== YOUR CUSTOM CLASS ========== #
@dataclass
class Payment(StateMachineSession[PayState, PayEvent, PaymentCtx]):
    ctx: PaymentCtx
    state: PayState = PayState.NEW

    def handle(self, event: PayEvent) -> None:
        self.state = pay_sm.dispatch(self.ctx, self.state, event)
# ========== YOUR CUSTOM CLASS ========== #

# ========== YOUR CUSTOM RENDERER FOR VISUALIZATION ========== #
# class HookRenderer(Renderer):
#     requires = "hooks"

#     def render(self, payload: StateMachinePayload) -> None:
#         hooks = payload.get("hooks", {})
#         for state, on_enter_hooks in hooks.get("on_enter", {}).items():
#             for hook in on_enter_hooks:
#                 print(f"State {state.name} has on_enter hook: {hook.__name__}()")
#         for state, on_exit_hooks in hooks.get("on_exit", {}).items():
#             for hook in on_exit_hooks:
#                 print(f"State {state.name} has on_exit hook: {hook.__name__}()")
#         for hook in hooks.get("before_each_transition", []):
#             print(f"Before each transition hook: {hook.__name__}()")
#         for hook in hooks.get("after_each_transition", []):
#             print(f"After each transition hook: {hook.__name__}()")
# ========== YOUR CUSTOM RENDERER FOR VISUALIZATION ========== #

def pretty_audit(audit: list[str], bleeding: int = 4) -> str:
    result: str = ""
    for entry in audit:
        result += f"{' ' * bleeding}- {entry}\n"
    return result

def pretty_payment_dump(payment: Payment) -> str:
    console.print(
        f'[{ROSE_COLOR}]\\[{payment.ctx.payment_id}][/{ROSE_COLOR}] [cyan]STATE:[/cyan] {payment.state}\n',
        f'[{ROSE_COLOR}]\\[{payment.ctx.payment_id}][/{ROSE_COLOR}] [cyan]AUDIT:[/cyan] \n{pretty_audit(payment.ctx.audit)}\n',
    )

def main() -> None:
    # ========== INSPECTING THE STATE MACHINE ========== #
    # repr(pay_sm) shows the total of transitions and hooks
    console.print(Syntax(f"pay_sm = {pay_sm!r}", "python", theme="one-dark"))
    console.print()
    # ========== INSPECTING THE STATE MACHINE ========== #

    # ========== A SUCCESSFUL PAYMENT PROCESS ========== #
    p1: Payment = Payment(ctx=PaymentCtx("p1"))
    # Payment()::handle(...) ==> .dispatch(...)
    # ** Your custom class method as explicit API. **
    p1.handle(PayEvent.AUTHORIZE)
    # StateMachineSession[...]::__rshift__(...) ==> .dispatch(...)
    # ** Your custom class must be inherited from StateMachineSession to use this sugar syntax. **
    p1 >> PayEvent.CAPTURE >> PayEvent.REFUND
    
    console.print(
        '\n',
        f'[{ROSE_COLOR}]\\[{p1.ctx.payment_id}][/{ROSE_COLOR}] [cyan bold]STATE: [/][cyan]{p1.state}[/cyan]\n',
        f'[{ROSE_COLOR}]\\[{p1.ctx.payment_id}][/{ROSE_COLOR}] [cyan]AUDIT:[/cyan] \n{pretty_audit(p1.ctx.audit)}\n',
        '\n\n'
    )
    # ========== A SUCCESSFUL PAYMENT PROCESS ========== #

    # ========== A FAILED PAYMENT PROCESS ========== #
    p2: StateMachineSession[PayState, PayEvent, PaymentCtx] = pay_sm.session(ctx=PaymentCtx("p2"), initial_state=PayState.NEW)
    p2 >> PayEvent.AUTHORIZE >> PayEvent.FAIL
    
    console.print(
        '\n',
        f'[{ROSE_COLOR}]\\[{p2.context.payment_id}][/{ROSE_COLOR}] [cyan]STATE: {p2.current_state}[/cyan]\n',
        f'[{ROSE_COLOR}]\\[{p2.context.payment_id}][/{ROSE_COLOR}] [cyan]AUDIT:[/cyan] \n{pretty_audit(p2.context.audit)}\n',
        '\n\n'
    )
    # ========== A FAILED PAYMENT PROCESS ========== #

    # ========== A PROTECTED PAYMENT PROCESS ========== #
    p3: Payment = Payment(ctx=PaymentCtx("p3"))
    try:
        p3.handle(PayEvent.CAPTURE) # invalid transition, a exception'll be raised
    except InvalidTransition as e:
        console.print(f"[red bold] [{ROSE_COLOR}]\\[{p3.ctx.payment_id}][/{ROSE_COLOR}] Tried to CAPTURE without being AUTHORIZED first!")
        console.print(f"[{WARNING_COLOR} bold]   \\-[*] Ignored just for demostration purposes, but you should handle it properly in a real application.[/{WARNING_COLOR} bold]")
    
    console.print(
        '\n',
        f'[{ROSE_COLOR}]\\[{p3.ctx.payment_id}][/{ROSE_COLOR}] [cyan]STATE: {p3.state}[/cyan]\n',
        f'[{ROSE_COLOR}]\\[{p3.ctx.payment_id}][/{ROSE_COLOR}] [cyan]AUDIT:[/cyan] {pretty_audit(p3.ctx.audit)}'
    )
    # ========== A PROTECTED PAYMENT PROCESS ========== #

    # ========== STATE MACHINE VISUALIZATION ========== #
    # pay_sm.visualize().custom(HookRenderer())
    # pay_sm.export().to_png("pay_sm.png") # makes a flowchart and saves it as a png file
    # ========== STATE MACHINE VISUALIZATION ========== #

if __name__ == "__main__":
    main()
```

</details>

---

## License

This project is licensed under the [MIT][mit.url] License.

<table style="padding-left: 2rem; padding-right: 2rem; margin-left: auto; margin-right: auto;">

<tr>  
<th>Action</th>
<th align="center">Permission</th>
</tr>

<tr>
<td>Commercial use</td>
<td align="center">✅</td>
</tr>
<tr>
<td>Modification</td>
<td align="center">✅</td>
</tr>
<tr>
<td>Distribution</td>
<td align="center">✅</td>
</tr>
<tr>
<td>Private use</td>
<td align="center">✅</td>
</tr>

</table>


[mit.url]: https://opensource.org/licenses/MIT

---
