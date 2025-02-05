import json
import xml.etree.ElementTree as ET
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_hidden_labels(json_content):
    """
    Extracts the labels of nodes marked as hidden from the JSON content.

    Args:
        json_content (dict): JSON content as a dictionary.

    Returns:
        list: A list of labels for nodes marked as hidden.
    """
    try:
        hidden_labels = [
            node["label"]
            for node in json_content["tree"]["nodes"]
            if node.get("hidden") is True
        ]
        logging.info(f"Hidden labels extracted: {hidden_labels}")
        return hidden_labels
    except Exception as e:
        logging.error(f"Failed to parse JSON content: {e}")
        raise

def remove_subtrees_from_xml(xml_content, hidden_labels):
    """
    Removes subtrees from the XML based on the specified labels.

    Args:
        xml_content (str): XML content as a string.
        hidden_labels (list): A list of labels for nodes to remove.

    Returns:
        str: The pruned XML content as a string.
    """
    try:
        tree = ET.ElementTree(ET.fromstring(xml_content))
        root = tree.getroot()

        def should_remove(node):
            """Checks if a node should be removed based on its label."""
            label_element = node.find("label")
            return label_element is not None and label_element.text in hidden_labels

        def remove_nodes(parent):
            """Recursively removes matching nodes from the XML tree."""
            for child in list(parent):
                if should_remove(child):
                    logging.info(f"Removing node with label: {child.find('label').text}")
                    parent.remove(child)
                else:
                    remove_nodes(child)

        remove_nodes(root)

        # Convert the modified XML tree back to a string
        return ET.tostring(root, encoding="unicode")

    except Exception as e:
        logging.error(f"Failed to process XML content: {e}")
        raise

def prune_tree(json_content, xml_content):
    """
    Prunes an XML tree by removing subtrees specified in the JSON content.

    Args:
        json_content (dict): JSON content as a dictionary.
        xml_content (str): XML content as a string.

    Returns:
        str: The pruned XML content as a string.
    """
    try:
        logging.info("Extracting hidden labels from JSON content...")
        hidden_labels = get_hidden_labels(json_content)

        logging.info("Pruning XML tree using extracted labels...")
        pruned_xml = remove_subtrees_from_xml(xml_content, hidden_labels)

        logging.info("Pruned XML tree successfully generated.")
        return pruned_xml
    except Exception as e:
        logging.error(f"Failed to prune tree: {e}")
        raise
