import subprocess
import logging
import tempfile
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def panacea(xml_content):
    """
    Executes the PANACEA tool pipeline entirely in memory.

    Args:
        xml_content (str): Content of the input XML file as a string.

    Returns:
        dict: A dictionary containing the generated PRISM outputs as strings.
    """
    PANACEA_DIR = "/app/PANACEA"
    
    try:
        # Crea file temporaneo per il contenuto XML
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=".xml") as xml_temp:
            xml_temp.write(xml_content)
            xml_temp.flush()  # Assicura che il contenuto sia scritto nel file prima di usarlo

            file_basename = os.path.splitext(os.path.basename(xml_temp.name))[0]

            # File temporanei per i risultati di PRISM
            with tempfile.NamedTemporaryFile(mode="r", delete=True, suffix=".prism") as prism_temp, \
                 tempfile.NamedTemporaryFile(mode="r", delete=True, suffix=".txt") as txt_temp, \
                 tempfile.NamedTemporaryFile(mode="r", delete=True, suffix=".csv") as csv_temp, \
                 tempfile.NamedTemporaryFile(mode="r", delete=True, suffix=".dot") as dot_temp:

                try:
                    # Esegui main.py per generare il file PRISM
                    logging.info("Running main.py script in memory...")
                    main_script_path = os.path.join(PANACEA_DIR, "main.py")
                    subprocess.run(
                        f"python {main_script_path} --input {xml_temp.name} --output {prism_temp.name}",
                        shell=True,
                        check=True,
                        executable="/bin/bash"
                    )
                    logging.info("main.py script executed successfully.")

                    # Esegui PRISM
                    logging.info("Executing PRISM in memory...")
                    prism_script_path = os.path.join(PANACEA_DIR, "prism-games-3.2.1-linux64-x86/bin/prism")
                    prism_props_path = os.path.join(PANACEA_DIR, "properties.props")
                    subprocess.run(
                        f"{prism_script_path} {prism_temp.name} {prism_props_path} -prop 1 "
                        f"-simpath 'deadlock' {txt_temp.name} "
                        f"-exportresults {csv_temp.name}:csv -exportstrat {dot_temp.name}",
                        shell=True,
                        check=True,
                        executable="/bin/bash"
                    )
                    logging.info("PRISM executed successfully.")

                    # Legge i contenuti dei file generati
                    txt_temp.seek(0)
                    csv_temp.seek(0)
                    dot_temp.seek(0)

                    txt_content = txt_temp.read()
                    csv_content = csv_temp.read()
                    dot_content = dot_temp.read()

                except subprocess.CalledProcessError as e:
                    logging.error(f"Error during command execution: {e}")
                    raise RuntimeError(f"Command execution failed: {e}")

        logging.info("Panacea completed successfully.")

        return {
            "txt_content": txt_content,
            "csv_content": csv_content,
            "dot_content": dot_content
        }

    except Exception as e:
        logging.error(f"Error: {e}")
        raise RuntimeError(f"Error: {e}")
