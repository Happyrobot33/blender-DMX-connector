import bpy
from enum import Enum

from bpy.app.handlers import persistent

__all__ = ("Task", "HandlerType")


_handler_names = [
    "depsgraph_update_pre",
    "depsgraph_update_post",
    "frame_change_pre",
    "frame_change_post",
    "load_factory_preferences_pre",
    "load_factory_preferences_post",
    "load_pre",
    "load_post",
    "redo_pre",
    "redo_post",
    "render_cancel",
    "render_complete",
    "render_init",
    "render_pre",
    "render_post",
    "render_stats",
    "render_write",
    "save_pre",
    "save_post",
    "undo_pre",
    "version_update",
]


class HandlerType(Enum):
    """Enum for Blender event handler types"""
    DEPSGRAPH_UPDATE_PRE = "depsgraph_update_pre"
    DEPSGRAPH_UPDATE_POST = "depsgraph_update_post"
    FRAME_CHANGE_PRE = "frame_change_pre"
    FRAME_CHANGE_POST = "frame_change_post"
    LOAD_FACTORY_PREFERENCES_PRE = "load_factory_preferences_pre"
    LOAD_FACTORY_PREFERENCES_POST = "load_factory_preferences_post"
    LOAD_PRE = "load_pre"
    LOAD_POST = "load_post"
    REDO_PRE = "redo_pre"
    REDO_POST = "redo_post"
    RENDER_CANCEL = "render_cancel"
    RENDER_COMPLETE = "render_complete"
    RENDER_INIT = "render_init"
    RENDER_PRE = "render_pre"
    RENDER_POST = "render_post"
    RENDER_STATS = "render_stats"
    RENDER_WRITE = "render_write"
    SAVE_PRE = "save_pre"
    SAVE_POST = "save_post"
    UNDO_PRE = "undo_pre"
    VERSION_UPDATE = "version_update"


class Task:
    functions = {}

    def register(cls):
        cls._registered_handlers = []

        for name in _handler_names:
            funcs = cls.functions.get(name)
            
            # Also try with enum values
            if funcs is None:
                for handler in HandlerType:
                    if handler.value == name:
                        funcs = cls.functions.get(handler)
                        break
            
            if not hasattr(funcs, "__iter__"):
                funcs = [funcs]

            for func in funcs:
                if callable(func):
                    func = persistent(func)
                    getattr(bpy.app.handlers, name).append(func)
                    cls._registered_handlers.append((name, func))

    def unregister(cls):
        for name, func in reversed(cls._registered_handlers):
            getattr(bpy.app.handlers, name).remove(func)

        del cls._registered_handlers
    
    def enforce_run_last(cls, handler_name):
        """Move the specified handler to the end of the list to ensure it runs last"""
        handlers = getattr(bpy.app.handlers, handler_name)
        if cls._registered_handlers:
            #print(f"Enforcing {handler_name} handlers to run last for {cls}")
            for name, func in cls._registered_handlers:
                func = persistent(func)
                if func in handlers:
                    handlers.remove(func)
                    handlers.append(func)
                    #print(f"Moved {func} to end of {handler_name} handlers")
