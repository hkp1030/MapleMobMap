
import os

from xml.etree.ElementTree import parse

'''
tree = parse('./Mob/0100000.img.xml')
root = tree.getroot()

print(root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value'])
'''

mobList = {}
for mob in os.listdir('./Mob'):
    tree = parse('./Mob/' + mob)
    root = tree.getroot()

    try:
        exp = int(root.find('./imgdir[@name="info"]/int[@name="exp"]').attrib['value'])
        mobList[mob.split('.')[0]] = exp
    except AttributeError:
        continue


print(mobList)
