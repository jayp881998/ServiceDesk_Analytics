import json
import time
import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# In production, store credentials in environment variables
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN')
ZENDESK_USER_EMAIL = os.getenv('ZENDESK_EMAIL')
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')

# Authentication for Zendesk API
auth = (f'{ZENDESK_USER_EMAIL}/token', ZENDESK_API_TOKEN)

# Define the start time for historical ticket data (UNIX timestamp)
start_time = 1546300800  # Replace with your desired start time

# Function to fetch ticket data
def fetch_tickets():
    print('Getting tickets from Zendesk...')
    tickets = []
    seen_tickets = set()  # To track seen (id, updated_at) combinations
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/incremental/tickets.json?start_time={start_time}&include=metric_sets"

    while url:
        response = requests.get(url, auth=auth)
        if response.status_code == 429:
            print('Rate limited! Please wait.')
            time.sleep(int(response.headers['retry-after']))
            continue
        if response.status_code != 200:
            print(f'Error fetching tickets with status code {response.status_code}')
            exit()
        
        data = response.json()
        for ticket in data['tickets']:
            # Create a unique identifier for the ticket using (id, updated_at)
            ticket_id = ticket['id']
            updated_at = ticket['updated_at']
            
            # Check if this (id, updated_at) combination has already been seen
            if (ticket_id, updated_at) not in seen_tickets:
                seen_tickets.add((ticket_id, updated_at))  # Add to seen set
                tickets.append(ticket)  # Append unique ticket to the list

        # Check if there is more data to fetch
        if data['end_of_stream']:
            url = None
        else:
            url = data['next_page']

        # Optional: Wait to avoid hitting the rate limit
        time.sleep(1)

    # Save the fetched data to a JSON file
    ticket_output_file = "./output/ZendeskTickets.json"
    with open(ticket_output_file, mode='w', encoding='utf-8') as f:
        json.dump(tickets, f, sort_keys=True, indent=2)

    df_tickets = pd.json_normalize(tickets)

    unique_columns = df_tickets.columns.tolist()
    print(f'Ticket data unique columns: {unique_columns}')
    print(f'Number of ticket columns: {len(df_tickets.columns)}')
    print(f"Ticket data saved to {ticket_output_file}. Number of records: {len(tickets)}")


# Function to fetch user data
def fetch_users():
    print('Getting users from Zendesk...')
    users = []
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users.json'
    params = {'page[size]': 100}

    response = requests.get(url, params=params, auth=auth)
    if response.status_code != 200:
        print(f"Failed to fetch users: {response.status_code}")
        return
    
    page = response.json()
    users.extend(page['users'])
    
    while page['meta']['has_more']:
        params['page[after]'] = page['meta']['after_cursor']
        response = requests.get(url, params=params, auth=auth)
        
        if response.status_code == 429:  # if rate limit reached
            retry_after = int(response.headers.get('retry-after', 1))
            print(f'Rate limited! Waiting for {retry_after} seconds.')
            time.sleep(retry_after)
            response = requests.get(url, params=params, auth=auth)
        
        if response.status_code != 200:
            print(f"Failed to fetch users on next page: {response.status_code}")
            break

        page = response.json()
        users.extend(page['users'])

    # Save the users data to a JSON file
    user_output_file = "./output/ZendeskUsers.json"
    with open(user_output_file, mode='w', encoding='utf-8') as f:
        json.dump(users, f, sort_keys=True, indent=2)
    
    # Load the user data into a pandas DataFrame for analysis
    df_users = pd.json_normalize(users)

    # Print unique columns and number of columns
    unique_columns = df_users.columns.tolist()
    print(f'User data unique columns: {unique_columns}')
    print(f'Number of user columns: {len(df_users.columns)}')
    print(f"User data saved to {user_output_file}. Number of records: {len(users)}")

# Main function to run both fetch operations
def main():
    fetch_tickets()
    fetch_users()

if __name__ == "__main__":
    main()
