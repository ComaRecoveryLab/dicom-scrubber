#!/usr/bin/env python
# coding: utf-8

import os
import json
import argparse

import pydicom as dcm


def check_dicoms(session_path):
    print(f'Checking {session_path} for DICOMs...')

    dicom_output_dict = {}
    for field_tag, field_name in scrub_field_dict.items():
        dicom_output_dict[field_name] = set()

    num_dicoms = 0
    # Iterate through all files and subdirectories within the session path
    for path, subdirs, files in os.walk(session_path):
        for file in [dicom for dicom in files if dicom.endswith('.dcm')]:
            num_dicoms += 1
            dicom_data = dcm.dcmread(os.path.join(path, file), force=True)
            # Iterate through fields in the scrub_field_dict and print values
            for field_tag, field_name in scrub_field_dict.items():
                # Convert hexadecimal values to integers and check for field in the DICOM header
                x, y = map(lambda val: int(val, base=16), field_tag.split(","))
                if (x, y) in dicom_data:
                    # Obtain the field value and append if new:
                    val = dicom_data[(x, y)].value
                    dicom_output_dict[field_name].add(str(val))


    print(f'{num_dicoms} DICOMs found: \n')
    for field_name, value_list in dicom_output_dict.items():
        field_vals = str(list(value_list))
        print(f'{field_name}: {field_vals}')


if __name__ == "__main__":
    
    script_dir = os.path.abspath(os.path.dirname(__file__))
    with open(f'{script_dir}/id_fields.json', 'r') as json_file:
        scrub_field_dict = json.load(json_file)
    
    parser = argparse.ArgumentParser(description='Check DICOM fields.')
    parser.add_argument('scan_session_directory', nargs='?', default='.', help='Path to the directory containing DICOM files')

    # Parse arguments
    args = parser.parse_args()

    # Extract arguments
    session_directory = args.scan_session_directory

    check_dicoms(session_directory)

