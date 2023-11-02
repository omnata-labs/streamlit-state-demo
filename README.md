# streamlit-state-demo
A demo showing some tips for managing component state during reuse.

This repo contains:
- A python module ([widget_base.py](src/widget_base.py)), which contains a base class you can extend when creating reusable Streamlit widgets
- An example ([streamlit_app.py](src/streamlit_app.py)), which contains an example of this class being used in Streamlit to create a table chooser widget.

The WidgetBase class automatically isolates the session state of its Streamlit fields, by inspecting the stack trace and creating a namespace.

It also encourages separation of state management and rendering. This encourages the "result" of some UI selections to be useful downstream, even if the fields are no longer rendered.

