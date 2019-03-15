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
container.bind_contextual(when=Parent, wants=Child, wants_name='child1', give=lambda: Child('her'))
container.bind_contextual(when=Parent, wants=Child, wants_name='child2', give=lambda: Child('him'))
parent = container.make(Parent)

assert isinstance(parent.child1, Child)
assert isinstance(parent.child2, Child)
assert parent.child1.name == 'her'
assert parent.child2.name == 'him'
```


## Django Support

Now featuring Django support! New in v0.3.0

1) Configure your instance of `touchstone.Container` however you see fit.
2) In your main `settings.py`, set `TOUCHSTONE_CONTAINER_GETTER` to
   the path to a callable that will return the instace of
   `touchstone.Container` your app uses.

To get injected properties in your class-based views:
1) In your main `settings.py`, add `touchstone.django.InjectViewsMiddleware`
   to your `MIDDLEWARE` list.
2) Use class annotations on your class-based views. Cached Properties will
   be added to your view classes so that they automatically resolve using
   your configured touchstone container. For example:

```python
class MyView(View):
    something: MyObject
    def get(self, request):
        # You can now access self.something!
```

To get injected properties in your middleware, you'll need to do a little
more work because we haven't found a good way to hook into Django's middleware
instantiation logic.
```
from touchstone.django import get_container, MagicInjectedProperties
magic = MagicInjectedProperties(get_container())

@magic.set_magic_properties
class MyMixin:
    something: MyObject
    # define your mixin here...
    # You'll be able to use `self.something` from within every instace method.
```
