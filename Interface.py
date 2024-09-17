import streamlit as st
import streamlit_authenticator as stauth
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the style_tables dictionary from the pickle file
with open('style_tables.pkl', 'rb') as f:
    style_tables = pickle.load(f)

# Usernames and names
names = ['May Shaw', 'Max Xiang']
usernames = ['mayshaw', 'maxxiang']

# Hashed passwords (replace with your actual hashed passwords)
hashed_passwords = [
    '$2b$12$2BXijxBk6gRtwv.aMAD6Ku6mdpVqQJCWMlks9OSn9hd3JfgZexT76',
    '$2b$12$upzorxoKyMTn/e/MhPPO9eBwQdhPa7JGoATSTMHOGUbhtmut0GAme'
]

# Create credentials dictionary
credentials = {
    'usernames':{
        usernames[0]:{
            'name': names[0],
            'password': hashed_passwords[0]
        },
        usernames[1]:{
            'name': names[1],
            'password': hashed_passwords[1]
        }
    }
}


# Create an authenticator object
authenticator = stauth.Authenticate(credentials, 'cookie_name', 'signature_key', cookie_expiry_days=30)

# Authentication logic
name, authentication_status, username = authenticator.login(location='main')

# Show different content based on authentication status
def format_thousands(x):
    if pd.isnull(x):
        return ""  # You can choose a placeholder like "N/A" if preferred
    elif isinstance(x, (int, float)):
        return "{:,.0f}".format(x)
    else:
        return x  # Return the value as is if it's not numeric

if authentication_status:
    st.write(f'Welcome {name}!')

    # Optional: Add a logout button in the sidebar
    authenticator.logout('Logout', 'sidebar')

    # Title of the app
    st.title("Inventory Turnover Analysis")

    # Sidebar for search and style selection
    st.sidebar.header("Search and Select")

    # Search bar for filtering styles
    search_query = st.sidebar.text_input("Search for a style", "")

    # Filter styles based on the search query
    filtered_styles = [style for style in style_tables.keys() if search_query.lower() in style.lower()]

    # Dropdown menu for selecting the style from the filtered list
    style = st.sidebar.selectbox("Select Style", filtered_styles)

    # Display the selected style's table
    if style:
        st.write(f"## Analysis for Style: {style}")

        # Apply custom formatter to handle NaN values
        formatted_table = style_tables[style].style.format(format_thousands)

        # Display the full table with full width
        st.write("### Full Data Table")
        st.dataframe(formatted_table.set_table_styles([{
            'selector': 'th',
            'props': [('white-space', 'normal')]
        }]), width=1500, height=600)


        st.write("### Detailed Metrics with Visualization")

        # Define lists of metrics
        individual_metrics = ['Storage Cost','Gross Sales', 'Profit', 'Gross Margin']
        combined_metrics = [('Invoiced PRs', 'Received Pairs')]

        # Inventory Turn and Months on Hand
        if 'Inventory Turn' in style_tables[style].index:
            inventory_turn_totals = style_tables[style].loc['Inventory Turn'].filter(like='Total')
            inventory_turn_totals = pd.to_numeric(inventory_turn_totals, errors='coerce').dropna()
            inventory_turn_totals = inventory_turn_totals.round(2)
            if not inventory_turn_totals.empty:
                st.write("### Inventory Turn (Totals Only):")
                st.write(inventory_turn_totals.to_frame())

                fig, ax = plt.subplots()
                inventory_turn_totals.plot(kind='line', ax=ax, marker='o', title='Inventory Turn')
                ax.set_ylabel('Turn Rate')
                ax.set_xlabel('Year')
                ax.set_ylim([inventory_turn_totals.min() * 0.9, inventory_turn_totals.max() * 1.1])
                st.pyplot(fig)
            else:
                st.write("No numeric data available for 'Inventory' totals.")
        else:
            st.write("Metric 'Inventory Turn' not found in DataFrame.")

        if 'Months on Hand' in style_tables[style].index:
            months_on_hand_totals = style_tables[style].loc['Months on Hand'].filter(like='Total')
            months_on_hand_totals = pd.to_numeric(months_on_hand_totals, errors='coerce').dropna()

            if not months_on_hand_totals.empty:
                st.write("### Months on Hand (Totals Only):")
                st.write(months_on_hand_totals.to_frame())

                fig, ax = plt.subplots()
                months_on_hand_totals.plot(kind='line', ax=ax, marker='o', title='Months on Hand (Totals)')
                ax.set_ylabel('Months on Hand')
                ax.set_xlabel('Year')
                ax.set_ylim([months_on_hand_totals.min() * 0.9, months_on_hand_totals.max() * 1.1])
                st.pyplot(fig)
            else:
                st.write("No numeric data available for 'Months on Hand' totals.")
        else:
            st.write("Metric 'Months on Hand' not found in DataFrame.")

        # Plot individual metrics
        for metric in individual_metrics:
            if metric in style_tables[style].index:
                metric_data = style_tables[style].loc[metric]
                # Exclude 'Total' columns if desired
                metric_data = metric_data[[col for col in metric_data.index if 'Total' not in col]]

                # Handle data conversion: Remove any symbols like $ or % for calculation purposes
                if metric_data.dtype == 'object':
                    metric_data_numeric = metric_data.replace('[\$,]', '', regex=True).replace('[\%,]', '', regex=True)
                metric_data_numeric = pd.to_numeric(metric_data_numeric, errors='coerce').dropna()

                if not metric_data_numeric.empty:
                    # Check the first element for symbol detection and apply appropriate formatting
                    if '$' in metric_data.iloc[0]:  # If the data represents dollar values
                        formatted_data = metric_data_numeric.apply(lambda x: f"${x:,.2f}")
                    elif '%' in metric_data.iloc[0]:  # If the data represents percentages
                        formatted_data = metric_data_numeric.apply(lambda x: f"{x:.2f}%")
                    else:
                        formatted_data = metric_data_numeric.round(2)  # Just round to 2 decimals otherwise

                    # Display the formatted table
                    st.write(f"#### {metric} Table")
                    st.write(formatted_data.to_frame().transpose())

                    # Create the plot (based on numeric values without symbols)
                    fig, ax = plt.subplots()
                    metric_data_numeric.plot(kind='line', ax=ax, marker='o', title=metric)
                    ax.set_ylabel(metric)
                    ax.set_xlabel('Time')  # Adjust as needed
                    ax.set_ylim([metric_data_numeric.min() * 0.9, metric_data_numeric.max() * 1.1])
                    st.pyplot(fig)
                else:
                    st.write(f"No numeric data available for metric '{metric}'.")
            else:
                st.write(f"Metric '{metric}' not found in DataFrame.")

        # Plot combined metrics
        for metric1, metric2 in combined_metrics:
            if metric1 in style_tables[style].index and metric2 in style_tables[style].index:
                data_metric1 = style_tables[style].loc[metric1]
                data_metric2 = style_tables[style].loc[metric2]

                # Exclude 'Total' columns if desired
                data_metric1 = data_metric1[[col for col in data_metric1.index if 'Total' not in col]]
                data_metric2 = data_metric2[[col for col in data_metric2.index if 'Total' not in col]]

                # Handle data conversion
                if data_metric1.dtype == 'object':
                    data_metric1 = data_metric1.replace('[\$,]', '', regex=True)
                data_metric1 = pd.to_numeric(data_metric1, errors='coerce').dropna()

                if data_metric2.dtype == 'object':
                    data_metric2 = data_metric2.replace('[\$,]', '', regex=True)
                data_metric2 = pd.to_numeric(data_metric2, errors='coerce').dropna()

                # Align data by index (time periods)
                combined_data = pd.DataFrame({metric1: data_metric1, metric2: data_metric2})

                if not combined_data.empty:
                    # Display the combined data table
                    st.write(f"#### {metric1} and {metric2} Table")
                    st.write(combined_data.transpose())

                    # Create the plot
                    fig, ax = plt.subplots()
                    combined_data[metric1].plot(kind='line', ax=ax, marker='o', color='red', label=metric1)
                    combined_data[metric2].plot(kind='line', ax=ax, marker='o', color='blue', label=metric2)

                    ax.set_ylabel('Number of Pairs')
                    ax.set_xlabel('Time')  # Adjust as needed
                    ax.set_title(f'{metric1} vs. {metric2}')
                    ax.legend()

                    ymin = combined_data.min().min() * 0.9
                    ymax = combined_data.max().max() * 1.1
                    ax.set_ylim([ymin, ymax])

                    st.pyplot(fig)
                else:
                    st.write(f"No data available for metrics '{metric1}' and '{metric2}'.")
            else:
                st.write(f"Metrics '{metric1}' or '{metric2}' not found in DataFrame.")

elif authentication_status == False:
    st.error('Username/password is incorrect')

elif authentication_status == None:
    st.warning('Please enter your username and password')
