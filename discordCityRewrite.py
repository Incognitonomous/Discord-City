import random
import math
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import datetime
#import svgModule

def PolarToCartesian(coord,centre):
    #converts polar coords into cartesian coords
    angle = coord[0]
    magnitude = coord[1]    
    x = magnitude*math.cos(angle)+centre[0]
    y = magnitude*math.sin(angle)+centre[1]
    return [x,y]

def shiftPair(inputList):
    #creates a list of pairs, where the second item is 1 position further
    #than the first item in the original list
    shiftedList = inputList[1:] + [inputList[0]]
    return list(zip(inputList,shiftedList))
        

class city:
    def __init__(self,width,height):
        self.streets = []
        self.width = width
        self.height = height
        self.centre = [width/2,height/2]
        #self.ptoc = lambda coord: PolarToCartesian(coord,self.centre)
        #angle = 0

        #creates streets at random angle intervals greater than 40 degrees, depending on the streetNum
        streetNum = random.randint(2,5)
        streetAngle = 360/streetNum

        for i in range(0,streetNum):
            self.streets.append(random.uniform(streetAngle*i+40,streetAngle*(i+1)))
        print(self.streets)
    
    def setOwner(self,owner):
        self.owner = owner

    def createSolidWall(self,memberList,radius):
        num = len(memberList)
        segments = list(((2*math.pi)/num * i) for i in range(0,num))
        segmentPairs = shiftPair(segments)
        maxAngle = math.acos(radius/(radius+40))

        memberList[0].generateWall(radius,segmentPairs[num-1][0],segmentPairs[num-1][1],maxAngle,10)

        for i in range(1,num):
            #print(num-i-1)
            memberList[i].generateWall(radius,segmentPairs[i][0],segmentPairs[i][1],maxAngle,10)
        #segments.insert(0,0)


        
    def createCity(self,memberList):
        self.houseList = []
        self.boostList = []
        self.modList = []
        #seperates owners, boosters and regular members
        classMap = [self.member, self.administrator, self.booster, self.owner]
        listMap = {"member":self.houseList.append, "administrator":self.modList.append,"booster":self.boostList.append,"owner":self.setOwner}

        for member in memberList:
            mapNum = member.owner*8 + member.boosting*4 + member.administrator*2 + 1
            #print(mapNum)
            mapNum = int(math.log2(mapNum))
            member = classMap[mapNum](member,self.centre)
            listMap[member.type](member)
        
        #sorts list by priority
        self.boostList.sort(key = lambda x: x.priority, reverse = False)
        self.houseList.sort(key = lambda x: x.priority, reverse = False)
        self.modList.sort(key = lambda x: x.priority, reverse = False)

        radius = 80
        #creates the owner centre piece
        self.owner.createCastle(radius-60)
        rAppend = 20
        band = 1
        streetPairs = shiftPair(self.streets)
        segments = [self.segment(streetPairs[0][0],streetPairs[0][1],radius)]
        
        sAppend = 0
        bAppend = 0

        num = len(self.modList)
        x = 9 * (num>9) + num * (num<=9)
        innerRing = self.modList[:x]
        self.createSolidWall(innerRing,40)
        outerRing = []
        try:
            outerRing = self.modList[x+1:]
        except:
            pass

        #for i in innerRing:


        for house in self.houseList:
            #iterates though house lists
            if not(segments[sAppend].evalLen(house.getAngle(radius),radius)):
                #if segment full
                if sAppend + 1 < len(streetPairs):
                    #if there are still segments left in the circle
                    #add 1 to segment append, add new segment to segments
                    sAppend+=1
                    segments.append(self.segment(streetPairs[sAppend][0],streetPairs[sAppend][1],radius))

                else:
                    #if there are no segments left in the circle, create a new band, starting with
                    #an empty segments list
                    radius += rAppend 
                    segments = [self.segment(streetPairs[0][0],streetPairs[0][1],radius)]
                    sAppend = 0
                    band += 1
                    
                    #creates empty space every 2 bands. if there are more boosters in the server, create
                    #a new ring in that space
                    if band % 3 != 2:
                        if bAppend < len(self.boostList):
                            radius += 15
                            self.boostList[bAppend].createWall(radius,self.streets)
                            radius += 15
                            bAppend+=1
                        else:
                            radius += rAppend
                        band += 1

            #create a house for regular member in the corresponding radius and segment
            segments[sAppend] = house.createHouse(segments[sAppend],radius,rAppend)
            #print(radius)

        #adds boosters and owner into houseList for later rendering
        self.houseList += self.boostList
        self.houseList.append(self.owner)
        self.houseList += self.modList
                
    def saveCity(self,directory,name):
        svg = self.svg(directory,name,self.width,self.height)
        svg.saveFile(self.houseList)

    class house:
        def getFill(self,colour):
            rgb = colour
            try:
                magnitude = (rgb[0]**2+rgb[1]**2+rgb[2]**2)**0.5
                #magnitude += magnitude == 0
                if magnitude == 0:
                    rgb = [50,50,50]
                else:
                    rgb = list(map(lambda x: int(x/magnitude * 200),rgb))
            except:
                rgb=list(map(lambda x: (2*(x<215)-1)*40))
            return rgb
        
        def __init__(self,member,centre):
            #print(member.messageCount)
            self.size = 0
            self.lineColour = member.colour
            self.fillColour = self.getFill(self.lineColour)
            self.priority = member.joinDate.timestamp()
            self.name = member.mention
            self.centre = centre
            self.ptoc = lambda coord: PolarToCartesian(coord,self.centre)
            self.shapes = []
            
        def getAngle(self,radius):
            self.angle = self.size/radius
            return self.angle
        
        class shape:
            def __init__(self,colours,strokeWidth,fill,house):
                self.name = house.name
                self.strokeWidth = strokeWidth
                colour_choice = [house.lineColour,house.fillColour]
                self.lineColour = self.formatColour(colour_choice[colours[0]])
                self.fillColour = self.formatColour(colour_choice[colours[1]])
                self.doFill = fill
                self.contents = ""
                self.type = ""

            def draw(self):
                #pointer-events=\"bounding-box\"
                self.contents = "\n<{0} ".format(self.type)
                self.contents += self.specifics()
                self.contents += "style=\"stroke:{0};stroke-width:{1}".format(self.lineColour,self.strokeWidth)
                self.contents += self.fill() + "\"> "
                title = "<title>{0}</title>".format(self.name)
                self.contents += title
                self.contents += " </{0}>".format(self.type)
                return self.contents

            def formatColour(self,colour):
                return"rgb({0},{1},{2})".format(*colour)

            def specifics(self):
                return ""

            def fill(self):
                if self.doFill:
                    return ";fill:{0}".format(self.fillColour)
                else:
                    return ";fill:none"
        
        class polygon(shape):
            def __init__(self,coords,house,colours = [0,1],strokeWidth = 2,fill = True):
                super().__init__(colours,strokeWidth,fill,house)
                self.type = "polygon"
                self.coords = coords
                #print(coords)

            def specifics(self):
                append = "points=\""
                for coord in self.coords:
                    append += "{0},{1} ".format(*coord)
                append = append[0:-1]
                append += "\" "
                return append

        class circle(shape):
            def __init__(self,centre,radius,house,colours = [0,1],strokeWidth = 2,fill = True):
                super().__init__(colours,strokeWidth,fill,house)
                self.type = "circle"
                self.centre = centre
                self.radius = radius
                

            def specifics(self):
                append = "cx=\"{0}\" cy=\"{1}\" r=\"{2}\" ".format(*self.centre,self.radius)
                return append

            def fill(self):
                if self.doFill:
                    return ";fill:{0}".format(self.fillColour)
                else:
                    return ";fill:none"
        class segmented_circle(circle):
            def __init__(self,centre,radius,segment,colours,strokeWidth,fill,house):
                super().__init__(centre,radius,colours,strokeWidth,fill,house)
                circumference = 2*math.pi*(radius)
                segment[1] -= radius/20
                segment = list(map(lambda x:(x/365*(circumference)), segment))
                #segment[1] -= 20
                self.segmentOffset = (circumference)-segment[0]
                self.segmentRatio = [(segment[1]-segment[0]),circumference-(segment[1]-segment[0])]
                

            def specifics(self):
                append = "cx=\"{0}\" cy=\"{1}\" r=\"{2}\" ".format(*self.centre,self.radius)
                append += "stroke-dasharray=\"{0} {1}\" stroke-dashoffset=\"{2}\" ".format(*self.segmentRatio,self.segmentOffset)
                return append

        class line(shape):
            def __init__(self,coord1,coord2,strokeWidth,house):
                super().__init__([0,0],strokeWidth,False,house)
                self.type = "line"
                self.coord1 = coord1
                self.coord2 = coord2

            def specifics(self):
                append = "x1=\"{0}\" y1=\"{1}\" x2=\"{2}\" y2=\"{3}\" ".format(*self.coord1,*self.coord2)
                return append

            def fill(self):
                return ""

    class owner(house):
        def __init__(self,member,centre):
            super().__init__(member,centre)
            self.size = int((datetime.datetime.now().date()-member.joinDate.date()).days/365.25)+3
            self.type = "owner"

        def createCastle(self,radius):
            R = radius
            #R = math.sqrt(2*r**2)
            #coords = [[math.pi/4, R],[3*math.pi/4,R], [5*math.pi/4,R], [5*math.pi/4,R/2], [3*math.pi/2,R], [7*math.pi/4,R/2], [7*math.pi/4,R]]
            baseCoords = [[math.pi/4,R],[3*math.pi/4,R],[3*math.pi/4 + 5/R,2*R/3],[math.pi/4 - 5/R ,2*R/3]]
            baseCoords = list(map(self.ptoc,baseCoords))
            self.shapes.append(self.polygon(baseCoords,self))
            coords = [[math.pi/4 - 5/R ,R/2],[3*math.pi/4 + 5/R,R/2],[5*math.pi/4 - 2/R,R],[5*math.pi/4,R/2],[3*math.pi/2,R],[7*math.pi/4,R/2],[7*math.pi/4 + 2/R,R]]
            coords = list(map(self.ptoc,coords))
            #coords = [self.ptoc()]
            self.shapes.append(self.polygon(coords,self))
            for i in range(2,len(coords),2):
                self.shapes.append(self.circle(coords[i],3,self))
        
    class member(house):
        def __init__(self,member,centre):
            super().__init__(member,centre)
            self.size = math.log(member.messageCount+math.e)*5
            self.type = "member"
        
        def getAngle(self,radius):
            self.angle = self.size/radius
            return self.angle
        
        def createHouse(self,segment,radius,rAppend):
            temp = segment.currentAngle + self.angle
            coords = [self.ptoc([segment.currentAngle,radius]),self.ptoc([temp,radius]),self.ptoc([temp,radius+rAppend]),self.ptoc([segment.currentAngle,radius+rAppend])]
            segment.currentAngle += self.angle
            self.shapes.append(self.polygon(coords,self))
            return segment
    
    class booster(house):
        def __init__(self,member,centre):
            super().__init__(member,centre)
            self.size = int((datetime.datetime.now().date() - member.boostSince.date()).days/30.5)+1
            #self.size = 4
            self.type = "booster"
        
        def createWall(self, radius, streets):
            r = radius
            R = radius + 40
            maxAngle = math.acos(r/R)
            #print(maxAngle)
            wallBreakPairs = []
            for street in streets:
                x = (street/360*2*math.pi)-20/radius
                x += 2*math.pi*(x<0)
                wallBreakPairs.append([x,street/360*2*math.pi+20/radius])

            #print(wallBreakPairs)

            wallBreakGroupGroups = []
            wallBreakPairPairs = shiftPair(wallBreakPairs)
            #print(wallBreakPairPairs)

            for PairPair in wallBreakPairPairs:
                wallBreakGroup = self.bufferWallBreak(PairPair[0][1],PairPair[1][0],maxAngle)
                wallBreakGroupGroups.append(wallBreakGroup)
                #wallBreaks += [PairPair[0][1],PairPair[1][0]]
                #wallBreaks += self.bufferWallBreak(PairPair[0][1],PairPair[1][0])
            
            #print(wallBreakGroupGroups)

            tierMap = {1: self.tier1Wall, 2:self.tier2Wall, 3:self.tier3Wall, 4:self.tier4Wall, 5:self.tier5Wall}

            for group in wallBreakGroupGroups:
                groupPair = shiftPair(group)[:-1]
                tierMap[self.size](groupPair,r)
                
        def squareTurret(self,angle,radius,colour = [0,1]):
            coords = [[angle-10/radius,radius-10],[angle+10/radius,radius-10],[angle+10/radius,radius+10],[angle-10/radius,radius+10]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords
        
        def diamondTurret1(self,angle,radius,colour = [0,1]):
            coords = [[angle,radius-10],[angle-7/radius,radius],[angle,radius+10],[angle+7/radius,radius]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords
        
        def diamondTurret2(self,angle,radius,colour = [0,1]):
            coords = [[angle,radius-12],[angle-10/radius,radius],[angle,radius+12],[angle+10/radius,radius]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords

        def crystalTurret1(self,angle,radius,colour = [0,1]):
            coords = [[angle,radius-12],[angle+0.04,radius-6],[angle+0.04,radius+6],[angle,radius+12],[angle-0.04,radius+6],[angle-0.04,radius-6],[angle,radius-12]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords

        def crystalTurret2p1(self,angle,radius,colour = [1,1]):
            coords = [[angle,radius-12],[angle+0.06,radius-6],[angle+0.06,radius+6],[angle,radius+12],[angle-0.06,radius+6],[angle-0.06,radius-6],[angle,radius-12]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            return coords
        
        def crystalTurret2p2(self,angle,radius,colour = [1,0]):
            coords = [[angle,radius-8],[angle+0.04,radius-4],[angle+0.04,radius+4],[angle,radius+8],[angle-0.04,radius+4],[angle-0.04,radius-4]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords
        
        def wall(self,angle1,angle2,radius,colour = [0,0]):
            coords = [[angle1,radius+5],[angle1,radius-5],[angle2,radius-5],[angle2,radius+5]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords

        def thiccWall(self,angle1,angle2,radius,colour = [0,0]):
            coords=[[angle1,radius-5],[angle1,radius+5],[(angle1+angle2)/2,radius+5],[angle2,radius+5],[angle2,radius-5]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords

        def generateWall(self,groupPair,r,funcListTurret,colourListTurret,funcListWall,colourListWall):
            for connection in groupPair:
                for i in range(0,len(funcListWall)):
                    funcListWall[i](connection[0],connection[1],r,colour=colourListWall[i])
                for i in range(0,len(funcListTurret)):
                    funcListTurret[i](connection[0],r,colour=colourListTurret[i])
            for i in range(0,len(funcListTurret)):
                    funcListTurret[i](groupPair[-1][1],r,colour=colourListTurret[i])

        def tier1Wall(self,groupPair, r):
            self.generateWall(groupPair,r,[self.squareTurret],[[0,1]],[self.wall],[[0,0]])
            
        
        def tier2Wall(self,groupPair, r):
            self.generateWall(groupPair,r,[self.diamondTurret1],[[0,1]],[self.wall],[[0,0]])

        def tier3Wall(self,groupPair, r):
            self.generateWall(groupPair,r,[self.diamondTurret2],[[0,1]],[self.thiccWall],[[0,0]])
            
        def tier4Wall(self, groupPair, r):
            self.generateWall(groupPair,r,[self.crystalTurret1],[[0,0]],[self.thiccWall],[[1,1]])

        def tier5Wall(self, groupPair, r):
            self.generateWall(groupPair,r,[self.crystalTurret2p1,self.crystalTurret2p2],[[0,0],[1,0]],[self.thiccWall],[[1,1]])

        def bufferWallBreak(self, wallBreak1, wallBreak2, maxAngle):
            try:
                wallBreak2 += 2*math.pi*(wallBreak2<wallBreak1)
                x = (wallBreak2-wallBreak1)/maxAngle
                x = int(x) + 1
                
                maxAngle = (wallBreak2-wallBreak1)/x
                wallBreaks = [wallBreak1]
                for i in range(0,x):
                    wallBreaks.append(wallBreaks[i]+maxAngle)
                #print(wallBreaks)
                
                return wallBreaks
            except:
                return wallBreak1,wallBreak2

    class administrator(house):
        def __init__(self,member,centre):
            super().__init__(member,centre)
            #self.size = int((datetime.datetime.now().date() - member.boostSince.date()).days/30.5)+1
            self.size = 4
            self.type = "administrator"
        
        def generateWall(self, radius, wallBreak1, wallBreak2, maxAngle, size):
            wallBreaks = self.bufferWallBreak(wallBreak1,wallBreak2,maxAngle)
            wallBreakPairs = shiftPair(wallBreaks)[:-1]
            self.renderWall(wallBreakPairs,radius,[self.squareTurret],[[0,1]],[self.wall],[[0,0]])

        def bufferWallBreak(self, wallBreak1, wallBreak2, maxAngle):
            try:
                wallBreak2 += 2*math.pi*(wallBreak2<wallBreak1)
                x = (wallBreak2-wallBreak1)/maxAngle
                x = int(x) 
                
                maxAngle = (wallBreak2-wallBreak1)/x
                wallBreaks = [wallBreak1]
                for i in range(0,x):
                    wallBreaks.append(wallBreaks[i]+maxAngle)
                #print(wallBreaks)
                
                return wallBreaks
            except:
                return wallBreak1,wallBreak2
        
        def renderWall(self,groupPair,r,funcListTurret,colourListTurret,funcListWall,colourListWall):
            for connection in groupPair:
                for i in range(0,len(funcListWall)):
                    funcListWall[i](connection[0],connection[1],r,colour=colourListWall[i])
                for i in range(0,len(funcListTurret)):
                    funcListTurret[i](connection[0],r,colour=colourListTurret[i])
            

        def squareTurret(self,angle,radius,colour = [0,1]):
            coords = [[angle-10/radius,radius-10],[angle+10/radius,radius-10],[angle+10/radius,radius+10],[angle-10/radius,radius+10]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
        
        def wall(self,angle1,angle2,radius,colour = [0,0]):
            coords = [[angle1,radius+5],[angle1,radius-5],[angle2,radius-5],[angle2,radius+5]]
            coords = list(map(self.ptoc,coords))
            self.shapes.append(self.polygon(coords,self,colours=colour))
            #return coords

    class segment:
        def __init__(self,startAngle,endAngle,radius):
            self.startAngle = (startAngle/360) * 2 * math.pi + random.uniform(10/radius,25/radius)
            self.endAngle = (endAngle/360) * 2 * math.pi
            self.endAngle += 2*math.pi*(self.endAngle<self.startAngle)
            self.angle = self.endAngle-self.startAngle
            self.currentAngle = self.startAngle

        def evalLen(self,angle,radius):
            #print(self.currentAngle,self.endAngle,angle)
            return self.currentAngle + angle + (10/(radius)) < self.endAngle

    class svg:
        def __init__(self,directory, name, width, height):
            self.directory = directory
            self.name = name
            self.contents = "<svg width=\"{0}\" height=\"{1}\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\"> ".format(width,height)
            self.contents += "<image width=\"{0}\" height=\"{1}\" xlink:href=\"paper.png\"/> ".format(width,height)
            self.contents += "<image width=\"{0}\" height=\"{1}\" xlink:href=\"https://raw.githubusercontent.com/Greenfoot5/Discord-City/master/paper.png\"/> ".format(width,height)
            self.contents += "<image x=\"20\" y=\"20\" width=\"200\" height=\"200\" xlink:href=\"http://www.clipartbest.com/cliparts/jTx/6od/jTx6od7ec.png\"/> "
            #self.contents += "<image width=\"200\" height=\"200\" xlink:href=\"compass.png\"/>"
            self.width = width
            self.height = height
            self.centre = [width/2,height/2]
        
        def saveFile(self, houseList):
            #houseList[0]
            for house in houseList:
                for shape in house.shapes:
                    self.contents += shape.draw()
            self.contents += "\n</svg>"

            with open(self.directory+self.name+".svg","w",encoding="utf-8") as file:
                file.write(self.contents)
            drawing = svg2rlg(self.directory+self.name+".svg")
            renderPM.drawToFile(drawing, self.directory+self.name+".png", fmt="PNG")
            
def memberList(num):
    memberlist = []
    for i in range(0,num):
        memberlist.append([i,[random.randint(0,255),random.randint(0,255),random.randint(0,255)],random.randint(0,100000),random.choice(["bob","fred"])])

    return memberlist

def do_City(memberList):
    if len(memberList) > 1000:
        x = int(2**10+math.log(len(memberList), base=10)-2)
    else:
        x = 2**10
    c = city(x,x)
    c.createCity(memberList)
    c.saveCity("","test")
    return x
