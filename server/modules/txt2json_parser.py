import json
import os
import logging

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

import logging
import json

def extract_policy(txt_content):
    """
    Parses a tabular text file content (as a string), extracts states and actions,
    and returns a corresponding JSON structure excluding the fields 'action', 'step', and 'sched'.

    :param txt_content: Content of the TXT file as a string.
    :return: Dictionary containing the extracted policy data.
    """
    logging.info("Parsing TXT policy to JSON in memory...")

    # Split content into lines
    lines = txt_content.strip().split("\n")

    # Extract column headers from the first line
    ELEMENTS = lines[0].strip().split()

    # Remove the first line (header) and the last line (final state)
    lines = lines[1:]

    states = []

    for line in lines:
        if not line.strip():
            continue  # Skip empty lines
        
        # Split the line into cells
        cells = line.split()
        
        # Extract the action within square brackets and remove it
        action = None
        if cells[0].startswith("[") and cells[0].endswith("]"):
            action = cells[0][1:-1]  # Removes square brackets
        
        # Map values to their respective elements
        def parse_value(value):
            if value == "-":
                return None
            if value == "false":
                return False
            if value == "true":
                return True
            try:
                return float(value) if "." in value else int(value)
            except ValueError:
                return value

        state_data = {ELEMENTS[i]: parse_value(cells[i]) for i in range(len(cells))}
        
        # Use the value of the `step` field as the `state_id`
        state_id = state_data["step"]

        # Exclude the fields 'action', 'step', and 'sched' from state_data
        filtered_state_data = {k: v for k, v in state_data.items() if k not in ["action", "step", "sched"]}

        states.append({
            "state_id": int(state_id),
            "state_data": filtered_state_data,
            "optimal_action": action
        })

    logging.info("Policy successfully parsed into JSON.")

    return {"states": states}  # Restituisce direttamente il JSON
