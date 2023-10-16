# Import python packages
import streamlit as st
from typing import Optional
from snowflake.snowpark.context import get_active_session

# Write directly to the app
st.title("Widget reuse demo")
st.write("""Let's reuse some widgets!""")

# Get the current credentials
session = get_active_session()

from widget_base import WidgetBase
WidgetBase.prepare()

#st.write(st.session_state)

choice = st.radio(label="What should we do?",
                 options=["Choose some tables",
                         "Something else"])
if choice=="Something else":
    st.write("ok, fine")
    st.stop()
else:
    class TableChooser(WidgetBase):
        def __init__(self,
                    initial_database:Optional[str] = None,
                    initial_schema:Optional[str] = None,
                    initial_table:Optional[str] = None):
            WidgetBase.__init__(self)
            self._apply_session_state_defaults(
                {
                    "database":initial_database,
                    "schema": initial_schema,
                    "table": initial_table
                }
            )
            self.selected_database = self._get_session_state('database')
            self.selected_schema = self._get_session_state('schema')
            self.selected_table = self._get_session_state('table')
            self.full_table_name = None
            self._apply_session_state_defaults(
                {
                    "show_selection": initial_database is None or \
                                    initial_schema is None or \
                                    initial_table is None
                }
            )
            self.show_selection = self._get_session_state('show_selection')
            self.databases = [None] + [d['name'] for d in session.sql('show databases').collect()]
            if self.selected_database is None:
                return
            self.schemas = [None] + [s['name'] for s in session.sql(f"""
                show schemas in database "{self.selected_database}"
                """).collect()]
            if self.selected_schema is None:
                return
            self.tables = [None] + [t['name'] for t in session.sql(f"""
                show tables in schema "{self.selected_database}"."{self.selected_schema}"
                """).collect()]
            self.full_table_name = f'"{self.selected_database}"."{self.selected_schema}"."{self.selected_table}"'
            
        def handle_change_selection(self):
            self._set_session_state('show_selection',True)

        def handle_complete_selection(self):
            self._set_session_state('show_selection',False)
        
        def render(self):
            if self.show_selection is True:
                st.selectbox(
                    label="Database",
                    key=self._full_key("database"),
                    options=self.databases,
                    format_func=lambda x:x or '')
                
                if self.selected_database is None:
                    st.write('Please select a database')
                    return
                
                st.selectbox(
                    label="Schema",
                    key=self._full_key("schema"),
                    options=self.schemas,
                    format_func=lambda x:x or '')
                
                if self.selected_schema is None:
                    st.write('Please select a schema')
                    return
                
                st.selectbox(
                    label="Table",
                    key=self._full_key("table"),
                    options=self.tables,
                    on_change=self.handle_complete_selection,
                    format_func=lambda x:x or '')
                
                if self.selected_table is None:
                    st.write('Please select a table')
                    st.stop()
            else:
                col1,col2 = st.columns([2,1])
                with col1:
                    st.write(f"Selected Table: **{self.full_table_name}**")
                with col2:
                    st.button(label='Change',
                             key=self._full_key('change_selection'),
                             on_click=self.handle_change_selection)
                
            
            
    
    st.subheader('Select the first table')
    table_1_chooser = TableChooser()
    table_1_chooser.render()
    if table_1_chooser.full_table_name is not None:
        table_1_data = session.table(table_1_chooser.full_table_name)
        st.subheader('Select the second table')
        table_2_chooser = TableChooser(
            initial_database='SCRATCH',
            initial_schema='PUBLIC',
            initial_table='CUSTOMERS'
        )
        table_2_chooser.render()
        if table_2_chooser.full_table_name is not None:
            table_2_data = session.table(table_2_chooser.full_table_name)
        
        
            st.dataframe(table_1_data, use_container_width=True)
            st.dataframe(table_2_data, use_container_width=True)
