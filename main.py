
import os
from xml.etree.ElementTree import parse
import csv


# mob 불러와서 리스트에 담은 후 리턴
def mobLoad():
    mobList = {}
    for mob in os.listdir('./Mob'):
        tree = parse('./Mob/' + mob)
        root = tree.getroot()

        try:
            exp = int(root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value'])
            mobList[mob.split('.')[0]] = exp
        except AttributeError:
            continue

    return mobList

# map 불러와서 리스트에 담은 후 리턴
def mapLoad():
    mapList = {}
    for i in range(7):
        path = './Map/Map{}/'.format(i)
        for map in os.listdir(path):
            tree = parse(path + map)
            root = tree.getroot()

            # 몬스터 없는 맵이면 패스~
            try:
                root.find('./imgdir[@name="life"]/imgdir/string[@value="m"]').attrib
            except AttributeError:
                continue

            # 해당 맵 아이디로 딕셔너리 생성
            mapId = map.split('.')[0]
            mapList[mapId] = {}

            # 젠 속도 구하기
            mobRate = float(root.find('./imgdir[@name="info"]/float[@name="mobRate"]').attrib['value'])
            mapList[mapId]['mobRate'] = mobRate

            # 해당 맵에 있는 몬스터 구하기
            life = root.findall('./imgdir[@name="life"]/imgdir')
            life = [mob for mob in life if mob.find('./string[@name="type"]').attrib['value'] == 'm']
            mapList[mapId]['life'] = [m.find('string[@name="id"]').attrib['value'] for m in life]

    return mapList

# 맵 리스트에 맵 이름 추가하여 리턴
def addMapName(mapList):
    tree = parse('String/Map.img.xml')
    root = tree.getroot()

    for id, value in mapList.items():
        try:
            stringMap = root.find('.//imgdir[@name="{}"]'.format(int(id)))
            value['name'] = stringMap.find('./string[@name="streetName"]').attrib['value'] + ' : ' + \
                            stringMap.find('./string[@name="mapName"]').attrib['value']
        except AttributeError:
            continue

    return mapList


mobList = mobLoad()
mapList = addMapName(mapLoad())

for id, value in mapList.items():
    try:
        sumExp = 0
        for mob in value['life']:
            sumExp += mobList[mob]
        value['mapExp'] = sumExp * value['mobRate']
    except KeyError:
        continue

f = open('맵별 경험치 효율.csv', 'w', newline='')
wr = csv.writer(f)
wr.writerow(['이름', '경험치 효율'])
for id, value in mapList.items():
    try:
        wr.writerow([value['name'], value['mapExp']])
    except KeyError:
        continue
f.close()