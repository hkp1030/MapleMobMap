import csv
from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import parse

DATA_DIR = Path('data')


# mob 불러와서 리스트에 담은 후 리턴
def load_mob():
    mob_dict = defaultdict(dict)
    for path in (DATA_DIR / 'Mob').rglob('*.xml'):
        tree = parse(path)
        root = tree.getroot()

        # 해당 몬스터 아이디 구하기
        mob_id = int(root.attrib['name'].split('.')[0])

        # 경험치, 레벨 노드 찾기
        exp_node = root.find('./dir[@name="info"]/int32[@name="exp"]')
        level_node = root.find('./dir[@name="info"]/int32[@name="level"]')

        # 경험치, 레벨이 없는 몬스터는 패스
        if exp_node is None or level_node is None:
            continue

        # 해당 몬스터의 레벨과 경험치 구하기
        exp = int(exp_node.attrib['value'])
        level = int(level_node.attrib['value'])
        mob_dict[mob_id]['exp'] = exp
        mob_dict[mob_id]['level'] = level

    return mob_dict


def load_map_name():
    map_name_dict = defaultdict(dict)
    tree = parse(DATA_DIR / 'String/Map.img.xml')
    root = tree.getroot()

    for node in root.findall('./dir/dir'):
        map_id = int(node.attrib['name'])
        street_name_node = node.find('./string[@name="streetName"]')
        map_name_node = node.find('./string[@name="mapName"]')

        map_name_dict[map_id]['streetName'] = street_name_node.attrib['value'] if street_name_node is not None else ''
        map_name_dict[map_id]['mapName'] = map_name_node.attrib['value'] if map_name_node is not None else ''

    return map_name_dict


# map 불러와서 리스트에 담은 후 리턴
def load_map():
    map_dict = defaultdict(dict)

    mob_dict = load_mob()
    map_name_dict = load_map_name()

    for path in (DATA_DIR / 'Map').rglob('*.xml'):
        tree = parse(path)
        root = tree.getroot()

        # 해당 맵 아이디 구하기
        map_id = int(root.attrib['name'].split('.')[0])

        # 맵 이름이 없는 맵은 패스
        if map_id not in map_name_dict:
            continue

        # 몬스터 없는 맵이면 패스
        if root.find('./dir[@name="life"]//string[@name="type"][@value="m"]') is None:
            continue

        # 맵 이름과 거리 이름 구하기
        map_dict[map_id]['streetName'] = map_name_dict[map_id]['streetName']
        map_dict[map_id]['mapName'] = map_name_dict[map_id]['mapName']

        # 젠 속도 구하기
        mob_rate = float(root.find('./dir[@name="info"]/single[@name="mobRate"]').attrib['value'])
        map_dict[map_id]['mobRate'] = mob_rate

        # 해당 맵에 있는 몬스터 구하기
        mob_ids = [
            int(mob.find('string[@name="id"]').attrib['value'])
            for mob in root.findall('./dir[@name="life"]//string[@name="type"][@value="m"]/..')
        ]
        map_dict[map_id]['life'] = mob_ids

        # 평균 레벨, 맵 경험치 구하기
        sum_exp = 0
        sum_level = 0
        mob_count = 0
        for mob in mob_ids:
            if mob not in mob_dict:
                continue
            sum_exp += mob_dict[mob]['exp']
            sum_level += mob_dict[mob]['level']
            mob_count += 1

        if mob_count > 0:
            map_dict[map_id]['mapExp'] = int(sum_exp * mob_rate)
            map_dict[map_id]['avgLevel'] = int(sum_level / mob_count)
        else:
            map_dict[map_id]['mapExp'] = 0
            map_dict[map_id]['avgLevel'] = 0

    return map_dict


def main():
    map_list = load_map()

    with open('맵별 경험치 효율.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', '거리 이름', '맵 이름', '평균 레벨', '몬스터 수', '젠률', '경험치 효율'])
        for map_id, data in map_list.items():
            writer.writerow([map_id, data['streetName'], data['mapName'], data['avgLevel'], len(data['life']),
                             data['mobRate'], data['mapExp']])


if __name__ == '__main__':
    main()
