#!/usr/bin/env python
# coding: utf-8

# In[6]:


import argparse
import os
import json
import random
import string

import pydicom as dcm


# In[3]:


def vr_scrub(vr):
    if vr in ["LO", "SH", "PN", "LT", "ST", "UT", "DA", "TM", "DT", "CS", "UI"]:
        # The VR is a string type, so convert the new value to a string
        return('REDACTED')
    elif vr in  ["IS", "SL", "SS", "UL", "US"]:
        # The VR is an integer type, so convert the new value to an integer
        return(0)
    elif vr in ["DS", "FD", "FL"]:
        # The VR is a decimal type, so convert the new value to a float
        return(0.0)
    elif vr in ["OB", "OW", "UN"]:
        # The VR is other byte, so convert the new value to bytes
        return(bytes('REDACTED', 'utf-8'))
    else:
        print(f"The tag {tag} has VR {vr}, which is not handled by this function.")


# In[4]:


def remove_identifiers_from_dicom(dicom_file, subject_id=None):
    """
    Removes identifying information from a DICOM file and optionally sets a new subject ID.

    Args:
        dicom_file (str): Path to the DICOM file.
        subject_id (str, optional): New subject ID to assign. Defaults to None.
    """
    dicom_data = dcm.dcmread(dicom_file)
    
    # Extract DICOM metadata for filename
    modality = dicom_data.get("Modality","NA")
    seriesInstanceUID = dicom_data.get("SeriesInstanceUID","NA")
    instanceNumber = str(dicom_data.get("InstanceNumber","0"))

    # Generate a new filename based on DICOM metadata and a random suffix (sometimes two dicoms will have the same UID and instance number)
    filename = dicom_file.split('/')[-1]
    new_filename = modality + "." + seriesInstanceUID + "." + instanceNumber + "." + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + ".dcm"
    
    # Iterate through fields to scrub, specified by the scrub_fields.json file
    for field in scrub_fields:
        # Convert hexadecimal values to integers
        x, y = map(lambda val: int(val, base=16), field.split(","))
    
        # Check if field exists in DICOM data
        if (x, y) in dicom_data:
            # Get value representation of the field
            value_rep = dicom_data[(x, y)].VR
            # Scrub the value
            dicom_data[(x, y)].value = vr_scrub(value_rep)
    
    # Assign new subject ID if provided
    if subject_id:
        dicom_data.PatientID = subject_id
                
    # Save modified DICOM data to file and rename
    dicom_data.save_as(dicom_file, write_like_original=False)
    os.rename(dicom_file, dicom_file.replace(filename, new_filename))


# In[5]:


def scrub_dicoms(session_path, subject_id=None):
    dicom_number = 0
    
    # Iterate through all files and subdirectories within the session path
    for path, subdirs, files in os.walk(session_path):

        # Iterate through files ending with '.dcm'
        for file in [dicom for dicom in files if dicom.endswith('.dcm')]:
            
            # Scrub DICOM file
            remove_identifiers_from_dicom(dicom_file = os.path.join(path, file), subject_id=subject_id)
            dicom_number += 1

    print(f'{dicom_number} DICOM files scrubbed from the parent directory {session_path}\n')


# In[ ]:


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Scrub identifying information from DICOM files.')
    parser.add_argument('-p', '--session_directory', default='.', help='Path to the session directory containing DICOM files')
    parser.add_argument('-id', '--subject_id', default=None, help='Subject ID to assign to DICOM header')
    parser.add_argument('-c', '--dicom_field_config', default='./scrub_fields.json', help='Path to the JSON file containing fields to scrub')

    # Parse arguments
    args = parser.parse_args()

    # Extract arguments
    session_directory = args.session_directory
    subject_id = args.subject_id
    dicom_field_config = args.dicom_field_config

    # Load scrub field configurations from JSON file
    with open(dicom_field_config, 'r') as json_file:
        scrub_field_dict = json.load(json_file)
    
    scrub_fields = list(scrub_field_dict.values())

    # Scrub DICOM files
    scrub_dicoms(session_path=session_directory, subject_id=subject_id)

