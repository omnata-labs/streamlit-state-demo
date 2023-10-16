"""
Widgets!
"""
from __future__ import annotations
from abc import ABC
from typing import List, Literal, Optional, Set
import inspect
import os
from typing import Callable, Dict, TypeVar
import streamlit as st

T = TypeVar("T")
_PERSIST_STATE_KEY = f"{__name__}_PERSIST"

used_key_prefixes:Set[str] = set()

class WidgetBase(ABC):
    """
    A base class for widgets, which are ways of isolating a set of streamlit components with their
    own session state partition, and separating state management from rendering.
    This allows, for example, an action within a component to cause the parent to not render it.
    If this is done correctly, no widget will ever have its session state read from the outside via st.session_state.
    In a handler method, you only need to worry about writing the session state. Due to the order of streamlit execution,
    the constructor will take care of updating the instance variable from the session state.

    The rules for Widgets are:
    - Deal with session state read/write inside __init__, and within handler functions
    - Within __init__, populate the instance with the relevant objects. Ensure they are their proper types (e.g pydantic class, regardless of how they are stored in session state)
    - Within the render method, use the instance variables already populated instead of reading session state
    - Consumers of the class can instantiate it and read the instance variables separately to rendering it
    - Widgets should survive instantiation in any state, so that its consumers can choose to use it as early as they need.

    """
    @classmethod
    def prepare(cls):
        """
        This class method should be ran by the main streamlit script on each execution.
        It clears the state of which key prefixes have been used, so that they each end up with the same key prefixes each time.
        """
        used_key_prefixes.clear()
        # we have to rewrite all the session state entries to prevent them being deleted if its field isn't rendered
        if _PERSIST_STATE_KEY in st.session_state:
            st.session_state.update({
                key: value
                for key, value in st.session_state.items()
                if key in st.session_state[_PERSIST_STATE_KEY]
            })

    def __init__(self, named_instance: Optional[str] = None):
        self._key_prefix: str = ""
        # We go up the stack until there are no more WidgetBase instances
        # The idea is that each instance of a component can derive its key from the path it took to get here
        #st.write(inspect.stack())
        named_instance_used = False
        for frame in inspect.stack():
            if "self" in frame.frame.f_locals:
                frame_class = frame.frame.f_locals["self"].__class__
                if issubclass(frame_class, WidgetBase):
                    if not isinstance(frame_class, ABC) and "WidgetBase" not in frame.code_context[0]:
                        named_part = '' if named_instance is None or named_instance_used is True else f"[{named_instance}]"
                        named_instance_used = True
                        if issubclass(frame_class, BlendState):
                            self._key_prefix = f"{frame_class.__name__}{named_part}"
                        else:
                            sibling_index = 0
                            while f"{frame_class.__name__}{named_part}[{sibling_index}].{self._key_prefix}" in used_key_prefixes:
                                sibling_index += 1
                            self._key_prefix = f"{frame_class.__name__}{named_part}[{sibling_index}].{self._key_prefix}"
                            used_key_prefixes.add(self._key_prefix)
                else:
                    break
    
    def _session_state_for_this_widget(self):
        """
        Returns a dictionary of session state for this widget
        """
        return {k:v for k,v in st.session_state.items() if k.startswith(self._key_prefix)}

    def _full_key(self, key_name: str):
        """
        Builds the full key from a simple name, by adding the prefix unique to the component's instantation path
        """
        return f"{self._key_prefix}{key_name}"

    def _get_session_state(self, key_name: str):
        """
        Fetch a value from session state. key_name is the base key, it will be expanded.
        """
        if self._full_key(key_name) not in st.session_state:
            return None
        return st.session_state[self._full_key(key_name)]

    def _set_session_state(self, key_name: str, value: any):
        st.session_state[self._full_key(key_name)] = value

    def _apply_session_state_defaults(self, defaults: Dict[str, any]):
        """
        Initialises the session state for the first time with a dictionary of defaults.
        The keys will be converted to their full path within this method.
        """
        for k, v in defaults.items():
            full_key = self._full_key(k)
            if full_key not in st.session_state:
                # first, we register the key as needing to be persisted
                if _PERSIST_STATE_KEY not in st.session_state:
                    st.session_state[_PERSIST_STATE_KEY] = set()
                st.session_state[_PERSIST_STATE_KEY].add(full_key)
                st.session_state[full_key] = v

    def render(self):
        if (
            "show_component_filenames" in st.session_state
            and st.session_state["show_component_filenames"] is True
        ):
            current_class_path = inspect.getsourcefile(self.__class__)
            for f in inspect.stack():
                if f.filename.endswith("Launch.py"):
                    current_class_path = current_class_path.replace(
                        os.path.dirname(f.filename), ""
                    )
                    break
            st.markdown(f"""```{current_class_path}```""")



class BlendState(WidgetBase,ABC):
    """
    By using this class, its Widget descendants share the same state partition.
    Use thoughtfully.
    """

    def __init__(self):
        WidgetBase.__init__(self)

