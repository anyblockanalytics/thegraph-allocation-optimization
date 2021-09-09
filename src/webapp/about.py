import streamlit as st

def aboutTooling(col):
    with col.expander("Information about the Tooling 💡"):
        st.markdown(
            "# The Graph Allocation Optimization Tooling"
            "\nCheck out the [Documentation](https://enderym.github.io/allocation-optimization-doc/) "
            "\nThis web app provides metrics and functions to optimize allocations of indexers."
        )
