import json
import os
import logging

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_policy(json_input_path, output_dir, timestamp):
    """
    Parses a tabular file with space-separated cells, extracts states and actions,
    and saves a corresponding JSON file excluding the fields 'action', 'step', and 'sched' from state_data.

    :param json_input_path: Path to the input file.
    :param output_dir: Output directory for the JSON file.
    :param timestamp: Timestamp.
    """
    logging.info("Parsing TXT policy to JSON...")

    with open(json_input_path, 'r') as file:
        lines = file.readlines()

    # Extract column headers from the first line of the file
    ELEMENTS = lines[0].strip().split()

    # Remove the first line (header) and the last line (final state)
    lines = lines[1:]

    states = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Split the line into cells
        cells = line.split()
        # Extract the action within square brackets and remove it
        action = None
        if cells[0].startswith("[") and cells[0].endswith("]"):
            action = cells[0][1:-1]  # Removes the square brackets
        
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

    # Generate the output JSON file path
    output_file_name = f"{os.path.splitext(os.path.basename(json_input_path))[0]}_{timestamp}.json"
    output_path = os.path.join(output_dir, output_file_name)

    # Save the data as JSON
    try:
        with open(output_path, 'w') as json_file:
            json.dump({"states": states}, json_file, indent=4)
        logging.info(f"JSON policy data saved to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON policy data to: {output_path}: {e}")
        raise
        
    return output_path
