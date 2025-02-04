import xml.etree.ElementTree as ET
import json
import os
import re
import string
import logging
from datetime impor datetime

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def parse_node_name(label):
    """
    Parses the node label to create a human-readable name.
    Splits the label on capital letters and joins the segments with spaces.
    Capitalizes each word.

    Args:
        label (str): The original node label.

    Returns:
        str: The formatted name.
    """
    name = re.split(r'(?=[A-Z])', label)
    name = ' '.join(filter(None, name))
    name = string.capwords(name)
    return name

def extract_additional_info(comment):
    """
    Extracts additional information from the comment for nodes of type 'Action'.

    Args:
        comment (str): The comment string from the XML node.

    Returns:
        dict: A dictionary containing additional information parsed from the comment.
    """
    additional_info = {}
    for line in comment.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()  # Convert the key to lowercase
            value = value.strip()
            try:
                # Convert numeric values to integers if possible
                value = int(value)
            except ValueError:
                pass
            additional_info[key] = value
    return additional_info

def traverse(node, parent_id=None):
    """
    Recursively traverses the XML tree, extracting node and edge information.

    Args:
        node (Element): The current XML node.
        parent_id (int): The ID of the parent node, if applicable.
    """
    global node_id
    label = node.find('label').text if node.find('label') is not None else None
    comment = node.find('comment').text if node.find('comment') is not None else None
    node_type = None
    additional_info = {}

    if comment:
        # Extract the node type from the comment
        for line in comment.splitlines():
            if "Type:" in line:
                node_type = line.split("Type:")[1].strip()
                break
        # Extract additional information if the node is of type 'Action'
        if node_type == "Action":
            additional_info = extract_additional_info(comment)

    current_id = node_id
    if label:
        node_data = {
            "id": current_id,
            "name": parse_node_name(label),
            "label": label.replace(" ", ""),  # Remove spaces from the label
            "type": node_type,
        }
        # Add extra information for nodes of type 'Action'
        if node_type == "Action":
            node_data.update(additional_info)
        nodes.append(node_data)
        node_id += 1

    # Create an edge only if the node is not the root
    if parent_id is not None and label:
        edges.append({
            "id_source": parent_id,
            "id_target": current_id
        })

    # Recursively process the children of the current node
    for child in node.findall('node'):
        traverse(child, current_id)

def parse_tree(xml_input_path, output_dir, timestamp):
    """
    Parses an XML file into a JSON file.

    Args:
        xml_input_path (str): Path to the input XML file.
        output_dir (str): Folder where the output JSON file will be saved.

    Returns:
        str: Path to the generated JSON file.
    """
    logging.info("Parsing tree data from XML to JSON...")
    global nodes, edges, node_id
    nodes = []
    edges = []
    node_id = 0

    # Load the XML file
    try:
        tree = ET.parse(xml_input_path)
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file {xml_input_path}: {e}")
        raise

    root = tree.getroot()

    # Traverse the children of the root node
    for child in root.findall('node'):
        traverse(child)  # No `parent_id` passed for the root node

    # Extract XML file name (without path, but with extension)
    xml_file_name = os.path.basename(xml_input_path)

    # Generate the output file name
    input_name_without_ext = os.path.splitext(os.path.basename(xml_input_path))[0]
    output_file_name = f"{input_name_without_ext}_{timestamp}.json"
    output_file_path = os.path.join(output_dir, output_file_name)

    # Save the tree data to a JSON file
    output_data = {
        "xml_file_name": xml_file_name,
        "tree": {
            "nodes": nodes,
            "edges": edges
        }
    }

    try:
        with open(output_file_path, "w") as json_file:
            json.dump(output_data, json_file, indent=4)
        logging.info(f"JSON Tree data saved to {output_file_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON file {output_file_path}: {e}")
        raise

    return output_file_path
