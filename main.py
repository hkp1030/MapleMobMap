import csv
import os
from xml.etree.ElementTree import parse


# mob 불러와서 리스트에 담은 후 리턴
def mobLoad():
    mobList = {}
    for top, dirs, files in os.walk('./Mob'):
        for file in files:
            if os.path.splitext(file)[1] != '.xml':
                continue

            path = os.path.join(top, file)
            tree = parse(path)
            root = tree.getroot()

            # 경험치, 레벨이 없는 몬스터는 패스~
            try:
                root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value']
                root.find('./imgdir[@name="info"]/int[@name="level"]').attrib['value']
            except AttributeError:
                continue

            # 해당 몬스터 아이디로 딕셔너리 생성
            mobId = root.attrib['name'].split('.')[0]
            mobList[mobId] = {}

            # 해당 몬스터의 레벨과 경험치 구하기
            exp = int(root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value'])
            level = int(root.find('./imgdir[@name="info"]/int[@name="level"]').attrib['value'])
            mobList[mobId]['exp'] = exp
            mobList[mobId]['level'] = level

    return mobList


# map 불러와서 리스트에 담은 후 리턴
def mapLoad():
    mapList = {}
    for top, dirs, files in os.walk('./Map'):
        for file in files:
            if os.path.splitext(file)[1] != '.xml':
                continue

            path = os.path.join(top, file)
            tree = parse(path)
            root = tree.getroot()

            # 몬스터 없는 맵이면 패스~
            try:
                root.find('./imgdir[@name="life"]/imgdir/string[@value="m"]').attrib
            except AttributeError:
                continue

            # 해당 맵 아이디로 딕셔너리 생성
            mapId = root.attrib['name'].split('.')[0]
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
            value['streetName'] = stringMap.find('./string[@name="streetName"]').attrib['value']
            value['mapName'] = stringMap.find('./string[@name="mapName"]').attrib['value']
        except AttributeError:
            continue

    return mapList


def main():
    mobList = mobLoad()
    mapList = addMapName(mapLoad())

    for id, value in mapList.items():
        try:
            sumExp = 0
            sumLevel = 0
            for mob in value['life']:
                sumExp += mobList[mob]['exp']
                sumLevel += mobList[mob]['level']
            value['mapExp'] = int(sumExp * value['mobRate'])
            value['avgLevel'] = int(sumLevel / len(value['life']))
        except KeyError:
            continue

    f = open('맵별 경험치 효율.csv', 'w', newline='')
    wr = csv.writer(f)
    wr.writerow(['ID', '거리 이름', '맵 이름', '평균 레벨', '몬스터 수', '젠률', '경험치 효율'])
    for id, value in mapList.items():
        try:
            wr.writerow([id, value['streetName'], value['mapName'], value['avgLevel'], len(value['life']),
                         value['mobRate'], value['mapExp']])
        except KeyError:
            continue
    f.close()


if __name__ == "__main__":
    main()
