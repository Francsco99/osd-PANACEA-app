import os
import subprocess
import logging

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def panacea(xml_file_path, output_dir):
    """
    Executes the PANACEA tool pipeline, generating PRISM input files, running the main script, 
    and processing results using PRISM to produce outputs in TXT, DOT, and CSV formats.

    Args:
        xml_file_path (str): Path to the input XML file.
        output_dir (str): Directory to save the output files.

    Returns:
        dict: Paths to the generated TXT, CSV, and DOT files.
    """
    PRISM_INPUT_DIR = os.path.join(output_dir, "input")
    PRISM_OUTPUT_TXT = os.path.join(output_dir, "output", "txt")
    PRISM_OUTPUT_DOT = os.path.join(output_dir, "output", "dot")
    PRISM_OUTPUT_CSV = os.path.join(output_dir, "output", "csv")
    PANACEA_DIR = "/app/PANACEA"

    # Create directories for output files if they do not exist
    os.makedirs(PRISM_INPUT_DIR, exist_ok=True)
    os.makedirs(PRISM_OUTPUT_TXT, exist_ok=True)
    os.makedirs(PRISM_OUTPUT_DOT, exist_ok=True)
    os.makedirs(PRISM_OUTPUT_CSV, exist_ok=True)
    
    try:
        # Check that the XML file exists
        if not os.path.exists(xml_file_path):
            raise FileNotFoundError(f"The XML file {xml_file_path} was not found!")

        # Derive the base name of the file without the extension
        file_basename = os.path.splitext(os.path.basename(xml_file_path))[0]

        # Define paths for output files
        prism_input_path = os.path.join(PRISM_INPUT_DIR, f"{file_basename}.prism")
        txt_path = os.path.join(PRISM_OUTPUT_TXT, f"{file_basename}.txt")
        strategy_dot_path = os.path.join(PRISM_OUTPUT_DOT, f"{file_basename}.dot")
        results_csv_path = os.path.join(PRISM_OUTPUT_CSV, f"{file_basename}.csv")

        try:

            # 1. Run the main.py script
            logging.info("Running main.py script...")
            main_script_path = os.path.join(PANACEA_DIR, "main.py")
            subprocess.run(
                f"python {main_script_path} --input {xml_file_path} --output {prism_input_path}",
                shell=True,
                check=True,
                executable="/bin/bash"
            )
            logging.info("main.py script executed.")

            # 3. Execute PRISM
            logging.info("Executing PRISM...")
            prism_script_path = os.path.join(PANACEA_DIR, "prism-games-3.2.1-linux64-x86/bin/prism")
            prism_props_path = os.path.join(PANACEA_DIR, "properties.props")
            subprocess.run(
                f"{prism_script_path} {prism_input_path} {prism_props_path} -prop 1 "
                f"-simpath 'deadlock' {txt_path} "
                f"-exportresults {results_csv_path}:csv -exportstrat {strategy_dot_path}",
                shell=True,
                check=True,
                executable="/bin/bash"
            )
            logging.info("PRISM executed.")

        except subprocess.CalledProcessError as e:
            logging.error(f"Error during command execution: {e}")
            raise

        logging.info(f"Output successfully generated in the following locations:\n"
              f"- TXT: {txt_path}\n"
              f"- CSV: {results_csv_path}\n"
              f"- DOT: {strategy_dot_path}\n")
        return {
            "txt_path": txt_path,
            "csv_path": results_csv_path,
            "dot_path": strategy_dot_path
        }

    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        raise RuntimeError(f"Command execution failed: {e}")
    except Exception as e:
        logging.error(f"Error: {e}")
        raise RuntimeError(f"Error: {e}")