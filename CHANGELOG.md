# Touchstone Changelog

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
