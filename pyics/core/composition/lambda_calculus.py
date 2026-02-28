#!/usr/bin/env python3
"""
pyics/core/composition/lambda_calculus.py
Lambda Calculus Engine — Function Composition Primitives

PROBLEM SOLVED: Composable, pure function pipelines for DOP compliance.
DEPENDENCIES: functools (stdlib only)
CONTRACT: Lambda class provides identity, compose, pipe, partial, curry.

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — Lapis Lambda Calculus Foundation
"""

import functools
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, TypeVar, Protocol, runtime_checkable

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

# ---------------------------------------------------------------------------
# Core Lambda class (the public API)
# ---------------------------------------------------------------------------

class Lambda:
    """
    Lapis Lambda Calculus primitives for composable pure-function pipelines.

    All methods are pure functions — no state, no side effects.

    Composition semantics:
      - compose(f, g)(x)  ≡  f(g(x))   [right-to-left / mathematical order]
      - pipe(f, g)(x)     ≡  g(f(x))   [left-to-right / data-flow order]
    """

    @staticmethod
    def identity(x: A) -> A:
        """Identity function: returns its argument unchanged."""
        return x

    @staticmethod
    def compose(*fns: Callable) -> Callable:
        """
        Right-to-left function composition.

        Lambda.compose(f, g, h)(x)  ≡  f(g(h(x)))

        Follows mathematical function composition order.
        With zero functions returns identity; with one returns that function.
        """
        if not fns:
            return Lambda.identity
        if len(fns) == 1:
            return fns[0]
        return functools.reduce(
            lambda f, g: lambda x: f(g(x)),
            fns
        )

    @staticmethod
    def pipe(*fns: Callable) -> Callable:
        """
        Left-to-right function pipeline.

        Lambda.pipe(f, g, h)(x)  ≡  h(g(f(x)))

        Follows data-flow order — output of each step feeds the next.
        With zero functions returns identity; with one returns that function.
        """
        if not fns:
            return Lambda.identity
        if len(fns) == 1:
            return fns[0]
        return functools.reduce(
            lambda f, g: lambda x: g(f(x)),
            fns
        )

    @staticmethod
    def partial(fn: Callable, *args: Any, **kwargs: Any) -> Callable:
        """Partial application — fixes leading arguments."""
        return functools.partial(fn, *args, **kwargs)

    @staticmethod
    def curry(fn: Callable) -> Callable:
        """
        Auto-curry a function up to its declared arity.

        Returns a curried version that collects arguments one at a time
        until the full signature is satisfied, then calls the original.
        """
        arity = fn.__code__.co_argcount if hasattr(fn, '__code__') else 1

        def curried(*args: Any) -> Any:
            if len(args) >= arity:
                return fn(*args[:arity])
            return lambda *more: curried(*(args + more))

        return curried

    @staticmethod
    def flip(fn: Callable) -> Callable:
        """Flip the first two arguments of a two-argument function."""
        return lambda a, b: fn(b, a)

    @staticmethod
    def constant(value: A) -> Callable[..., A]:
        """Returns a function that always returns *value*, ignoring its argument."""
        return lambda _: value

    @staticmethod
    def memoize(fn: Callable) -> Callable:
        """Pure memoization — caches results for immutable inputs."""
        return functools.lru_cache(maxsize=None)(fn)


# ---------------------------------------------------------------------------
# ABC contract wrappers (retained for domain coordinator compatibility)
# ---------------------------------------------------------------------------

@runtime_checkable
class LambdaCalculusProtocol(Protocol):
    """Protocol for lambda calculus composition engines."""

    def compose_functions(self, *fns: Callable) -> Callable: ...
    def pipe_functions(self, *fns: Callable) -> Callable: ...


class LambdaCalculusBase(ABC):
    """Abstract base for lambda calculus composition engines."""

    @abstractmethod
    def compose_functions(self, *fns: Callable) -> Callable:
        """Compose functions right-to-left."""
        ...

    @abstractmethod
    def pipe_functions(self, *fns: Callable) -> Callable:
        """Compose functions left-to-right."""
        ...


class LambdaCalculusImplementation(LambdaCalculusBase):
    """Concrete implementation delegating to the Lambda class."""

    def compose_functions(self, *fns: Callable) -> Callable:
        return Lambda.compose(*fns)

    def pipe_functions(self, *fns: Callable) -> Callable:
        return Lambda.pipe(*fns)


# ---------------------------------------------------------------------------
# Module metadata (single-pass cost accounting)
# ---------------------------------------------------------------------------

__module_metadata__ = {
    "name": "lambda_calculus",
    "domain": "composition",
    "problem_classification": "Pure function composition primitives",
    "dependencies": [],
    "contracts": ["LambdaCalculusProtocol", "LambdaCalculusBase"],
    "thread_safe": True,
    "cost_weight": 0.05,
}


def get_module_exports() -> Dict[str, Any]:
    """Export module contracts and implementations for domain registration."""
    return {
        'Lambda': Lambda,
        'LambdaCalculusProtocol': LambdaCalculusProtocol,
        'LambdaCalculusBase': LambdaCalculusBase,
        'LambdaCalculusImplementation': LambdaCalculusImplementation,
        'get_module_metadata': lambda: __module_metadata__.copy(),
    }


def initialize_module() -> bool:
    """Validate module follows ABC contract structure on load."""
    try:
        impl = LambdaCalculusImplementation()
        f = impl.compose_functions(lambda x: x + 1, lambda x: x * 2)
        assert f(3) == 7  # (3 * 2) + 1
        g = impl.pipe_functions(lambda x: x + 1, lambda x: x * 2)
        assert g(3) == 8  # (3 + 1) * 2
        return True
    except Exception:
        return False


__all__ = [
    'Lambda',
    'LambdaCalculusProtocol',
    'LambdaCalculusBase',
    'LambdaCalculusImplementation',
    'get_module_exports',
    'initialize_module',
]

if not initialize_module():
    raise RuntimeError("Failed to initialize module: lambda_calculus.py")

# [EOF] - End of lambda_calculus.py
