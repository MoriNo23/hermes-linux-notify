# pydbus introspection XML — common mistakes

pydbus derives the exported D-Bus interface entirely from the class
docstring, parsed as D-Bus Introspection XML. There is no decorator-based
alternative in pydbus (unlike dbus-next/dbus-fast).

## Checklist when a client can't find a method or gets a marshalling error

1. **`direction` on every `<arg>`** — must be `in` or `out`, and must match
   the actual Python method's parameter/return position. A missing or wrong
   `direction` attribute is the most common cause of "method not found"-style
   errors that are actually XML mismatches, not missing methods.
2. **Argument order matches the Python method signature order** — the XML
   doesn't use argument names to bind, it uses position.
3. **`type` uses D-Bus signature characters**, not Python types: `s` for
   string, `i`/`u` for int32/uint32, `b` for bool, `a{sv}` for a dict of
   variants, `ay` for a byte array. A Python-shaped type name here (e.g.
   `str`) silently fails introspection rather than raising at class
   definition time.
4. **Multiple interfaces on one object** need multiple `<interface>` blocks
   under a single `<node>` root — a common mistake is nesting a second
   `<node>` instead, which pydbus does not merge as expected.
5. **Properties** need explicit `<property name="..." type="..." access="read|write|readwrite"/>`
   tags — a plain Python `@property` with no corresponding XML entry is
   invisible over D-Bus, which surprises people expecting decorator-style
   auto-export like dbus-next/dbus-fast provide.

## Minimal template to copy from

```xml
<node>
  <interface name='com.example.Demo'>
    <method name='Echo'>
      <arg type='s' name='what' direction='in'/>
      <arg type='s' name='response' direction='out'/>
    </method>
    <property name='Count' type='i' access='read'/>
    <signal name='Changed'>
      <arg type='i' name='new_value'/>
    </signal>
  </interface>
</node>
```

Signals declared here are triggered from Python via a matching method with
the `@signal` behavior — but note pydbus's mechanism differs release to
release in how signals are emitted from within a published object; when in
doubt, prefer `dbus-fast`'s explicit `@signal()` decorator style, which
gives a compile-time-visible declaration instead of a string-parsed one.
