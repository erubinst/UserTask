import dash
from dash import html, dcc, Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
from flask import request, jsonify
import config
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize an empty DataFrame to store tasks
tasks_df = pd.DataFrame(columns=['name', 'structureType', 'taskId'])
latest_received_message = None

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Task Tracker"), className="display-4", width=12)),
    html.Div([
        dbc.Row([
            dbc.Col(html.Div("Name", className='fw-bold fs-4'), width=2),
            dbc.Col(html.Div("Product", className='fw-bold fs-4'), width=2)
        ]),
        dbc.Row(html.Br())
    ]),
    # Display existing tasks
    dbc.Row([dbc.Col(html.Div(id='task-list'), width = 6),
            dbc.Col(dbc.Button('Complete', id='complete-button', color='success', style={'display': 'none'}), width = 2)]),
    # Interval component to periodically check for new tasks
    dcc.Interval(
        id='interval-component',
        interval=1000,  # in milliseconds, adjust as needed
        n_intervals=0
    )   
])

def update_messages():
    message = request.get_json()
    if message:
        config.latest_received_message = message
    return jsonify(success=True)

server = app.server
server.add_url_rule('/task', view_func=update_messages, methods=['POST'])

def update_task_list_helper():
    task_rows = []
    for index, row in tasks_df.iterrows():
        task_rows.append(dbc.Row([
            dbc.Col(html.Div(f"{row['name']}"), width=4),
            dbc.Col(html.Div(f"{row['structureType']}"), width=4),
            dbc.Row(html.Br())
        ]))
    return task_rows

# Callback to update task list and show/hide complete button
@app.callback(
    [Output('task-list', 'children'),
     Output('complete-button', 'style')],
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)
def update_task_list_and_button(n_intervals):
    if config.latest_received_message is None:
        raise PreventUpdate
    new_task_msg = config.latest_received_message
    name = new_task_msg.get('name', 'Unknown')
    structure_type = new_task_msg.get('structureType', 'Unknown')
    taskId = new_task_msg.get('taskId', 'Unknown')

    # Append the new task information to the DataFrame
    tasks_df.loc[(len(tasks_df.index))] = [name, structure_type, taskId]

    task_rows = update_task_list_helper()

    config.latest_received_message = None

    # Check if there are tasks to display - not sure if I need this here
    complete_button_style = {'display': 'none'} if len(tasks_df) == 0 else {'display': 'inline-block'}

    return task_rows, complete_button_style

@app.callback(
    [Output('task-list', 'children', allow_duplicate=True),
     Output('complete-button', 'style', allow_duplicate=True)],
    [Input('complete-button', 'n_clicks')],
    prevent_initial_call=True
)
def complete_task(n_clicks):
    if n_clicks is None or len(tasks_df) == 0:
        raise PreventUpdate

    # Remove the completed task
    completed_task = tasks_df.iloc[0]
    tasks_df.drop(tasks_df.index[0], inplace=True)

    # Send completed task message to the server
    complete_message = {
        "msgType": "EndTask",
        "taskId": int(completed_task['taskId']),
        "name": completed_task['name'],
        "outcome": "success"
    }
    executer_url = 'http://localhost:9091/execution-ui'
    response = requests.post(executer_url, json=complete_message)
    print(response.text)

    # Check if there are tasks to display
    complete_button_style = {'display': 'none'} if len(tasks_df) == 0 else {'display': 'inline-block'}

    # Update the task list
    task_rows = update_task_list_helper()

    return task_rows, complete_button_style



if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0")
