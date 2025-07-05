import csv
import os
from pathlib import Path
from xml.etree.ElementTree import parse

DATA_DIR = Path('data')


# mob 불러와서 리스트에 담은 후 리턴
def mob_load():
    mob_list = {}
    for top, dirs, files in os.walk(DATA_DIR / 'Mob'):
        for file in files:
            path = Path(top) / file
            if path.suffix != '.xml':
                continue

            tree = parse(path)
            root = tree.getroot()

            # 경험치, 레벨이 없는 몬스터는 패스~
            try:
                root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value']
                root.find('./imgdir[@name="info"]/int[@name="level"]').attrib['value']
            except AttributeError:
                continue

            # 해당 몬스터 아이디로 딕셔너리 생성
            mob_id = root.attrib['name'].split('.')[0]
            mob_list[mob_id] = {}

            # 해당 몬스터의 레벨과 경험치 구하기
            exp = int(root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value'])
            level = int(root.find('./imgdir[@name="info"]/int[@name="level"]').attrib['value'])
            mob_list[mob_id]['exp'] = exp
            mob_list[mob_id]['level'] = level

    return mob_list


# map 불러와서 리스트에 담은 후 리턴
def map_load():
    map_list = {}
    for top, dirs, files in os.walk(DATA_DIR / 'Map'):
        for file in files:
            path = Path(top) / file
            if path.suffix != '.xml':
                continue

            tree = parse(path)
            root = tree.getroot()

            # 몬스터 없는 맵이면 패스~
            try:
                root.find('./imgdir[@name="life"]/imgdir/string[@value="m"]').attrib
            except AttributeError:
                continue

            # 해당 맵 아이디로 딕셔너리 생성
            map_id = root.attrib['name'].split('.')[0]
            map_list[map_id] = {}

            # 젠 속도 구하기
            mob_rate = float(root.find('./imgdir[@name="info"]/float[@name="mobRate"]').attrib['value'])
            map_list[map_id]['mobRate'] = mob_rate

            # 해당 맵에 있는 몬스터 구하기
            life = root.findall('./imgdir[@name="life"]/imgdir')
            life = [mob for mob in life if mob.find('./string[@name="type"]').attrib['value'] == 'm']
            map_list[map_id]['life'] = [m.find('string[@name="id"]').attrib['value'] for m in life]

    return map_list


# 맵 리스트에 맵 이름 추가하여 리턴
def add_map_name(map_list):
    tree = parse(DATA_DIR / 'String/Map.img.xml')
    root = tree.getroot()

    for id, value in map_list.items():
        try:
            string_map = root.find('.//imgdir[@name="{}"]'.format(int(id)))
            value['streetName'] = string_map.find('./string[@name="streetName"]').attrib['value']
            value['mapName'] = string_map.find('./string[@name="mapName"]').attrib['value']
        except AttributeError:
            continue

    return map_list


def main():
    mob_list = mob_load()
    map_list = add_map_name(map_load())

    for id, value in map_list.items():
        try:
            sum_exp = 0
            sum_level = 0
            for mob in value['life']:
                sum_exp += mob_list[mob]['exp']
                sum_level += mob_list[mob]['level']
            value['mapExp'] = int(sum_exp * value['mobRate'])
            value['avgLevel'] = int(sum_level / len(value['life']))
        except KeyError:
            continue

    with open('맵별 경험치 효율.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['streetName', 'mapName', 'avgLevel', 'mapExp'])
        for id, value in map_list.items():
            try:
                writer.writerow([value['streetName'], value['mapName'], value['avgLevel'], value['mapExp']])
            except KeyError:
                continue


if __name__ == '__main__':
    main()
