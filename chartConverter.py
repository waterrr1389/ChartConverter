import os
import sys
import json
import bisect
import logging

# Configure logging for error reporting and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Chart:
    """Base class for chart structure."""
    def __init__(self):
        self.meta = {}
        self.SV = False

class Malody(Chart):
    """Malody chart representation."""
    def __init__(self):
        super().__init__()
        self.note = []
        self.time = []
        self.effect = []
        self.extra = {}

class Mania(Chart):
    """Mania chart representation."""
    def __init__(self):
        super().__init__()

def read_file(file_path):
    """Reads the file and returns the data as a dictionary."""
    if not file_path.endswith(".mc"):  # Process only .mc files
        logging.warning(f"File {file_path} is not a valid .mc file.")
        return None

    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        logging.error(f"File {file_path} does not exist.")
    except json.JSONDecodeError:
        logging.error(f"File {file_path} is not a valid JSON file.")
    except Exception as e:
        logging.error(f"Error occurred while reading {file_path}: {e}")
    return None

def read_folder(folder_path):
    """Reads all files in a folder and returns a list of valid files."""
    if not os.path.isdir(folder_path):
        logging.error(f"{folder_path} is not a valid directory.")
        return []

    files = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            file_data = read_file(item_path)
            if file_data:
                files.append(file_data)
    return files

def extract_data(data):
    """Extracts chart data from a dictionary and returns a Malody object."""
    if isinstance(data, dict):
        chart = Malody()
        chart.note = data.get('note', [])
        chart.meta = data.get('meta', {})
        chart.time = data.get('time', [])
        chart.effect = data.get('effect', [])
        chart.extra = data.get('extra', {})
        return chart
    return None

def process(chart):
    """Processes the chart and generates osu! formatted content."""
    meta = chart.meta
    notes = chart.note
    time = chart.time
    if meta.get('mode', None) != 0:
        logging.info(f"Chart {meta['song']['title']} is not a key mode chart. Skipping.")
        return

    # Extract relevant metadata
    title = meta['song']['title']
    artist = meta['song']['artist']
    creator = meta['creator']
    version = meta['version']
    bgimg = meta.get('background', '')
    keys = meta['mode_ext']['column']
    preview = meta.get('preview', 0)

    # Identify the sound note
    soundnote = next((note for note in [notes[0], notes[-1]] if note.get('type') == 1), None)
    if soundnote:
        notes.remove(soundnote)
        sound = soundnote['sound']
        offset = -soundnote.get('offset', 0)
    else:
        logging.warning(f"No sound note found in chart {title}.")
        return

    # Handle special effects (SV)
    if chart.effect:
        chart.SV = True
        effect = chart.effect

    # Prepare content to write to .osu file
    content = [
        'osu file format v14',
        '',
        '[General]',
        f'AudioFilename: {sound}',
        'AudioLeadIn: 0',
        f'PreviewTime: {preview}',
        'Countdown: 0',
        'SampleSet: Normal',
        'StackLeniency: 0.7',
        'Mode: 3',
        'LetterboxInBreaks: 0',
        'SpecialStyle: 0',
        'WidescreenStoryboard: 0',
        '',
        '[Editor]',
        'DistanceSpacing: 1.2',
        'BeatDivisor: 4',
        'GridSize: 8',
        'TimelineZoom: 2.4',
        '',
        '[Metadata]',
        f'Title:{title}',
        f'TitleUnicode:{title}',
        f'Artist:{artist}',
        f'ArtistUnicode:{artist}',
        f'Creator:{creator}',
        f'Version:{version}',
        'Source:Malody',
        'Tags:Malody Convert',
        'BeatmapID:0',
        'BeatmapSetID:-1',
        '',
        '[Difficulty]',
        'HPDrainRate:8',
        f'CircleSize:{keys}',
        'OverallDifficulty:8',
        'ApproachRate:5',
        'SliderMultiplier:1.4',
        'SliderTickRate:1',
        '',
        '[Events]',
        f'0,0,"{bgimg}",0,0',
        '\n'
    ]

    # Write to .osu file
    file_name = f'{artist} - {title} [{version}].osu'
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
        write_timing_points(f, time, offset)
        write_hit_objects(f, notes, time, keys)

def abs_beat(beat):
    return beat[0] + beat[1] / beat[2]

def note_column(column, keys):
    return int(512 * (2 * column + 1) / (2 * keys))
    
def write_timing_points(f, time, offset):
    """Writes timing points to the file."""
    
    current_time = offset
    prev_beat = 0
    time_per_beat = 60 * 1000 / time[0]['bpm']
    timing = ['[TimingPoints]']

    for t in time:
        current_beat = abs_beat(t['beat'])
        time_diff = (current_beat - prev_beat) * time_per_beat
        current_time += time_diff
        time_per_beat = 60 * 1000 / t['bpm']
        timing.append(f'{int(current_time)},{time_per_beat},4,1,0,0,1,0')
        prev_beat = current_beat

    timing.append('\n')

    f.write('\n'.join(timing))

def write_hit_objects(f, notes, time, keys):
    """Writes hit objects to the file."""
    hitobjects = ['[HitObjects]']
    timing_beats = [abs_beat(t["beat"]) for t in time]
    current_time = 0
    prev_beat = 0

    for note in notes:
        note_beat = abs_beat(note['beat'])
        idx = bisect.bisect_right(timing_beats, note_beat) - 1
        idx = max(0, idx)
        bpm = time[idx]["bpm"]
        time_per_beat = 60000 / bpm
        current_time += (note_beat - prev_beat) * time_per_beat
        column = note_column(note['column'], keys)
        endbeat = note.get('endbeat', None)

        if endbeat:  # Long note
            endtime = current_time + (abs_beat(endbeat) - note_beat) * time_per_beat
            hitobjects.append(f'{column},192,{int(current_time)},128,0,{int(endtime)}:0:0:0:0')
        else:
            hitobjects.append(f'{int(column)},192,{current_time},1,0,0:0:0:0:')

        prev_beat = note_beat

    f.write('\n'.join(hitobjects))

def main():
    """Main function to handle input and processing."""
    if len(sys.argv) > 1:
        input_file_data, input_chart_data = [], []
        for path in sys.argv[1:]:
            if os.path.isdir(path):
                input_file_data.extend(read_folder(path))
            else:
                file_data = read_file(path)
                if file_data:
                    input_file_data.append(file_data)

        input_chart_data = [extract_data(data) for data in input_file_data if data is not None]
        for chart in input_chart_data:
            process(chart)
    else:
        print("Please input a file.")

if __name__ == '__main__':
    main()

# import os
# import sys
# import json
# import bisect

# class chart:
#     def __init__(self):
#         self.meta = {}
#         self.SV = False

# class malody(chart):
#     def __init__(self):
#         super().__init__()
#         self.note = []
#         self.time = []
#         self.effect = []
#         self.extra = {}

# class mania(chart):
#     def __init__(self):
#         super().__init__()


# def readFile(file_path):
#     if not file_path.endswith(".mc"):  # 只处理 .mc 文件
#         return None
#     try:
#         with open(file_path, 'r', encoding="utf-8") as file:
#             data = json.load(file)
#         return data
#     except FileNotFoundError:
#         print(f"File {file_path} does not exist.")
#         return None
#     except json.JSONDecodeError:
#         print(f"File {file_path} is not a legal json file.")
#         return None
#     except Exception as e:
#         print(f"Error occurs: {e}.")
#         return None

# def readFolder(folder_path):
#     if not os.path.isdir(folder_path):
#         print(f"{folder_path} is not a legal folder.")
#         return []
    
#     items = os.listdir(folder_path)
#     files = []

#     for item in items:
#         item_path = os.path.join(folder_path, item)
#         if os.path.isfile(item_path):
#             files.append(readFile(item_path))

#     return files
    
# def extractData(object):
#     if isinstance(object, dict):
#         chart = malody()
#         chart.note = object['note']
#         chart.meta = object['meta']
#         chart.time = object['time']
#         if 'extra' in object:
#             chart.extra = object['extra']
#         if 'effect' in object:
#             chart.effect = object['effect']
#         return chart
#     else:
#         return None
    
# def process(chart):
#     time = chart.time
#     notes = chart.note 
#     meta = chart.meta
#     if meta['mode'] != 0:
#         print(f'Chart {meta['song']['title']} is not a key mode chart.Ignore.')
#     else:
#         title = meta['song']['title']
#         artist = meta['song']['artist']
#         creator = meta['creator']
#         version = meta['version']
#         bgimg = meta['background']
#         keys = meta['mode_ext']['column']
#         preview = meta.get('preview', 0)

#         # either the first or the last note store the sound
#         if notes[0].get('type') == 1:
#             soundnote = notes[0]
#         elif notes[-1].get('type') == 1:
#             soundnote = notes[-1]
#         if soundnote in notes:
#             notes.pop(notes.index(soundnote))
#         # osu! global offset is opposite to the chart offset
#         sound = soundnote['sound']
#         offset = -soundnote.get('offset', 0)
#         # vol = soundnote['vol'] useless key

#         if chart.effect != None:
#             chart.SV = True
#             effect = chart.effect

#         content = ['osu file format v14',
#                     '',
#                     '[General]',
#                     f'AudioFilename: {sound}',
#                     'AudioLeadIn: 0',
#                     f'PreviewTime: {preview}',
#                     'Countdown: 0',
#                     'SampleSet: Normal',
#                     'StackLeniency: 0.7',
#                     'Mode: 3',
#                     'LetterboxInBreaks: 0',
#                     'SpecialStyle: 0',
#                     'WidescreenStoryboard: 0',
#                     '',
#                     '[Editor]',
#                     'DistanceSpacing: 1.2',
#                     'BeatDivisor: 4',
#                     'GridSize: 8',
#                     'TimelineZoom: 2.4',
#                     '',
#                     '[Metadata]',
#                     f'Title:{title}',
#                     f'TitleUnicode:{title}',
#                     f'Artist:{artist}',
#                     f'ArtistUnicode:{artist}',
#                     f'Creator:{creator}',
#                     f'Version:{version}',
#                     'Source:Malody',
#                     'Tags:Malody Convert',
#                     'BeatmapID:0',
#                     'BeatmapSetID:-1',
#                     '',
#                     '[Difficulty]',
#                     'HPDrainRate:8',
#                     f'CircleSize:{keys}',
#                     'OverallDifficulty:8',
#                     'ApproachRate:5',
#                     'SliderMultiplier:1.4',
#                     'SliderTickRate:1',
#                     '',
#                     '[Events]',
#                     '//Background and Video events',
#                     f'0,0,\"{bgimg}\",0,0',
#                     '',
#                     '[TimingPoints]',
#                     '']
        
#         file_name = f'{artist} - {title} [{version}.osu'
#         with open(file_name, 'w', encoding='utf-8') as f:
            
#             f.write('\n'.join(content))

#             abs_beat = lambda beat: beat[0] + beat[1] / beat[2]
#             current_time = offset
#             prev_beat = 0
#             timing = []
#             time_per_beat = 60 * 1000 / time[0]['bpm']

#             for t in time:
#                 current_beat = abs_beat(t['beat'])

#                 time_diff = (current_beat - prev_beat) * time_per_beat  
#                 current_time += time_diff 

#                 time_per_beat = 60 * 1000 / t['bpm']

#                 timing.append(f'{int(current_time)},{time_per_beat},4,1,0,0,1,0')
#                 prev_beat = current_beat 

#             f.write('\n'.join(timing))

#             f.write('\n\n[HitObjects]\n')
#             col = lambda column, keys: int(512*(2*column+1)/(2*keys))
#             hitobjects = []
#             timing_beats = [abs_beat(t["beat"]) for t in time]
#             current_time = offset
#             prev_beat = 0
#             print(len(notes))
#             print(notes[0]['column'])
#             for note in notes:
#                 current_beat = abs_beat(note['beat'])
#                 idx = bisect.bisect_right(timing_beats, current_beat) - 1
#                 idx = max(0, idx)  # 确保 idx 不会小于 0
#                 # 获取对应的 BPM
#                 bpm = time[idx]["bpm"]
#                 time_per_beat = 60000 / bpm
#                 current_time += (current_beat - prev_beat) * time_per_beat
#                 column = col(note['column'], keys)
#                 endbeat = note.get('endbeat', None)
                
#                 if endbeat != None: # current note is long note
#                     endtime = current_time + (abs_beat(endbeat) - current_beat) * time_per_beat
#                     hitobjects.append(f'{column},192,{int(current_time)},128,0,{int(endtime)}:0:0:0:0')
#                 else:
#                     hitobjects.append(f'{int(column)},192,{current_time},1,0,0:0:0:0:')

#                 prev_beat = current_beat

#             f.write('\n'.join(hitobjects))


                


# def main():
#     if len(sys.argv) > 1:
#         inputFile, inputChart = [], []
#         for path in sys.argv[1:]:
#             if os.path.isdir(path):
#                 inputFile.extend(readFolder(path))
#             else:
#                 file_data = readFile(path)
#                 if file_data:
#                     inputFile.append(file_data)

#             inputChart = [extractData(data) for data in inputFile if data is not None]
#         for chart in inputChart:
#             process(chart)
#     else:
#         print("Please input a file.")
    
#     if inputChart:
#         print(len(inputChart))
#     else:
#         print("No valid charts found.")

# if  __name__ == '__main__':
#     main()