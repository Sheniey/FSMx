<a name="readme-top"></a>

<h1 align="center">Finite State Machine eXtended (FSMX)</h1>

<div align="center">

![Contributors][contributors.shield]
![Forks][forks.shield]
![Stargazers][stars.shield]
![Issues][issues.shield]

![PyPI - Version][fsmx.shield]
![GitHub License][license.shield]

</div>

[contributors.shield]: https://img.shields.io/github/contributors/sheniey/fsmx.svg?style=for-the-badge&logo=github&logoColor=eaeaea&label=Contributors&link=https%3A%2F%2Fgithub.com%2Fsheniey%2Ffsmx%2Fgraphs%2Fcontributors
[forks.shield]: https://img.shields.io/github/forks/sheniey/fsmx?style=for-the-badge&logo=github&logoColor=eaeaea&label=Forks&link=https%3A%2F%2Fgithub.com%2Fsheniey%2Ffsmx%2Fnetwork%2Fmembers
[stars.shield]: https://img.shields.io/github/stars/sheniey/fsmx?style=for-the-badge&logo=github&logoColor=eaeaea&label=Stars&link=https%3A%2F%2Fgithub.com%2Fsheniey%2Ffsmx%2Fstargazers
[issues.shield]: https://img.shields.io/github/issues/sheniey/fsmx?style=for-the-badge&logo=github&logoColor=eaeaea&label=Issues&link=https%3A%2F%2Fgithub.com%2Fsheniey%2Ffsmx%2Fissues
[fsmx.shield]: https://img.shields.io/pypi/v/fsmx?pypiBaseUrl=https%3A%2F%2Fpypi.org&logo=Python&logoColor=eaeaea&label=PyPi%20-%20Version&link=https%3A%2F%2Fpypi.org%2Fproject%2Ffsmx%2F
[license.shield]: https://img.shields.io/github/license/sheniey/fsmx?style=flat&logo=wikiversity&logoColor=eaeaea&label=License&link=https%3A%2F%2Fchoosealicense.com%2Flicenses%2Fmit%2F

<a name="content-table"></a>

<br>
<br>
<br>

---

## Table of Contents

- <a href="#description" title="Description">Description</a>
- <a href="#features" title="Features">Features</a>
- <a href="#installation" title="Installation">Installation</a>
- <a href="#dependencies" title="Dependencies">Dependencies</a>
- <a href="#samples" title="Samples">Samples</a>
- <a href="#faqs" title="Frequently Asked Questions">FAQs</a>
- <a href="#license" title="License">License</a>

<a name="description"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## What is it?

<p style="text-align: justify;"> 
<strong>FSMx</strong> is a Python library for building finite state machines with a focus on flexibility, extensibility, and ease of use. FSMX provides a simple and intuitive API for defining states, transitions, and actions, while also supporting advanced features like custom contexts, hooks, and visualization.
<p>

<a name="features"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## Features

- [x] Async/Sync support.
- [x] Custom context support.
- [x] Event driven.
- [ ] Flowchart visualization w/Graphviz.
- [x] FSM Private sessions API.
- [ ] Full documentation.
- [x] Hooks support.
- [ ] Multiple export formats.
- [ ] Multiple visualization styles.
- [ ] < Python 3.14 support.
- [x] Scalable.
- [x] Type hints.

<a name="installation"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## Installation

> [!IMPORTANT]
> Makes sure you have `Python 3.14` or higher installed; otherwise, you will not be able to use this library.

```bash
# PyPi
pip install fsmx
```

[( See quickstart >> )](#samples)

<a name="dependencies"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## Dependencies

- [`rich`][rich.project] - for pretty printing and syntax highlighting.
- [`graphviz`][graphviz.project] *(optional)* - for visualization and export features.

[rich.project]: https://pypi.org/project/rich/
[graphviz.project]: https://pypi.org/project/graphviz/

<a name="samples"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## Samples

<details>
<summary>Quick Start</summary>

```python
from enum import Enum, auto
from dataclasses import dataclass, field
from fsmx import StateMachine, GuardRejected # <-- This Library
import random

GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

class PokemonState(Enum):
    IDLE = auto()
    SLEEPING = auto()
    EATING = auto()
    PLAYING = auto()
    TRAINING = auto()

class PokemonEvent(Enum):
    REST = auto()
    WAKE_UP = auto()
    GO_TO_SLEEP = auto()
    EAT = auto()
    PLAY = auto()
    TRAIN = auto()

@dataclass
class PokemonContext:
    name: str
    
    energy: int
    happiness: int
    strength: int

    log: list[str] = field(default_factory=list)

poke_sm: StateMachine[PokemonState, PokemonEvent, PokemonContext] = StateMachine()

@poke_sm.transition(PokemonState.SLEEPING, PokemonEvent.WAKE_UP, PokemonState.IDLE)
def wake_up(ctx: PokemonContext) -> None:
    energy_increase = random.randint(30, 45)
    ctx.energy = min(100, ctx.energy + energy_increase)
    ctx.log.append(
        f"{ctx.name} woke up!\n"
        f"{GREEN}  ↑ +{energy_increase}% Energy {RESET}"
    )

@poke_sm.transition(PokemonState.IDLE, PokemonEvent.GO_TO_SLEEP, PokemonState.SLEEPING)
def go_to_sleep(ctx: PokemonContext) -> None:
    ctx.log.append(
        f"{ctx.name} went to sleep!\n"
        f"{CYAN}  zZz... {RESET}"
    )

@poke_sm.transition(PokemonState.IDLE, PokemonEvent.EAT, PokemonState.EATING)
def eat(ctx: PokemonContext) -> None:
    energy_increase = random.randint(10, 30)
    happiness_increase = random.randint(0, 10)

    ctx.energy = min(100, ctx.energy + energy_increase)
    ctx.happiness = min(100, ctx.happiness + happiness_increase)

    ctx.log.append(
        f"{ctx.name} is eating!\n"
        f"{GREEN}  ↑ +{energy_increase}% Energy {RESET}\n"
        f"{GREEN}  ↑ +{happiness_increase}% Happiness {RESET}"
    )

@poke_sm.transition(
    from_state=PokemonState.IDLE,
    event=PokemonEvent.PLAY,
    to_state=PokemonState.PLAYING,
    guard=lambda ctx: ctx.energy >= 15
)
def play(ctx: PokemonContext) -> None:
    happiness_increase = random.randint(15, 25)
    energy_decrease = random.randint(10, 15)

    ctx.happiness = min(100, ctx.happiness + happiness_increase)
    ctx.energy = max(0, ctx.energy - energy_decrease)

    ctx.log.append(
        f"{ctx.name} is playing!\n"
        f"{GREEN}  ↑ +{happiness_increase}% Happiness {RESET}\n"
        f"{RED}  ↓ -{energy_decrease}% Energy {RESET}"
    )

@poke_sm.transition(
    from_state=PokemonState.IDLE,
    event=PokemonEvent.TRAIN,
    to_state=PokemonState.TRAINING,
    guard=lambda ctx: ctx.energy >= 35 and ctx.happiness >= 10
)
def train(ctx: PokemonContext) -> None:
    strength_increase = random.randint(15, 30)
    energy_decrease = random.randint(25, 35)
    happiness_decrease = random.randint(2, 10)

    ctx.strength += strength_increase
    ctx.energy = max(0, ctx.energy - energy_decrease)
    ctx.happiness = max(0, ctx.happiness - happiness_decrease)

    ctx.log.append(
        f"{ctx.name} is training!\n"
        f"{GREEN}  ↑ +{strength_increase} Strength {RESET}\n"
        f"{RED}  ↓ -{energy_decrease}% Energy {RESET}\n"
        f"{RED}  ↓ -{happiness_decrease}% Happiness {RESET}"
    )

@poke_sm.transition(
    from_state=(PokemonState.EATING, PokemonState.PLAYING, PokemonState.TRAINING),
    event=PokemonEvent.REST,
    to_state=PokemonState.IDLE
)
def rest(ctx: PokemonContext) -> None:
    energy_increase = random.randint(0, 5)
    ctx.energy = min(100, ctx.energy + energy_increase)
    ctx.log.append(
        f"{ctx.name} is resting!\n"
        f"{GREEN}  ↑ +{energy_increase}% Energy {RESET}"
        if energy_increase > 0 else
        f"{ctx.name} is resting!\n"
        f"{CYAN}  No energy recovered. {RESET}"
    )

def main() -> None:
    pikachu_ctx = PokemonContext(name="Pikachu", energy=60, happiness=70, strength=40) # balanced stats, a bit more energetic and happy than strong
    scorbunny_ctx = PokemonContext(name="Scorbunny", energy=100, happiness=90, strength=20) # energetic and happy, but not very strong
    snorlax_ctx = PokemonContext(name="Snorlax", energy=20, happiness=50, strength=120) # overweight and sleepy, but strong!

    pokemon = poke_sm.session(random.choice([
        pikachu_ctx,
        scorbunny_ctx,
        snorlax_ctx
    ]), PokemonState.IDLE)

    try:
        pokemon \
            >> PokemonEvent.PLAY  >> PokemonEvent.REST \
            >> PokemonEvent.TRAIN >> PokemonEvent.REST \
            >> PokemonEvent.EAT   >> PokemonEvent.REST \
            >> PokemonEvent.TRAIN >> PokemonEvent.REST
        pokemon \
            >> PokemonEvent.GO_TO_SLEEP \
            >> PokemonEvent.WAKE_UP
    except GuardRejected as e:
        # This may happen when TRAIN is blocked by guard conditions.
        # ---------------------------------------------
        # Remove random.choice() and use:
        # SNORLAX to trigger it more often,
        # SCORBUNNY to almost never see it,
        # and PIKACHU for the most balanced behavior.
        pokemon.context.log.append(f"Oh no! {pokemon.context.name} couldn't perform the action: {e}")

    print(f"\n{pokemon.context.name}'s Activity Log:")
    for log_entry in pokemon.context.log:
        print(log_entry)

    print(f"\n{pokemon.context.name}'s Final Stats:")
    print(f"  - State: {pokemon.current_state.name}")
    print(f"  - Energy: {pokemon.context.energy}%")
    print(f"  - Happiness: {pokemon.context.happiness}%")
    print(f"  - Strength: {pokemon.context.strength}\n")

if __name__ == "__main__":
    main()
```

</details>

<br>

<details>
<summary>Showcase</summary>

```python
from typing import Literal
from dataclasses import dataclass, field
from enum import Enum, auto
from fsmx import StateMachine, InvalidTransition, Reactive # <-- This Library
from rich.console import Console
from rich.syntax import Syntax
import datetime as dt

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

<a name="faqs"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## Why I cannot use this library in Python 3.13 or lower?

You cannot use this library because it uses some of the new features and syntax introduced in Python 3.14, such as the `Self` type hint, which is not available in earlier versions. If you try to run this library in Python 3.13 or lower, you will encounter syntax errors or import errors due to the missing features.

<br>

<div align="center"> === <strong>Python 3.13</strong> === </div>

```python
from typing import Self

class MyClass:
    def my_method(self) -> Self:
        return self

    def another_method(self) -> "MyClass":
        return self
```

<br>

<div align="center"> === <strong>Python 3.14</strong> === </div>

```python
class MyClass:
    def my_method(self) -> MyClass:
        return self
```

Also you can use the `from __future__ import annotations` statement to enable postponed evaluation of type annotations, which allows you to use the `Self` type hint in Python 3.13 or lower. However, this is not recommended as it may cause compatibility issues and is not a long-term solution.

<a name="license"></a>

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---

## License

This project is licensed under the [*Massachusetts Institute of Technology* (MIT)][mit.url] License.

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

<p align="right">
    (<a href="#readme-top">Go Back</a>)
</p>

---
