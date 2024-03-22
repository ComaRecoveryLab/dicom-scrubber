#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import json
import random
import string

import pydicom as dcm

def vr_scrub(tag, vr):
    """
    Provides de-identified value for DICOM fields based on Value Representations (VRs).

    Args:
        vr (str): The DICOM Value Representation (VR) of the data.

    Returns:
        str, int, float, or bytes: Redacted or replaced value based on the VR.
            - For string types (LO, SH, PN, LT, ST, UT, TM, DT, CS, UI), returns 'REDACTED'.
            - For integer types (IS, SL, SS, UL, US), returns 0.
            - For decimal types (DS, FD, FL), returns 0.0.
            - For other byte types (OB, OW, UN), returns bytes('REDACTED', 'utf-8').
    """
    
    if vr in ["LO", "SH", "PN", "LT", "ST", "UT", "TM", "DT", "CS", "UI"]:
        # The VR is a string type
        return('REDACTED')
    elif vr in  ["IS", "SL", "SS", "UL", "US"]:
        # The VR is an integer type
        return(0)
    elif vr in ["DS", "FD", "FL"]:
        # The VR is a decimal type
        return(0.0)
    elif vr in ["OB", "OW", "UN"]:
        # The VR is other byte
        return(bytes('REDACTED', 'utf-8'))
    elif vr == 'DA':
        # The VR is a date
        return('00010101')
    else:
        print(f"The tag {tag} has VR {vr}, which is not handled by this function.")

def avoid_duplicates(path, counter=0):
    """
    Generate a unique filename by appending an increasing counter if the filename already exists.

    Args:
        file_path (str): The original file path.
        counter (int, optional): Counter for appending numbers. Defaults to 0.

    Returns:
        str: Unique filename.
    """
    if counter == 0:
        # Base case: check if the file already exists
        if not os.path.exists(path):
            return path

    # Generate a new filename by appending the counter
    new_path = f"{os.path.splitext(path)[0]}_{counter}{os.path.splitext(path)[1]}"

    # Check if the new filename already exists
    if os.path.exists(new_path):
        # If it exists, recursively call the function with an incremented counter
        return unique_filename(file_path, counter + 1)
    else:
        # If it doesn't exist, return the new filename
        return new_path

def remove_identifiers_from_dicom(dicom_file, subject_id=None):
    """
    Removes identifying information from a DICOM file and optionally sets a new subject ID.

    Args:
        dicom_file (str): Path to the DICOM file.
        subject_id (str, optional): New subject ID to assign. Defaults to None.
    """
    dicom_data = dcm.dcmread(dicom_file, force=True)
    
    # Extract DICOM metadata for filename
    modality = dicom_data.get("Modality","NA")
    seriesInstanceUID = dicom_data.get("SeriesInstanceUID","NA")
    instanceNumber = str(dicom_data.get("InstanceNumber","0"))

    # Generate a new filename based on DICOM metadata and a random suffix (sometimes two dicoms will have the same UID and instance number)
    filename = dicom_file.split('/')[-1]
    new_filename = avoid_duplicates(modality + "." + seriesInstanceUID + "." + instanceNumber + ".dcm")
    
    # Iterate through fields to scrub, specified by the id_fields.json file
    for field_tag, field_name in scrub_field_dict.items():
        # Convert hexadecimal values to integers
        x, y = map(lambda val: int(val, base=16), field_tag.split(","))
    
        # Check if field exists in DICOM data
        if (x, y) in dicom_data:
            value_rep = dicom_data[(x, y)].VR
            # Scrub the value
            dicom_data[(x, y)].value = vr_scrub(field_name, value_rep)
    
    # Assign new subject ID if provided
    if subject_id:
        dicom_data.PatientID = subject_id
                
    # Save modified DICOM data to file and rename
    try:
        dicom_data.save_as(dicom_file, write_like_original=False)
        os.rename(dicom_file, dicom_file.replace(filename, new_filename))
    except ValueError:
        print(f'DICOM file: {dicom_file} missing key fields for saving.')

def scrub_dicoms(session_path, subject_id=None):
    """
    Removes identifying information from all DICOM files in a directory and optionally sets a new subject ID.

    Args:
        session_path (str): Path to the scan session / directory containing DICOM files.
        subject_id (str, optional): New subject ID to assign. Defaults to None.
    """
    print(f'Scrubbing DICOM Files in {session_path}\n')
    
    dicom_number = 0
    
    # Iterate through all files and subdirectories within the session path
    for path, subdirs, files in os.walk(session_path):

        # Iterate through files ending with '.dcm'
        for file in [dicom for dicom in files if dicom.endswith('.dcm')]:
            
            # Scrub DICOM file
            remove_identifiers_from_dicom(dicom_file = os.path.join(path, file), subject_id=subject_id)
            dicom_number += 1

    print(f'{dicom_number} DICOM files scrubbed from the parent directory {session_path}\n')

if __name__ == "__main__":
    
    script_dir = os.path.abspath(os.path.dirname(__file__))
    with open(f'{script_dir}/id_fields.json', 'r') as json_file:
        scrub_field_dict = json.load(json_file)

    parser = argparse.ArgumentParser(description='Scrub identifying information from DICOM files.')
    parser.add_argument('scan_session_directory', nargs='?', default='.', help='Path to the directory containing DICOM files')
    parser.add_argument('-id', '--subject_id', default=None, help='Subject ID to assign to DICOM header')

    # Parse and extract arguments
    args = parser.parse_args()

    session_directory = args.scan_session_directory
    subject_id = args.subject_id

    # Scrub DICOM files
    scrub_dicoms(session_path=session_directory, subject_id=subject_id)
