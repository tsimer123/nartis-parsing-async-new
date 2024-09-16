import json
from pathlib import Path

# from config import localpath_meter_list


def write_file(host, data: dict):
    files_name = f'{host}_{data["command"]}.json'
    # name_file = Path('src', 'output_files', 'json', files_name)
    name_file = Path('output_files', 'json', files_name)
    # data.encode(encoding = 'UTF-8', errors = 'strict')
    with open(name_file, 'w') as write_file:
        json.dump(data, write_file)


# def write_file_csv(name: str, list_meters: list):
#     files_name = f'{name}.csv'
#     name_file = Path(localpath_meter_list, files_name)
#     with open(name_file, 'w', encoding='utf-8') as write_file:
#         for line in list_meters:
#             write_file.write(';'.join(line) + '\n')


# def read_file(files_name: str):
#     name_file = Path(localpath_meter_list, f'{files_name}.csv')
#     lines = []
#     with open(name_file) as f:
#         lines = f.readlines()
#     return lines
