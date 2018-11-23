# encoding: utf-8
import json

def load_json(jsonfile):
    '''读取json中的数据'''
    try:
        with open(jsonfile, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except IOError:
        raise

def save_json(data, savepath):
    '''以json格式保存数据到目标路径'''
    with open(savepath, 'w', encoding='utf-8') as f:
        jsonD = json.dumps(data, indent=4)
        f.write(jsonD)
