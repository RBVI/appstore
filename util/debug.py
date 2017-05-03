def wrap_traceback(func):
    "Decorator for catching tracebacks."

    def wf(*args, **kw):
        with open("/tmp/cxtoolshed.tb", "a") as f:
            try:
                v = func(*args, **kw)
            except:
                import traceback
                traceback.print_exc(file=f)
                raise
            else:
                return v
    return wf
