import csv
from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import parse

DATA_DIR = Path('data')

SPAWN_TICK = 7.0  # 리젠 틱 주기 (초)
TICK_ALIGN_DELAY = 3.5  # 리젠 완료 후 다음 틱까지 기대 대기 시간 (SPAWN_TICK / 2)
REGEN_MULTIPLIER = 1.65  # 리젠 대기 uniform(1.3, 2.0) x mobTime 의 기대 배수
CAPACITY_CONSTANT = 0.0000078125  # BMS CLifePool::Init 의 수용량 상수 (= 1/128000)


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


# info 노드에서 정수 값 구하기 (없으면 기본값)
def find_info_int(root, name, default=0):
    node = root.find(f'./dir[@name="info"]/int32[@name="{name}"]')
    return int(node.attrib['value']) if node is not None else default


# 발판(foothold) 경계 사각형으로 맵 크기 계산 (BMS CFieldMan::RestoreFoothold 재현)
def calc_map_size(root):
    mbr_left = float('inf')
    mbr_top = float('inf')
    mbr_right = float('-inf')
    mbr_bottom = float('-inf')

    for fh in root.findall('./dir[@name="foothold"]//int32[@name="x1"]/..'):
        x1 = int(fh.find('int32[@name="x1"]').attrib['value'])
        y1 = int(fh.find('int32[@name="y1"]').attrib['value'])
        x2 = int(fh.find('int32[@name="x2"]').attrib['value'])
        y2 = int(fh.find('int32[@name="y2"]').attrib['value'])
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)

        mbr_left = min(mbr_left, left + 30)
        mbr_right = max(mbr_right, right - 30)
        mbr_top = min(mbr_top, top - 300)
        # 걸을 수 없는 수직 벽은 bottom 갱신에서 제외
        if left != right:
            mbr_bottom = max(mbr_bottom, bottom + 10)

    # 발판이 없거나 수직 벽뿐인 맵은 크기 계산 불가
    if mbr_left == float('inf') or mbr_bottom == float('-inf'):
        return None

    # VR 경계로 클램프 (값이 0이거나 없으면 미적용)
    vr_left = find_info_int(root, 'VRLeft')
    vr_right = find_info_int(root, 'VRRight')
    vr_top = find_info_int(root, 'VRTop')
    vr_bottom = find_info_int(root, 'VRBottom')
    if vr_left != 0 and mbr_left < vr_left + 20:
        mbr_left = vr_left + 20
    if vr_right != 0 and mbr_right > vr_right - 20:
        mbr_right = vr_right - 20
    if vr_top != 0 and mbr_top < vr_top + 65:
        mbr_top = vr_top + 65
    if vr_bottom != 0 and mbr_bottom > vr_bottom:
        mbr_bottom = vr_bottom

    # inflate(10, 10)
    mbr_left -= 10
    mbr_top -= 10
    mbr_right += 10
    mbr_bottom += 10

    return mbr_right - mbr_left, mbr_bottom - mbr_top


# 맵의 몹 수용량 계산 (BMS CLifePool::Init 재현)
def calc_mob_capacity(root, mob_rate):
    # 고정 수용량이 지정된 맵은 그 값을 그대로 사용
    fixed_capacity = find_info_int(root, 'fixedMobCapacity')
    if fixed_capacity > 0:
        return fixed_capacity

    map_size = calc_map_size(root)
    map_width, map_height = map_size if map_size is not None else (0, 0)
    width = max(800, map_width)
    height = max(600, map_height - 450)
    return max(1, min(40, int(width * height * mob_rate * CAPACITY_CONSTANT)))


# life 노드에서 몬스터 스폰 포인트 (몬스터 아이디, 리젠 주기) 리스트 구하기
def parse_spawn_points(root):
    spawn_points = []
    for mob in root.findall('./dir[@name="life"]//string[@name="type"][@value="m"]/..'):
        mob_id = int(mob.find('string[@name="id"]').attrib['value'])
        mob_time_node = mob.find('int32[@name="mobTime"]')
        mob_time = int(mob_time_node.attrib['value']) if mob_time_node is not None else 0
        spawn_points.append((mob_id, mob_time))
    return spawn_points


# 솔로 플레이 + 스폰 즉시 처치 가정의 정상상태 분당 경험치 계산
def calc_exp_per_minute(spawn_points, mob_dict, capacity):
    normal_exps = []  # mobTime == 0: 7초 틱마다 수용량 한도까지 스폰
    timed_spawns = []  # mobTime > 0: 사망 후 mobTime x 1.3~2.0 뒤 리젠
    for mob_id, mob_time in spawn_points:
        # 덤프에 exp 노드가 없는 몬스터는 실제 exp 0 (WZ 기본값 생략)
        exp = mob_dict[mob_id]['exp'] if mob_id in mob_dict else 0
        if mob_time == 0:
            normal_exps.append(exp)
        elif mob_time > 0:
            timed_spawns.append((exp, mob_time))
        # mobTime == -1 은 맵 리셋 시 1회만 스폰되므로 제외

    # 시간 젠: 스폰 포인트마다 (리젠 대기 + 틱 정렬 대기)당 1마리
    exp_per_sec = 0.0
    timed_rate_sum = 0.0
    for exp, mob_time in timed_spawns:
        rate = 1 / (REGEN_MULTIPLIER * mob_time + TICK_ALIGN_DELAY)
        timed_rate_sum += rate
        exp_per_sec += exp * rate

    # 일반 젠: 시간 젠이 우선 소비하는 수용량을 제외하고 틱마다 min(수용량, 포인트 수)마리 스폰
    effective_capacity = max(0.0, capacity - SPAWN_TICK * timed_rate_sum)
    if normal_exps:
        avg_exp = sum(normal_exps) / len(normal_exps)
        exp_per_sec += min(effective_capacity, len(normal_exps)) * avg_exp / SPAWN_TICK

    return exp_per_sec * 60


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

        # 젠 속도 구하기 (없는 맵은 기본값 1.0)
        mob_rate_node = root.find('./dir[@name="info"]/single[@name="mobRate"]')
        mob_rate = float(mob_rate_node.attrib['value']) if mob_rate_node is not None else 1.0
        map_dict[map_id]['mobRate'] = mob_rate

        # 해당 맵에 있는 몬스터 스폰 포인트 구하기
        spawn_points = parse_spawn_points(root)
        map_dict[map_id]['spawnPointCount'] = len(spawn_points)

        # 몹 수용량 구하기
        capacity = calc_mob_capacity(root, mob_rate)
        map_dict[map_id]['mobCapacity'] = capacity

        # 평균 레벨 구하기
        sum_level = 0
        mob_count = 0
        for mob_id, _ in spawn_points:
            if mob_id not in mob_dict:
                continue
            sum_level += mob_dict[mob_id]['level']
            mob_count += 1
        map_dict[map_id]['avgLevel'] = int(sum_level / mob_count) if mob_count > 0 else 0

        # 분당 경험치 구하기 (수용량 기준 / 몬스터 수 기준)
        map_dict[map_id]['expPerMinCap'] = int(calc_exp_per_minute(spawn_points, mob_dict, capacity))
        map_dict[map_id]['expPerMinFull'] = int(calc_exp_per_minute(spawn_points, mob_dict, float('inf')))

    return map_dict


def main():
    map_list = load_map()

    with open('맵별 경험치 효율.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', '거리 이름', '맵 이름', '평균 레벨', '스폰 지점 수', '젠률', '몹 수용량',
                         '분당 경험치(수용량 기준)', '분당 경험치(스폰 지점 기준)'])
        for map_id, data in map_list.items():
            writer.writerow([map_id, data['streetName'], data['mapName'], data['avgLevel'],
                             data['spawnPointCount'], data['mobRate'], data['mobCapacity'],
                             data['expPerMinCap'], data['expPerMinFull']])


if __name__ == '__main__':
    main()
