import os
import sys
import json

class chart:
    def __init__(self):
        self.meta = {}

class malody(chart):
    def __init__(self):
        super().__init__()
        self.note = []
        self.time = []
        self.effect = []
        self.extra = {}

class mania(chart):
    def __init__(self):
        super().__init__()


def readFile(file_path):
    if not file_path.endswith(".mc"):  # 只处理 .mc 文件
        return None
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File {file_path} does not exist.")
        return None
    except json.JSONDecodeError:
        print(f"File {file_path} is not a legal json file.")
        return None
    except Exception as e:
        print(f"Error occurs: {e}.")
        return None

def readFolder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"{folder_path} is not a legal folder.")
        return []
    
    items = os.listdir(folder_path)
    files = []

    for item in items:
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            files.append(readFile(item_path))

    return files
    
def extractData(object):
    if isinstance(object, dict):
        chart = malody()
        chart.note = object['note']
        chart.meta = object['meta']
        chart.time = object['time']
        if 'extra' in object:
            chart.extra = object['extra']
        if 'effect' in object:
            chart.effect = object['effect']
        return chart
    else:
        return None

def main():
    if len(sys.argv) > 1:
        inputFile, inputChart = [], []
        for index in range(1, len(sys.argv)):
            file_path = sys.argv[index]
            if os.path.isdir(file_path):
                tmp = readFolder(file_path)
            else:
                tmp = readFile(file_path)

            inputFile.extend(tmp)
            # inputFile = [readFile(sys.argv[index]) for index in range(1, len(sys.argv))]
            inputChart = [extractData(data) for data in inputFile if data is not None]
    else:
        print("Please input a file.")
    
    if inputChart:
        # print(sys.argv[1])
        # print(inputChart[0].note)
        print(len(inputChart))
    else:
        print("No valid charts found.")

if  __name__ == '__main__':
    main()