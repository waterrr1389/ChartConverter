import os
import sys
import json

class chart:
    def __init__(self):
        self.meta = {}
        self.SV = False

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
    
def process(chart):
    time = chart.time
    note = chart.note 
    meta = chart.meta
    if meta['mode'] != 0:
        print(f'Chart {meta['song']['title']} is not a key mode chart.Ignore.')
    else:
        title = meta['song']['title']
        artist = meta['song']['artist']
        creator = meta['creator']
        version = meta['version']
        bgimg = meta['background']
        keys = meta['mode_ext']['column']
        preview = meta.get('preview', 0)

        # either the first or the last note store the sound
        if note[0].get('type') == 1:
            soundnote = note[0]
        elif note[-1].get('type') == 1:
            soundnote = note[-1]
        print(soundnote)
        # osu! global offset is opposite to the chart offset
        sound = -soundnote['sound']
        offset = soundnote.get('offset', 0)
        # vol = soundnote['vol'] useless key

        if chart.effect != None:
            chart.SV = True
            effect = chart.effect

        content = ['osu file format v14',
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
                    '//Background and Video events',
                    f'0,0,\"{bgimg}\",0,0',
                    '',
                    '[TimingPoints]',
                    '']
        
        file_name = f'{artist} - {title} [{version}]'
        with open(file_name, 'w', encoding='utf-8') as f:
            
            f.write('\n'.join(content))

            absbeat = lambda beat: beat[0] + beat[1] / beat[2]
            current_time = offset
            prev_beat = 0
            time_events = []
            time_per_beat = 60 * 1000 / time[0]['bpm']

            for t in time:
                current_beat = absbeat(t['beat'])

                time_diff = (current_beat - prev_beat) * time_per_beat  
                current_time += time_diff 

                time_per_beat = 60 * 1000 / t['bpm']

                time_events.append({'bpm': t['bpm'], 'absolute_beat': current_beat})
                f.write(f'{int(current_time)},{time_per_beat},4,1,0,0,1,0\n')
                prev_beat = current_beat 

            # if chart.SV:
                


def main():
    if len(sys.argv) > 1:
        inputFile, inputChart = [], []
        for path in sys.argv[1:]:
            if os.path.isdir(path):
                inputFile.extend(readFolder(path))
            else:
                file_data = readFile(path)
                if file_data:
                    inputFile.append(file_data)

            inputChart = [extractData(data) for data in inputFile if data is not None]
        for chart in inputChart:
            process(chart)
    else:
        print("Please input a file.")
    
    if inputChart:
        print(len(inputChart))
    else:
        print("No valid charts found.")

if  __name__ == '__main__':
    main()