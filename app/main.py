
"""Main Streamlit entry point for FlowDesk.

Sets up page configuration, sidebar navigation, and routes to the
appropriate page based on user selection.
"""

import streamlit as st

from app.pages import admin_dashboard, staff_dashboard, student_portal

# Navigation options mapped to their render functions
_PAGES: dict[str, callable] = {
    "Student Portal": student_portal.render,
    "Staff Dashboard": staff_dashboard.render,
    "Admin Dashboard": admin_dashboard.render,
}


def main() -> None:
    """Configure the Streamlit page and render the selected page.

    Sets the page title to 'FlowDesk' with a wide layout, displays a
    sidebar for navigation, and delegates rendering to the chosen page
    module.
    """
    st.set_page_config(page_title="FlowDesk", layout="wide")

    st.sidebar.title("FlowDesk")
    selection = st.sidebar.radio("Navigate", list(_PAGES.keys()))

    # Route to the selected page
    page_render = _PAGES.get(selection)
    if page_render is not None:
        page_render()


if __name__ == "__main__":
    main()
