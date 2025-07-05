import 'WzComparerR2.PluginBase'
import 'WzComparerR2.WzLib'
import 'System.IO'
import 'System.Xml'

------------------------------------------------------------
-- Wz_Image 타입인지 확인하는 헬퍼 함수
function isWzImage(value)
  return value and type(value) == "userdata"
    and (value:GetType().Name == 'Wz_Image' or value:GetType().Name == 'Ms_Image')
end

------------------------------------------------------------

-- 추출할 노드 경로 목록
local targetNodePaths = {
  'Map/Map/Map0',
  'Map/Map/Map1',
  'Map/Map/Map2',
  'Map/Map/Map3',
  'Map/Map/Map4',
  'Map/Map/Map5',
  'Map/Map/Map6',
  'Map/Map/Map8',
  'Map/Map/Map9',
  'Mob',
  'String'
}

-- XML 파일을 저장할 최상위 폴더
local outputDir = "./data"

------------------------------------------------------------
-- 메인 함수

-- targetNodePaths에 정의된 각 경로를 순회합니다.
for _, path in ipairs(targetNodePaths) do
  local topNode = PluginManager.FindWz(path)

  if topNode then
    env:WriteLine('Processing node: ' .. topNode.FullPath)

    -- topNode의 직속 하위 노드들만 순회합니다. (하위 폴더로 더 들어가지 않음)
    for _, n in each(topNode.Nodes) do
      local value = n.Value
      -- 하위 노드가 Wz_Image인 경우에만 처리합니다.
      if isWzImage(value) then
        local img = value

        -- Wz_Image 추출 시도
        if img:TryExtract() then

          -- XML 파일로 덤프
          local xmlFileName = outputDir .. "\\" .. (n.FullPathToFile) .. ".xml"
          local dir = Path.GetDirectoryName(xmlFileName)

          -- 폴더가 존재하지 않으면 생성
          if not Directory.Exists(dir) then
            Directory.CreateDirectory(dir)
          end

          -- 파일 생성 및 XML 작성
          local fs = File.Create(xmlFileName)
          local xw = XmlWriter.Create(fs)

          xw:WriteStartDocument(true);
          Wz_NodeExtension.DumpAsXml(img.Node, xw)
          xw:WriteEndDocument()

          xw:Flush()
          fs:Close()

          -- 메모리에서 이미지 데이터 해제
          img:Unextract()

        else -- 추출 실패 시
          env:WriteLine(n.FullPath .. ' extract failed.')
        end -- end extract
      end -- end type validate
    end -- end foreach child node
  else
    -- Wz 파일에서 해당 경로를 찾지 못한 경우
    env:WriteLine('Node not found: ' .. path)
  end -- end topNode check
end -- end foreach path

env:WriteLine('--------Done.---------')
