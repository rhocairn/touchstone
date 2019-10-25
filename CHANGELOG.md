# Touchstone Changelog

## 0.4.1
**Bug Fix**
* `MagicInjectedProperties` uses Django's `cached_property` which [changed](https://github.com/django/django/commit/06076999026091cf007d8ea69146340a361259f8#diff-31c53995d28395e13d586859808522f6) 
its behavior in version 3 so that we need to call `__set_name__` manually after adding a cached property dynamically. 

## 0.4.0
**Breaking Changes**
* Renamed the `called` argument of the `bind_contextual` methods to `wants_name`
  for clarity in the following situation:
  ```python
  class Thing:
      def __init__(self, obj):
        pass

  # Old API
  container.bind_contextual(when=Thing, called='obj', give=MyCls)

  # New API which makes more intuitive sense
  container.bind_contextual(when=Thing, wants_name='obj', give=MyCls)
  ```

## 0.3.0
**New Features**
* Added support for injecting attributes into Django class-based views and mixins.
