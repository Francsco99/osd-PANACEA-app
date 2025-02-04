import json
import xml.etree.ElementTree as ET
import os
import logging

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_hidden_labels(json_file):
    """
    Reads the JSON file and returns the labels of nodes with hidden=true.

    Args:
        json_file (str): Path to the input JSON file.

    Returns:
        list: A list of labels for nodes marked as hidden.
    """
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
        # Extract the labels of nodes with hidden=true
        hidden_labels = [
            node["label"]
            for node in data["tree"]["nodes"]
            if node.get("hidden") is True
        ]
        logging.info(f"Hidden labels extracted: {hidden_labels}")
        return hidden_labels
    except Exception as e:
        logging.error(f"Failed to read JSON file {json_file}: {e}")
        raise

def remove_subtrees_from_xml(xml_file, hidden_labels, output_file):
    """
    Removes subtrees from the XML based on the specified labels.

    Args:
        xml_file (str): Path to the input XML file.
        hidden_labels (list): A list of labels for nodes to remove.
        output_file (str): Path to save the pruned XML file.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        def should_remove(node):
            """
            Checks if a node should be removed based on its label.

            Args:
                node (Element): An XML node.

            Returns:
                bool: True if the node should be removed, False otherwise.
            """
            label_element = node.find("label")
            return label_element is not None and label_element.text in hidden_labels

        def remove_nodes(parent):
            """
            Recursively removes child nodes from a parent node.

            Args:
                parent (Element): The parent XML node.
            """
            for child in list(parent):
                if should_remove(child):
                    logging.info(f"Removing node with label: {child.find('label').text}")
                    parent.remove(child)
                else:
                    remove_nodes(child)

        # Remove nodes with the specified labels
        remove_nodes(root)

        # Save the updated XML file
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        logging.info(f"Pruned XML file saved to: {output_file}")
    except Exception as e:
        logging.error(f"Failed to process XML file {xml_file}: {e}")
        raise

def prune_tree(json_input_file, xml_input_file, output_folder):
    """
    Prunes an XML tree by removing subtrees specified in the JSON file.

    Args:
        json_input_file (str): Path to the input JSON file.
        xml_input_file (str): Path to the input XML file.
        output_folder (str): Directory to save the pruned XML file.

    Returns:
        str: Path to the generated pruned XML file.
    """
    try:
        # Get the labels of nodes to remove
        logging.info("Reading hidden labels from JSON file...")
        hidden_labels = get_hidden_labels(json_input_file)

        # Generate the name of the output file
        input_name_without_ext = os.path.splitext(os.path.basename(json_input_file))[0]
        pruned_file_name = f"{input_name_without_ext}_pruned.xml"
        xml_output_file = os.path.join(output_folder, pruned_file_name)

        logging.info(f"Pruning XML tree using labels: {hidden_labels}")

        # Remove the specified subtrees
        remove_subtrees_from_xml(xml_input_file, hidden_labels, xml_output_file)

        return xml_output_file
    except Exception as e:
        logging.error(f"Failed to prune tree: {e}")
        raise
