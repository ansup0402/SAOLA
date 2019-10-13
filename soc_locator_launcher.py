import os
import pathlib
cur_dir = pathlib.Path(__file__).parent



class soc_locator_launcher:

    def __init__(self, feedback, context, parameters, debugging=False):
        self.debugging = debugging
        self.feedback = feedback
        self.context = context
        self.parameters = parameters


    def setProgressMsg(self, msg):
        import time
        now = time.localtime()

        snow = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

        # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
        self.feedback.pushCommandInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushConsoleInfo("\n%s %s" % (snow, msg))
        # self.feedback.pushDebugInfo("\n%s %s" % (snow, msg))

    def execute_accessibility_in_straight(self):

        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        livingID = 'LIV_ID'
        curSOCID = 'CSOC_ID'
        popID = 'POP_ID'


        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # self.setProgressMsg('..... 분석 영역 데이터 생성')
        if self.feedback.isCanceled(): return None
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'])

        # 1-2 분석 지역 데이터 추출 : 세생활권
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 세생활권')
        if self.feedback.isCanceled(): return None
        clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                          onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                          overlay=boundary)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_living.shp')
        clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)

        if isinstance(clipedliving, str):
            model.livingareaLayer = model.writeAsVectorLayer(clipedliving)
        else:
            model.livingareaLayer = clipedliving
        model.livingareaIDField = livingID

        # 1-3 분석 지역 데이터 추출 : 인구데이터
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 인구 데이터')
        if self.feedback.isCanceled(): return None
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=boundary)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        # self.setProgressMsg('..... 분석 지역 데이터 추출 : 기존 생활 SOC 시설\n')
        if self.feedback.isCanceled(): return None
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOC.shp')
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)

        model.currentSOCID = curSOCID
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2

        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC
        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # self.setProgressMsg('..... 거주인구 지점의 최근린 생활SOC지점 검색')
        if self.feedback.isCanceled(): return None
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popwithnearestSOC.shp')
        popwithNearSOC = model.nearesthubpoints(input=clipedpop,
                                                onlyselected=False,
                                                sf_hub=model.currentSOC,
                                                hubfield=model.currentSOCID,
                                                output=out_path
                                                )

        # 2-2 개별거주인구와 생활SOC intersection : 개별 거주인구와 모든 생활SOC까지의 거리 계산
        # self.setProgressMsg('..... 거주인구 데이터와 생활 SOC 데이터 거리 분석\n')
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_popaddedlivingarea.shp')
        popWithNodeaddedliving = model.intersection(input=popwithNearSOC,
                                                    inputfields=[popID,
                                                                 model.popcntField,
                                                                 'HubDist'],
                                                    inputonlyseleceted=False,
                                                    overlay=clipedliving,
                                                    overayprefix='',
                                                    overlayer_fields=[model.livingareaIDField],
                                                    output=out_path
                                                    )

        if isinstance(popWithNodeaddedliving, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedliving)
        else:
            model.populationLayer = popWithNodeaddedliving
        #
        #
        #
        #
        #
        ################# [3 단계] 접근성 분석(직선거리) #################
        # 3-1 세생활권의 접근성 분석
        self.setProgressMsg('[3 단계] 접근성 분석(직선거리)......')
        # self.setProgressMsg('....... 세생활권 접근성 분석')
        if self.feedback.isCanceled(): return None
        dfPop = model.anal_accessibilityCurSOC_straight()

        # 3-2 접근성 분석 결과 평가
        # self.setProgressMsg('....... 접근성 분석 결과 평가')
        if self.feedback.isCanceled(): return None
        finallayer = model.make_Accessbillityscore(isNetwork=False, output=self.parameters["OUTPUT"])

        return finallayer


    def execute_equity_in_straight(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        curSOCID = 'CSOC_ID'
        livingID = 'LIV_ID'
        #
        #
        #
        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'])


        # 1-2 분석 지역 데이터 추출 : 세생활권
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('세생활권 레이어를 초기화 합니다.....')
        clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                        onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                        overlay=boundary)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_living.shp')
        clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)
        if isinstance(clipedliving, str):
            clipedliving = model.writeAsVectorLayer(clipedliving)
        else:
            clipedliving = clipedliving
        # model.livingareaIDField = livingID


        # 1-3 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 1-4 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('존의 생활SOC 레이어를 초기화 합니다.....')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary)

        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOC.shp')
        clipedCurSOC = model.addIDField(input=clipedCurSOC, idfid=curSOCID, output=out_path)
        model.currentSOCID = curSOCID

        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC

        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 2-1 세생활권내 인구 분석
        # 인구 계산
        if self.feedback.isCanceled(): return None
        out_path = ""
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_livingwithpop.shp')
        clipelivingwithpop = model.countpointsinpolygon(polylayer=clipedliving,
                                                        pointslayer=clipedpop,
                                                        field=self.parameters['IN_POP_CNTFID'],
                                                        weight=self.parameters['IN_POP_CNTFID'],
                                                        classfield=None,
                                                        output=out_path)

        if isinstance(clipelivingwithpop, str):
            clipelivingwithpop = model.writeAsVectorLayer(clipelivingwithpop)
        else:
            clipelivingwithpop = clipelivingwithpop

        # 세생활권(인구수)레이어를 Point레이어로 변경
        if self.feedback.isCanceled(): return None
        out_path = ""
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pointlivingwithpop.shp')
        clipepointlivingwithpop = model.centroidlayer(input=clipelivingwithpop,
                                                 output=out_path)

        if isinstance(clipepointlivingwithpop, str):
            model.populationLayer = model.writeAsVectorLayer(clipepointlivingwithpop)
        else:
            model.populationLayer = clipepointlivingwithpop
        model.popcntField = self.parameters['IN_POP_CNTFID']
        model.popIDField = livingID

        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        self.setProgressMsg('[3 단계] 생활 SOC 잠재적 위치 데이터 생성......')
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/grid.shp')
        gridlayer = model.createGridfromLayer(sourcelayer=boundary,
                                              gridsize=self.parameters['IN_GRID_SIZE'],
                                              output=out_path)

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=False,
                                        overlay=boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        if isinstance(grid, str):
            model.potentiallayer = model.writeAsVectorLayer(grid)
        else:
            model.potentiallayer = grid
        model.potentialID = "id"    # "ID"필드가 자동으로 생성됨

        # 10. 분석 실행(기존 시설 거리 분석)
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2


        #
        #
        #
        #
        #
        ################# [4 단계] 형평성 분석(직선거리) #################
        self.setProgressMsg('[4 단계] 형평성 분석(직선거리)......')
        # 4-1 형평성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존 SOC 시설의 직선거리를 분석합니다.....')
        dfPop = model.anal_AllCurSOC_straight()


        # 4-2 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('잠재적 위치의 직선거리를 분석합니다.....')
        potengpd = model.anal_AllPotenSOC_straight()

        # 4-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging:self.setProgressMsg('형평성 지수를 계산합니다.....')
        finallayer = model.make_equityscore(isNetwork=False, output=self.parameters["OUTPUT"])


        return finallayer


    def execute_accessbillity_in_network(self):

        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        livingID = 'LIV_ID'
        popID = 'POP_ID'
        nodeID = self.parameters['IN_NODE_ID']



        #
        #
        #
        #
        #
        model.classify_count =  self.parameters['IN_CALSSIFYNUM']
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_node.shp')
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)

        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = nodeID


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                           onlyselected=False,
                                           distance=2000)

        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_link.shp')
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)

        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']
        
        # 1-4 분석 지역 데이터 추출 : 세생활권
        # 6. 인구레이어 노드 찾기
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('세생활권의 인구정보를 분석합니다.....')
        clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                          onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                          overlay=boundary)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_living.shp')
        clipedliving = model.addIDField(input=clipedliving, idfid=livingID, output=out_path)
        if isinstance(clipedliving, str):
            model.livingareaLayer = model.writeAsVectorLayer(clipedliving)
        else:
            model.livingareaLayer = clipedliving
        model.livingareaIDField = livingID

        # 1-5 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary)

        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.addIDField(input=clipedpop, idfid=popID, output=out_path)
        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOCWithNode.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)


        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 2-1 거주인구 지점의 최근린 생활SOC지점 검색
        if self.feedback.isCanceled(): return None
        out_path = ""
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/curSOCwithNode.shp')
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=nodeID,
                                                output=out_path
                                                )
        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        # 2-2 거주인구 지점의 최근린 노드 검색
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popwithNode.shp')
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                            onlyselected=False,
                                            sf_hub=model.nodelayer,
                                            hubfield=model.nodeIDfield,
                                            output=out_path
                                            )


        # 2-3 개별거주인구와 세생활권 intersection : 개별 거주인구와 모든 세생활권까지의 거리 계산
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_popaddedlivingarea.shp')
        popWithNodeaddedliving = model.intersection(input=popWithNode,
                                                    inputfields=[model.popIDField,
                                                                 model.nodeIDfield,
                                                                 model.popcntField],
                                                    inputonlyseleceted=False,
                                                    overlay=clipedliving,
                                                    overayprefix='',
                                                    overlayer_fields=[model.livingareaIDField],
                                                    output=out_path
                                                    )

        if isinstance(popWithNodeaddedliving, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedliving)
        else:
            model.populationLayer = popWithNodeaddedliving

        #
        #
        #
        #
        #
        ################# [3 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        self.setProgressMsg('[3 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        # 3-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        

        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....')
        alllink = None
        if self.debugging: alllink = os.path.join(cur_dir, 'temp/alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [4 단계] 접근성 분석(네트워크) #################
        self.setProgressMsg('[4 단계] 접근성 분석(네트워크)......')
        # 4-1 세생활권의 접근성 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('세생활권의 최근린 SOC 시설을 찾습니다.....')
        dfPop = model.anal_accessibilityCurSOC_network()

        # 4-2 접근성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('형평성 지수를 계산합니다.....')
        finallayer = model.make_Accessbillityscore(isNetwork=True, output=self.parameters["OUTPUT"])

        return finallayer




    def execute_efficiency_in_straight(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        #
        #
        #
        #
        #
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('바운더리 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('주거인구 레이어를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_POP_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 1-3 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        if isinstance(clipedCurSOC, str):
            model.currentSOC = model.writeAsVectorLayer(clipedCurSOC)
        else:
            model.currentSOC = clipedCurSOC

        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2
        #
        #
        #
        #
        #
        ################# [2 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/grid.shp')
        gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                              gridsize=self.parameters['IN_GRID_SIZE'],
                                              output=out_path)

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=False,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            model.potentiallayer = model.writeAsVectorLayer(clipedgrid)
        else:
            model.potentiallayer = clipedgrid
        model.potentialID = "id"  # "ID"필드가 자동으로 생성됨


        #
        #
        #
        #
        #
        ################# [3 단계] 효율성 분석(네트워크) #################
        self.setProgressMsg('[3 단계] 효율성 분석(네트워크)......')
        # 5-1 효율성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('생활SOC 버퍼......')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/bufferedCurSOC.shp')
        bufferedSOC = model.bufferwithQgis(input=model.currentSOC,
                                            onlyselected=False,
                                            distance=model.cutoff)

        # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 제거)
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존서비스되는 인구 삭제.......')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popremovedCurSOC.shp')
        poplyr = model.differencelayer(input=clipedpop,
                                       onlyselected=False,
                                       overlayer=bufferedSOC,
                                       overonlyselected=False,
                                       output=out_path)

        if isinstance(poplyr, str):
            model.populationLayer = model.writeAsVectorLayer(poplyr)
        else:
            model.populationLayer = poplyr
        model.popcntField = self.parameters['IN_POP_CNTFID']

        # 5-3 효율성 분석 : 잠재적 위치(서비스 영역 설정)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popenSvrArea.shp')
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)

        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popaddedpotenid.shp')
        overprefix = 'POTL_'
        popaddedpoten = model.intersection(input=model.populationLayer,
                                                   inputfields=[model.popcntField],
                                                   inputonlyseleceted=False,
                                                   overlay=potenSvrArea,
                                                   overayprefix=overprefix,
                                                   overlayer_fields=[model.potentialID],
                                                   output=out_path
                                                   )

        # 해당 인구레이어는 잠재적레이어와 outter join 된 결과임
        if isinstance(popaddedpoten, str):
            model.populationLayer = model.writeAsVectorLayer(popaddedpoten)
        else:
            model.populationLayer = popaddedpoten


        # 5-5 효율성 분석 : 잠재적 위치 분석 실행
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')
        relpotenID = overprefix + model.potentialID
        if self.debugging: relpotenID = relpotenID[0: 10]  # shape file의 필드명 최대길이는 10자리 / 메모리에 있으때는 상관없음
        potengpd = model.anal_efficiencyPotenSOC_straight(relpotenID=relpotenID)


        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('효율성 지수를 계산합니다.....')
        finallayer = model.make_efficiencyscore(output=self.parameters["OUTPUT"])

        return finallayer

    def execute_efficiency_in_network(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        popID = 'POP_ID'
        #
        #
        #
        #
        #
        model.classify_count = self.parameters['IN_CALSSIFYNUM']
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('노드/링크 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)

        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_node.shp')
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)

        # 최종 노드, 링크 레이어 클래스에 할당
        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = self.parameters['IN_NODE_ID']


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                            onlyselected=False,
                                            distance=2000)

        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_link.shp')
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)


        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']


        # 1-4 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 1-5 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 2-1 거주인구 지점의 최근린 생활SOC지점 검색
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')
        out_path = ""
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/curSOCwithNode.shp')
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=model.nodeIDfield,
                                                output=out_path
                                                )

        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        # 2-2 거주인구 지점의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        out_path = ''
        popWithNode = model.nearesthubpoints(input=clipedpop,
                                             onlyselected=False,
                                             sf_hub=model.nodelayer,
                                             hubfield=model.nodeIDfield,
                                             output=out_path
                                             )

        # ID 만들어 넣기 $id
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popwithNode.shp')
        popwthNode2 = model.addIDField(input=popWithNode, idfid=popID, output=out_path)

        model.popIDField = popID
        model.popcntField = self.parameters['IN_POP_CNTFID']
        if isinstance(popwthNode2, str):
            model.populationLayer = model.writeAsVectorLayer(popwthNode2)
        else:
            model.populationLayer = popwthNode2
        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        self.setProgressMsg('[3 단계] 생활 SOC 잠재적 위치 데이터 생성......')
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/grid.shp')
        gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                              gridsize=self.parameters['IN_GRID_SIZE'],
                                              output=out_path)

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=False,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 레이어의 인근 노드를 찾습니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/gridwithNode.shp')
        gridwithNode = model.nearesthubpoints(input=grid,
                                              onlyselected=False,
                                              sf_hub=model.nodelayer,
                                              hubfield=model.nodeIDfield,
                                              output=out_path
                                              )
        if isinstance(gridwithNode, str):
            model.potentiallayer = model.writeAsVectorLayer(gridwithNode)
        else:
            model.potentiallayer = gridwithNode
        model.potentialID = "id"  # "ID"필드가 자동으로 생성됨
        #
        #
        #
        #
        #
        ################# [3 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        self.setProgressMsg('[3 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        # 3-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 3-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....')
        alllink = None
        if self.debugging: alllink = os.path.join(cur_dir, 'temp/alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [4 단계] 효율성 분석(네트워크) #################
        self.setProgressMsg('[4 단계] 효율성 분석(네트워크)......')
        # 5-1 효율성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존 SOC 시설을 분석합니다.....')
        dfPop = model.anal_efficiencyCurSOC_network()

        # 5-2 효율성 분석 : 기존 생활 SOC 시설(기 서비스 지역 제거)
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('이미 서비스 되고 있는 인구데이터를 제거합니다.....')
        poplayerwithCurSOC = model.removeRelCurSOCInPoplayer()
        if isinstance(poplayerwithCurSOC, str):
            model.populationLayer = model.writeAsVectorLayer(poplayerwithCurSOC)
        else:
            model.populationLayer = poplayerwithCurSOC

        if self.debugging:
            out_path = os.path.join(cur_dir, 'temp/popwithNoderemovedCurSOC.shp')
            poplyr = model.vectorlayer2ShapeFile(model.populationLayer, output=out_path)

        # 5-3 효율성 분석 : 잠재적 위치(서비스 영역 설정)
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popenSvrArea.shp')
        potenSvrArea = model.bufferwithQgis(input=model.potentiallayer,
                                            onlyselected=False,
                                            distance=model.cutoff,
                                            output=out_path)

        # 5-4 효율성 분석 : 잠재적 위치(잠재적 위치 서비스 지역 분석)
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popaddedpotenid.shp')
        overprefix = 'POTL_'
        popWithNodeaddedpoten = model.intersection(input=model.populationLayer,
                                                   inputfields=[model.popIDField, model.popcntField, model.nodeIDfield],
                                                   inputonlyseleceted=False,
                                                   overlay=potenSvrArea,
                                                   overayprefix=overprefix,
                                                   overlayer_fields=[model.potentialID, model.nodeIDfield],
                                                   output=out_path
                                                   )

        # 해당 인구레이어는 잠재적레이어와 outter join 된 결과임
        if isinstance(popWithNodeaddedpoten, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNodeaddedpoten)
        else:
            model.populationLayer = popWithNodeaddedpoten


        # 5-5 효율성 분석 : 잠재적 위치 분석 실행
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')
        relpotenID = overprefix + model.potentialID
        if self.debugging: relpotenID = relpotenID[0: 10]      # shape file의 필드명 최대길이는 10자리 / 메모리에 있으때는 상관없음

        relpotenNodeID = overprefix + model.nodeIDfield
        if self.debugging: relpotenNodeID = relpotenNodeID[0:10] # shape file의 필드명 최대길이는 10자리 / 메모리에 있으때는 상관없음
        potengpd = model.anal_efficiencyPotenSOC_network(relpotenID=relpotenID,
                                                         relpotenNodeID=relpotenNodeID)

        # 5-6 효율성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('효율성 지수를 계산합니다.....')
        finallayer = model.make_efficiencyscore(output=self.parameters["OUTPUT"])

        return finallayer







    def execute_equity_in_network(self):
        try:
            from .soc_locator_model import soc_locator_model
        except ImportError:
            from soc_locator_model import soc_locator_model
        model = soc_locator_model(feedback=self.feedback, context=self.context, debugmode=self.debugging)

        #
        #
        #
        #
        #
        model.classify_count = self.parameters['IN_CALSSIFYNUM']
        ################# [1 단계] 분석 위한 데이터 초기화 : 분석 영역 데이터 추출 #################
        self.setProgressMsg('[1 단계] 분석을 위한 데이터를 초기화 합니다......')
        # 1-1 분석 영역 데이터 생성
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/boundary.shp')
        boundary = model.dissolvewithQgis(input=self.parameters['IN_SITE'].sourceName(),
                                          onlyselected=self.parameters['IN_SITE_ONLYSELECTED'],
                                          output=out_path)
        if isinstance(boundary, str):
            model.boundary = model.writeAsVectorLayer(boundary)
        else:
            model.boundary = boundary

        # 1-2 분석 지역 데이터 추출 : 노드
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('노드/링크 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_node.shp')
        clipednode = model.clipwithQgis(input=self.parameters['IN_NODE'].sourceName(),
                                        onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                        overlay=boundary,
                                        output=out_path)
        if isinstance(clipednode, str):
            model.nodelayer = model.writeAsVectorLayer(clipednode)
        else:
            model.nodelayer = clipednode
        model.nodeIDfield = self.parameters['IN_NODE_ID']


        # 1-3 분석 지역 데이터 추출 : 링크
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('링크 데이터를 초기화 합니다.....')
        boundary2000 = model.bufferwithQgis(input=boundary,
                                           onlyselected=False,
                                           distance=2000)

        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_link.shp')
        clipedlink = model.clipwithQgis(input=self.parameters['IN_LINK'].sourceName(),
                                        onlyselected=self.parameters['IN_LINK_ONLYSELECTED'],
                                        overlay=boundary2000,
                                        output=out_path)

        if isinstance(clipedlink, str):
            model.linklayer = model.writeAsVectorLayer(clipedlink)
        else:
            model.linklayer = clipedlink
        model.linkFromnodefield = self.parameters['IN_LINK_FNODE']
        model.linkTonodefield = self.parameters['IN_LINK_TNODE']
        model.linklengthfield = self.parameters['IN_LINK_LENGTH']
        model.linkSpeed = self.parameters['IN_LINK_SPEED']

        # 1-4 분석 지역 데이터 추출 : 세생활권
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('세생활권 인구 레이어의 인근 노드를 찾습니다.....')

        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_living.shp')
        clipedliving = model.clipwithQgis(input=self.parameters['IN_LIVINGAREA'].sourceName(),
                                          onlyselected=self.parameters['IN_LIVINGAREA_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 1-5 분석 지역 데이터 추출 : 인구데이터
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_pop.shp')
        clipedpop = model.clipwithQgis(input=self.parameters['IN_POP'].sourceName(),
                                       onlyselected=self.parameters['IN_NODE_ONLYSELECTED'],
                                       overlay=boundary,
                                       output=out_path)

        # 1-6 분석 지역 데이터 추출 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_curSOC.shp')
        clipedCurSOC = model.clipwithQgis(input=self.parameters['IN_CURSOC'].sourceName(),
                                          onlyselected=self.parameters['IN_CURSOC_ONLYSELECTED'],
                                          overlay=boundary,
                                          output=out_path)

        # 5. 기존시설 노드 찾기
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존의 생활SOC 레이어의 인근 노드를 찾습니다.....')

        out_path = ""
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/curSOCwithNode.shp')
        curSocwithNode = model.nearesthubpoints(input=clipedCurSOC,
                                                onlyselected=False,
                                                sf_hub=model.nodelayer,
                                                hubfield=self.parameters['IN_NODE_ID'],
                                                output=out_path
                                                )

        if isinstance(curSocwithNode, str):
            model.currentSOC = model.writeAsVectorLayer(curSocwithNode)
        else:
            model.currentSOC = curSocwithNode

        #
        #
        #
        #
        #
        ################# [2 단계] 세생활권 인구정보와 생활SOC정보 분석 #################
        self.setProgressMsg('[2 단계] 세생활권 인구정보와 생활SOC 분석......')
        # 2-1 세생활권내 인구 분석
        if self.debugging: self.setProgressMsg('세생활권내에 인구 분석......')
        if self.feedback.isCanceled(): return None
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_livingwithpop.shp')
        clipelivingwithpop = model.countpointsinpolygon(polylayer=clipedliving,
                                                        pointslayer=clipedpop,
                                                        field=self.parameters['IN_POP_CNTFID'],
                                                        weight=self.parameters['IN_POP_CNTFID'],
                                                        classfield=None,
                                                        output=out_path)
        # 2-2 거주인구 지점의 최근린 노드  검색
        if self.debugging: self.setProgressMsg('세생활권(인구) 인근 노드 찾기......')
        if self.feedback.isCanceled(): return None
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/popwithNode.shp')
        popWithNode = model.nearesthubpoints(input=clipelivingwithpop,
                                            onlyselected=False,
                                            sf_hub=model.nodelayer,
                                            hubfield=self.parameters['IN_NODE_ID'],
                                            output=out_path
                                            )

        if isinstance(popWithNode, str):
            model.populationLayer = model.writeAsVectorLayer(popWithNode)
        else:
            model.populationLayer = popWithNode
        model.popcntField = self.parameters['IN_POP_CNTFID']

        #
        #
        #
        #
        #
        ################# [3 단계] 생활 SOC 잠재적 위치 데이터 생성 #################
        self.setProgressMsg('[3 단계] 생활 SOC 잠재적 위치 데이터 생성......')
        # 3-1  잠재적 위치 데이터 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 그리드 데이터를 생성합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/grid.shp')
        gridlayer = model.createGridfromLayer(sourcelayer=model.boundary,
                                             gridsize=self.parameters['IN_GRID_SIZE'],
                                             output=out_path)

        # 3-2 분석 지역 데이터 추출 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 데이터를 초기화 합니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/cliped_grid.shp')
        clipedgrid = model.clipwithQgis(input=gridlayer,
                                        onlyselected=False,
                                        overlay=model.boundary,
                                        output=out_path)

        if isinstance(clipedgrid, str):
            grid = model.writeAsVectorLayer(clipedgrid)
        else:
            grid = clipedgrid

        # 3-3 잠재적 위치의 최근린 노드  검색
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 후보지 레이어의 인근 노드를 찾습니다.....')
        out_path = ''
        if self.debugging: out_path = os.path.join(cur_dir, 'temp/gridwithNode.shp')
        gridwithNode = model.nearesthubpoints(input=grid,
                                                  onlyselected=False,
                                                  sf_hub=model.nodelayer,
                                                  hubfield=self.parameters['IN_NODE_ID'],
                                                  output=out_path
                                                  )
        if isinstance(gridwithNode, str):
            model.potentiallayer = model.writeAsVectorLayer(gridwithNode)
        else:
            model.potentiallayer = gridwithNode
        model.potentialID = "ID"  # "ID"필드가 자동으로 생성됨

        #
        #
        #
        #
        #
        ################# [4 단계] 최단거리 분석을 위한 네트워크 데이터 생성 #################
        self.setProgressMsg('[4 단계] 최단거리 분석을 위한 네트워크 데이터 생성......\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        # 4-1 networkx 객체 생성
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석을 위한 노드링크 객체를 생성합니다.....')
        isoneway = (self.parameters['IN_LINK_TYPE'] == 0)
        model.initNXGraph(isoneway=isoneway)
        graph = model.createNodeEdgeInGraph()

        # 5-2 모든 노드간의 최단 거리 분석
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('최단거리 분석 위한 기초자료를 생성합니다.....\n(분석 조건에 따라 10분~60분 이상 소요됩니다...)')
        alllink = None
        if self.debugging: alllink = os.path.join(cur_dir, 'temp/alllink.pickle')
        model.cutoff = self.parameters['IN_LIMIT_DIST']
        model.outofcutoff = self.parameters['IN_LIMIT_DIST'] * 2
        allshortestnodes = model.shortestAllnodes(algorithm='dijkstra',
                                                  output_alllink=alllink)

        #
        #
        #
        #
        #
        ################# [5 단계] 형평성 분석(네트워크) #################
        self.setProgressMsg('[5 단계] 형평성 분석(베트워크)......')
        # 5-1 형평성 분석 : 기존 생활 SOC 시설
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('기존 SOC 시설의 최단거리를 분석합니다.....')
        dfPop = model.anal_AllCurSOC_network()

        # 5-3 형평성 분석 : 잠재적 위치
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('잠재적 위치의 최단거리를 분석합니다.....')
        potengpd = model.anal_AllPotenSOC_network()

        # 5-3 형평성 분석 결과 평가
        if self.feedback.isCanceled(): return None
        if self.debugging: self.setProgressMsg('형평성 지수를 계산합니다.....')
        finallayer = model.make_equityscore(isNetwork=True, output=self.parameters["OUTPUT"])


        return finallayer


