import os
import argparse
import pandas as pd
import time
import requests
import json


def get_study_by_criteria(
    orthanc_url,
    accession_number,
    username=None,
    password=None,
):
    """
    Queries Orthanc to retrieve studies based on the patient ID, study date, and modality.

    Args:
        orthanc_url (str): The base URL of your Orthanc server (e.g., "http://localhost:8042").
        accession_number (str, optional): The accession number of the study to search for.
        username (str, optional): Username for Orthanc authentication.
        password (str, optional): Password for Orthanc authentication.

    Returns:
        list: A list of dictionaries, each representing a matching study with its details.
              Returns an empty list if no study is found.
    """
    auth = (username, password) if username and password else None
    search_url = f"{orthanc_url}/tools/find"

    # Build the DICOM Query/Retrieve (Q/R) request
    query = {"Level": "Study", "Query": {"AccessionNumber": accession_number}}

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            search_url, data=json.dumps(query), auth=auth, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP error status codes

        study_ids = response.json()
        if not study_ids:
            print(f"No study found for AccessionNumber: {accession_number}")
            return []

        found_studies = []
        print(f"Studies found (IDs): {study_ids}")

        # For each study ID found, retrieve the study details
        for study_id in study_ids:
            study_details_url = f"{orthanc_url}/studies/{study_id}"
            details_response = requests.get(study_details_url, auth=auth)
            details_response.raise_for_status()
            found_studies.append(details_response.json())
            print(f"Details of study {study_id} retrieved.")

        return found_studies
    except:
        print("Error checking in PACS")


def find_and_retrieve_from_remote_aet(
    orthanc_url,
    remote_aet_name,
    accession_number,
    retrieve_aet_title=None,
    username=None,
    password=None,
):
    """
    Queries a remote AET via Orthanc (C-FIND) and retrieves the found studies (C-MOVE/C-GET).

    Args:
        orthanc_url (str): The base URL of your Orthanc server (e.g., "http://localhost:8042").
        remote_aet_name (str): The name of the remote modality/AET configured in Orthanc
                               (e.g., "EXTERNAL_PACS"). This must be the name you assigned
                               to the external AET in your Orthanc configuration.
        accession_number (str): The accession number of the study to search for.
        retrieve_aet_title (str, optional): The AET to retrieve the studies to.
                                            If None, Orthanc will attempt to retrieve them to itself.
                                            This is usually the AET of your Orthanc.
        username (str, optional): Username for Orthanc authentication.
        password (str, optional): Password for Orthanc authentication.

    Returns:
        list: A list of dictionaries, each representing a retrieved study with its details.
              Returns an empty list if no study is found or if the retrieval fails.
    """
    auth = (username, password) if username and password else None
    find_url = f"{orthanc_url}/modalities/{remote_aet_name}/query"

    # Build the C-FIND DICOM request
    # "Study" level to find studies
    query = {"Level": "Study", "Query": {"AccessionNumber": accession_number}}

    headers = {"Content-Type": "application/json"}

    print(
        f"Attempting C-FIND on '{remote_aet_name}' for AccessionNumber: {accession_number}..."
    )
    try:
        # Step 1: Execute the C-FIND to find studies
        response = requests.post(
            find_url, data=json.dumps(query), auth=auth, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP error status codes

        study_instance_uids = response.json()
        if not study_instance_uids:
            print(f"No study found on '{remote_aet_name}' for the specified criteria.")
            return []

        print(
            f"Studies found on '{remote_aet_name}' (StudyInstanceUIDs): {study_instance_uids}"
        )
        move_url = f"{orthanc_url}{study_instance_uids['Path']}/retrieve"
        response = requests.post(
            move_url, data=retrieve_aet_title, auth=auth, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP error status codes

        time.sleep(2)
        studies_found = get_study_by_criteria(
            orthanc_url=ORTHANC_URL,
            accession_number=an_to_find,
            username=ORTHANC_USERNAME,
            password=ORTHANC_PASSWORD,
        )
        return studies_found[0]["ID"]
    except:
        print(f"Error transferring for {an_to_find}.")
        return []


def download_study_zip_by_id(
    orthanc_url,
    orthanc_study_id,
    output_filename="Study.zip",
    username=None,
    password=None,
):
    """
    Downloads an Orthanc study as a ZIP file using its internal Orthanc ID.

    Args:
        orthanc_url (str): The base URL of your Orthanc server (e.g., "http://localhost:8042").
        orthanc_study_id (str): The internal Orthanc ID of the study (e.g., "6b9e19d9-62094390-5f9ddb01-4a191ae7-9766b715").
        output_filename (str): The name of the ZIP file to save. Defaults to "Study.zip".
        username (str, optional): Username for Orthanc authentication.
        password (str, optional): Password for Orthanc authentication.

    Returns:
        str or None: The full path to the downloaded file if successful, otherwise None.
    """
    auth = (username, password) if username and password else None
    download_url = f"{orthanc_url}/studies/{orthanc_study_id}/archive"

    print(f"Attempting to download study {orthanc_study_id} as '{output_filename}'...")

    try:
        # Use stream=True for potentially large files
        response = requests.get(download_url, stream=True, auth=auth)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        with open(output_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(
            f"Study '{orthanc_study_id}' successfully downloaded to '{output_filename}'"
        )
        return os.path.abspath(output_filename)

    except requests.exceptions.ConnectionError as e:
        print(
            f"Connection error: Could not connect to Orthanc at {orthanc_url}. Error: {e}"
        )
        return None
    except requests.exceptions.HTTPError as e:
        print(
            f"HTTP error during download: {e.response.status_code} - {e.response.text}"
        )
        if e.response.status_code == 404:
            print(f"Error: Study with ID '{orthanc_study_id}' not found on Orthanc.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Export patients form Orthanc PACS")
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("output_folder", help="Folder for ZIP files")
    parser.add_argument("--orthanc_url", required=True, help="Orthanc URL")
    parser.add_argument("--orthanc_username", required=True, help="Orthanc Username")
    parser.add_argument("--orthanc_password", required=True, help="Orthanc Password")
    parser.add_argument("--remote_aet_name", required=True, help="Remote AET Name")
    parser.add_argument("--my_orthanc_aet", required=True, help="My Orthanc AET")
    args = parser.parse_args()

    ORTHANC_URL = args.orthanc_url
    ORTHANC_USERNAME = args.orthanc_username
    ORTHANC_PASSWORD = args.orthanc_password
    REMOTE_AET_NAME = args.remote_aet_name
    MY_ORTHANC_AET = args.my_orthanc_aet

    os.makedirs(args.output_folder, exist_ok=True)
    df = pd.read_csv(args.csv_path)

    for idx, row in df.iterrows():
        an_to_find = str(row["AccessionNumber"]).strip()

        studies_found = get_study_by_criteria(
            ORTHANC_URL,
            an_to_find,
            username=ORTHANC_USERNAME,
            password=ORTHANC_PASSWORD,
        )
        if len(studies_found) == 0:
            orthanc_retrieved_id = find_and_retrieve_from_remote_aet(
                orthanc_url=ORTHANC_URL,
                remote_aet_name=REMOTE_AET_NAME,
                accession_number=an_to_find,
                retrieve_aet_title=MY_ORTHANC_AET,
                username=ORTHANC_USERNAME,
                password=ORTHANC_PASSWORD,
            )
        else:
            orthanc_retrieved_id = studies_found[0]["ID"]

        patient_folder = os.path.join(args.output_folder, str(row["Patient Name"]))
        session_folder = os.path.join(patient_folder, str(row["session"]))
        os.makedirs(session_folder, exist_ok=True)
        output_file_path = os.path.join(session_folder, f"{an_to_find}.zip")
        download_study_zip_by_id(
            orthanc_url=ORTHANC_URL,
            orthanc_study_id=orthanc_retrieved_id,
            output_filename=output_file_path,
            username=ORTHANC_USERNAME,
            password=ORTHANC_PASSWORD,
        )


if __name__ == "__main__":
    main()
