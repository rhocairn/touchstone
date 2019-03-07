# Touchstone

Touchstone is an annotations-driven Inversion of Control container for
Python 3.6 and above.

[GitHub](https://github.com/gmaybrun/touchstone)


## Learn by Example

### Auto Wiring

```python
from touchstone import Container

class Child:
    pass

class Parent:
    def __init__(self, child: Child) -> None:
        self.child = child


container = Container()
parent = container.make(Parent)

assert isinstance(parent.child, Child)
```


### Interface Binding

```python
from touchstone import Container

class AbstractChild:
    pass

class Child(AbstractChild):
    pass

class Parent:
    def __init__(self, child: AbstractChild) -> None:
        self.child = child


container = Container()
container.bind(AbstractChild, Child)
parent = container.make(Parent)

assert isinstance(parent.child, Child)
```


### Binding with Factory Methods

```python
from touchstone import Container

class Child:
    def __init__(self, name: str) -> None:
        self.name = name

class Parent:
    def __init__(self, child: Child) -> None:
        self.child = child


container = Container()
container.bind(Child, lambda: Child('them'))
parent = container.make(Parent)

assert isinstance(parent.child, Child)
assert parent.child.name == 'them'
```


### Binding Singletons

```python
from touchstone import Container, SINGLETON

class Child:
    def __init__(self, name: str) -> None:
        self.name = name

class Parent:
    def __init__(self, child: Child) -> None:
        self.child = child


container = Container()
them_child = Child('them')
container.bind_instance(Child, them_child)
# Or...
container.bind(Child, lambda: them_child, lifetime_strategy=SINGLETON)
parent = container.make(Parent)

assert isinstance(parent.child, Child)
assert parent.child is them_child
```


### Contextual Binding

```python
from touchstone import Container

class Child:
    def __init__(self, name: str) -> None:
        self.name = name

class Parent:
    def __init__(self, child1: Child, child2: Child) -> None:
        self.child1 = child1
        self.child2 = child2


container = Container()
container.bind_contextual(when=Parent, wants=Child, called='child1', give=lambda: Child('her'))
container.bind_contextual(when=Parent, wants=Child, called='child2', give=lambda: Child('him'))
parent = container.make(Parent)

assert isinstance(parent.child1, Child)
assert isinstance(parent.child2, Child)
assert parent.child1.name == 'her'
assert parent.child2.name == 'him'
```
