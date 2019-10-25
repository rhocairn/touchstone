# Touchstone Changelog

## 1.0.0
* Release of v1! No major changes to the functionality.
**Bug Fixes**
* `celery` no longer required on all installs. Install with the `django_celery` extras instead.

**Improvements**
* Added python 3.8 support
* Added `isort` and `black` for code formatting

## 0.5.0
**New Feature**
* Added `touchstone_task` which is a wrapper around Celery Tasks so that you can inject
properties via class variable annotations in Celery tasks.

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
