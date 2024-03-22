#!/usr/bin/env python
# coding: utf-8

# In[8]:


import os
import json
import argparse

import pydicom as dcm


# In[1]:


def check_dicoms(session_path, dicom_field_config):
    print(f'Checking {session_path} for DICOMs...')
    # Load scrub field configurations from JSON file
    with open(dicom_field_config, 'r') as json_file:
        scrub_field_dict = json.load(json_file)

    dicom_output_dict = {}
    for field_name, field_tag in scrub_field_dict.items():
        dicom_output_dict[field_name] = set()

    num_dicoms = 0
    # Iterate through all files and subdirectories within the session path
    for path, subdirs, files in os.walk(session_path):
        # Iterate through files ending with '.dcm'
        for file in [dicom for dicom in files if dicom.endswith('.dcm')]:
            num_dicoms += 1
            # Read DICOM file
            dicom_data = dcm.dcmread(os.path.join(path, file))
            # Iterate through fields in the scrub_field_dict and print values
            for field_name, field_tag in scrub_field_dict.items():
                # Convert hexadecimal values to integers
                x, y = map(lambda val: int(val, base=16), field_tag.split(","))
                # Check if field exists in DICOM data
                if (x, y) in dicom_data:
                    # Obtain the field value:
                    dicom_output_dict[field_name].add(dicom_data[(x, y)].value)

    print(f'{num_dicoms} DICOMs found: \n')
    for field_name, value_list in dicom_output_dict.items():
        field_vals = str(list(value_list))
        print(f'{field_name}: {field_vals}')


# In[ ]:


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Check DICOM fields.')
    parser.add_argument('-p', '--session_directory', default='.', help='Path to the session directory containing DICOM files')
    parser.add_argument('-c', '--dicom_field_config', default='./scrub_fields.json', help='Path to the JSON file containing DICOM field configurations')

    # Parse arguments
    args = parser.parse_args()

    # Extract arguments
    session_directory = args.session_directory
    dicom_field_config = args.dicom_field_config

    check_dicoms(session_directory, dicom_field_config)

