# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 20:06:31 2024

@author: edgar
"""

import os
from os.path import join
from os import listdir
import json
import pandas as pd

def compile_json_to_dataframe(directory):
    """
    Compiles JSON files in the specified directory into a DataFrame.

    Args:
        directory (str): Path to the directory containing JSON files.

    Returns:
        tuple: A DataFrame containing the compiled data and a list of all data.
    """
    # List to hold the data from all JSON files
    all_data = []
    
    subdirs = listdir(directory)
    # print(subdirs)

    # Iterate through all files in the specified directory
    for subdir in subdirs:
        for talent in listdir(join(directory, subdir)):
            files = listdir(join(directory, subdir, talent))
            print(f"{talent}: {len(files)}")
            for filename in files:
                if filename.endswith(".json"):
                    file_path = join(directory, subdir, talent, filename)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_data.append(data)

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(all_data)
    
    return df, all_data

if __name__ == "__main__":
    # Specify the directory containing the JSON files
    json_directory = "scraped_images"  # Replace with your directory
    
    # Compile the JSON files into a DataFrame
    dataframe, all_data = compile_json_to_dataframe(json_directory)
    
    # Display the DataFrame
    print(dataframe)

    # Save the DataFrame to a CSV file (optional)
    dataframe.to_csv('compiled_data.csv', index=False)

#%%
# names = []
# for i in all_data:
#     if len(i['character_tags']) == 1 and i['character_tags'][0] not in names:
#         names.append(i['character_tags'][0])

#%%
def count_json_files_in_subdirs(base_dir):
    """
    Counts the number of JSON files in subdirectories.

    Args:
        base_dir (str): Path to the base directory.

    Returns:
        DataFrame: A DataFrame containing the counts of JSON files.
    """
    data = []

    # Traverse the directory structure
    for subdir_1 in os.listdir(base_dir):
        subdir_1_path = os.path.join(base_dir, subdir_1)
        if os.path.isdir(subdir_1_path):
            for subdir_2 in os.listdir(subdir_1_path):
                subdir_2_path = os.path.join(subdir_1_path, subdir_2)
                if os.path.isdir(subdir_2_path):
                    # Count the number of JSON files in subdir_2
                    json_count = len([f for f in os.listdir(subdir_2_path) if f.endswith('.json')])
                    # Append the information to the list of dictionaries
                    data.append({
                        'name': subdir_2,
                        'count': json_count,
                        'gen': subdir_1
                    })

    # Transform the list of dictionaries into a DataFrame
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    # Specify the base directory containing the 'scraped_images' folder
    base_directory = "scraped_images"
    
    # Get the DataFrame with the JSON file counts
    json_counts_df = count_json_files_in_subdirs(base_directory)
    
    # Display the DataFrame
    print(json_counts_df)

    # Optionally, save the DataFrame to a CSV file
    json_counts_df.to_csv("json_counts.csv", index=False)
#%%
def count_json_files(base_dir):
    """
    Counts the number of JSON files and their ratings in subdirectories.

    Args:
        base_dir (str): Path to the base directory.

    Returns:
        DataFrame: A DataFrame containing the counts of JSON files and their ratings.
    """
    data = []

    # First pass: Traverse the directory structure to count JSON files
    for subdir_1 in os.listdir(base_dir):
        subdir_1_path = os.path.join(base_dir, subdir_1)
        if os.path.isdir(subdir_1_path):
            for subdir_2 in os.listdir(subdir_1_path):
                subdir_2_path = os.path.join(subdir_1_path, subdir_2)
                if os.path.isdir(subdir_2_path):
                    # Count the number of JSON files in subdir_2
                    json_files = [f for f in os.listdir(subdir_2_path) if f.endswith('.json')]
                    json_count = len(json_files)

                    # Append the initial information to the list of dictionaries
                    data.append({
                        'name': subdir_2,
                        'count': json_count,
                        'gen': subdir_1,
                        'Explicit': 0,
                        'General': 0,
                        'Questionable': 0,
                        'Sensitive': 0
                    })

    # Transform the list of dictionaries into a DataFrame
    df = pd.DataFrame(data)

    # Second pass: Traverse the directory structure to update rating counts
    for subdir_1 in os.listdir(base_dir):
        subdir_1_path = os.path.join(base_dir, subdir_1)
        if os.path.isdir(subdir_1_path):
            for subdir_2 in os.listdir(subdir_1_path):
                subdir_2_path = os.path.join(subdir_1_path, subdir_2)
                if os.path.isdir(subdir_2_path):
                    # Traverse each JSON file to count ratings
                    for json_file in os.listdir(subdir_2_path):
                        if json_file.endswith('.json'):
                            json_file_path = os.path.join(subdir_2_path, json_file)
                            with open(json_file_path, 'r') as f:
                                json_data = json.load(f)
                                rating = json_data.get("rating")
                                if rating in ["Explicit", "General", "Questionable", "Sensitive"]:
                                    # Increment the appropriate rating count in the DataFrame
                                    df.loc[df['name'] == subdir_2, rating] += 1

    return df

if __name__ == "__main__":
    # Specify the base directory containing the 'scraped_images' folder
    base_directory = "scraped_images"
    
    # Get the DataFrame with the JSON file counts and rating counts
    json_counts_df = count_json_files(base_directory)
    
    # Display the DataFrame
    print(json_counts_df)

    # Optionally, save the DataFrame to a CSV file
    json_counts_df.to_csv("json_counts_with_ratings.csv", index=False)

