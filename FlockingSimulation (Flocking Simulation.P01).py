
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from imgui.integrations.glfw import GlfwRenderer

import glfw
import glm
import imgui

import numpy as np
import freetype as ft

import math
import random
import os
import time


class Index:
    SPECIFIC_PROGRAM_INFO_COLOR = 0
    SPECIFIC_PROGRAM_INFO_TEXT_POS = 1
    SPECIFIC_PROGRAM_INFO_TEXT_INTERVAL = 2
    SPECIFIC_PROGRAM_INFO_NUM_TEXTS = 3
    SPECIFIC_PROGRAM_INFO_FONT_SIZE = 4
    SPECIFIC_PROGRAM_INFO_TEXT_START = 5

    IMGUI_WINDOW_HIERARCHY = 0
    IMGUI_WINDOW_INSPECTOR = 1

    SHADER_DEFAULT = 0
    SHADER_SIMPLE_USE_UNIFORMCOLOR = 1

    SHADER_CODE_DEFAULT = 0

    SHADER_FRAGMENT_CODE_SIMPLE_USE_UNIFORMCOLOR = 101

class SceneManager:
    def __init__(self, view3D):
        self.displaySize = (1280, 720)

        self.screenSize = (680, 680)        
        self.screenPos = []

        self.imguiSize = []
        self.imguiPos = []

        self.imguiFont = None

        self.drawingStuffVerticesList = []
        self.drawingStuffIndicesList = []

        self.coordAxesVertices = []
        self.coordAxesIndices = []

        self.programInfoAreaVertices = []
        self.programInfoAreaIndices = []

        self.fovy = 45.0
        self.aspect = self.screenSize[0] / self.screenSize[1]
        self.near = 0.1
        self.far = 1000.0

        self.shaders = []

        self.camera = None
        self.enableCameraMove = False
        self.enableCameraSailing = False
        self.cameraSailingSpeed = 1.0

        self.view3D = view3D
        self.drawAxes = True

        self.perspectivePrjMat = glm.perspective(self.fovy, self.aspect, self.near, self.far)
        self.orthoPrjMat = glm.ortho(0, self.screenSize[0], 0, self.screenSize[1], 1.0, 100.0)
        self.GUIPrjMat = glm.ortho(0, self.displaySize[0], 0, self.displaySize[1], 1.0, 100.0)

        self.view3DMat = glm.mat4()
        self.view2DMat = glm.translate(glm.vec3(0.0, 0.0, 20.0))
        self.view2DMat = glm.inverse(self.view2DMat)

        self.coordAxesViewMat = glm.mat4()

        self.modelMat = glm.mat4()        

        self.objects = []
        self.smallFont = None
        self.font = None
        self.largeFont = None

        self.deltaTime = 0.0
        self.dirty = True

        self.colors = {}

        self.programInfo = False
        self.numProgramInfoElement = 7

        self.specificProgramInfo = True
        self.specificProgramArgs = []

        self.controlFPS = False
        self.FPS = 30
        self.oneFrameTime = 1.0 / self.FPS
        self.deltaTime = 0.0
        self.elapsedTime = 0.0        
        self.enableRender = True

        self.pause = False
        self.debug = False
        self.debugMat = glm.mat4()

        self.logFile = None
        self.startLog = False

        self.numVertexComponents = 7
        self.numDrawingStuff = 2

        self.drawingStuffVAO = None
        self.drawingStuffVBO = None
        self.drawingStuffEBO = None
        
        self._Initialize()        

    def GetDisplaySize(self):
        return self.displaySize

    def SetDisplaySize(self, width, height):
        self.displaySize[0] = width
        self.displaySize[1] = height
        self.aspect = self.displaySize[0] / self.displaySize[1]

        self.dirty = True   

    def GetCamera(self):
        return self.camera

    def SetCamera(self, camera):
        self.camera = camera

    def GetView3D(self):
        return self.view3D

    def SetView3D(self, view3D):
        self.view3D = view3D

        if self.view3D == False:
            self.drawAxes = False

    def GetEnableCameraMove(self):
        return self.enableCameraMove

    def SetEnableCameraMove(self, enableCameraMove):
        self.enableCameraMove = enableCameraMove

        if self.enableCameraMove == False:
            self.enableCameraSailing = False

    def GetPerspectivePrjMat(self):
        return self.perspectivePrjMat

    def GetOrthoPrjMat(self):
        return self.orthoPrjMat        

    def GetGUIPrjMat(self):
        return self.GUIPrjMat

    def GetView3DMat(self):
        self.view3DMat = self.camera.GetViewMat()
        return self.view3DMat

    def GetView2DMat(self):
        return self.view2DMat

    def GetPause(self):
        return self.pause

    def GetDebug(self):
        return self.debug

    def GetColor(self, key, index):
        completedKey = key + str(index)
        return self.colors[completedKey]

    def GetShader(self, index):
        return self.shaders[index]

    def GetScreenSize(self):
        return self.screenSize

    def GetScreenPos(self):
        return self.screenPos

    def GetImguiSize(self, index):
        return self.imguiSize[index]

    def GetImguiPos(self, index):
        return self.imguiPos[index]

    def GetImguiFont(self):
        return self.imguiFont        

    def SetDirty(self, value):
        self.dirty = value

    def SetCameraPos(self):
        cameraSpeed = 0.0

        if self.enableCameraSailing == True:
            cameraSpeed = self.cameraSailingSpeed
        else:
            cameraSpeed = 0.05

        if gInputManager.GetKeyState(glfw.KEY_W) == True:
            self.camera.ProcessKeyboard('FORWARD', cameraSpeed)
            self.dirty = True
        if gInputManager.GetKeyState(glfw.KEY_S) == True:
            self.camera.ProcessKeyboard('BACKWARD', cameraSpeed)
            self.dirty = True
        if gInputManager.GetKeyState(glfw.KEY_A) == True:
            self.camera.ProcessKeyboard('LEFT', cameraSpeed)
            self.dirty = True
        if gInputManager.GetKeyState(glfw.KEY_D) == True:
            self.camera.ProcessKeyboard('RIGHT', cameraSpeed)
            self.dirty = True 
        if gInputManager.GetKeyState(glfw.KEY_E) == True:
            self.camera.ProcessKeyboard('UPWARD', cameraSpeed)
            self.dirty = True
        if gInputManager.GetKeyState(glfw.KEY_Q) == True:
            self.camera.ProcessKeyboard('DOWNWARD', cameraSpeed)
            self.dirty = True     

    def SetSpecificProgramArgs(self, index, subIndex, value):        
        argsList = list(self.specificProgramArgs[index])

        argsList[subIndex] = value     

        self.specificProgramArgs[index] = tuple(argsList)

    def InitializeOpenGL(self, shaders):        
        self.shaders = shaders

        color = self.GetColor('DefaultColor_', 1)
        glClearColor(color[0], color[1], color[2], 1.0)

        glEnable(GL_DEPTH_TEST)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        self.drawingStuffVAO = glGenVertexArrays(self.numDrawingStuff)
        self.drawingStuffVBO = glGenBuffers(self.numDrawingStuff)
        self.drawingStuffEBO = glGenBuffers(self.numDrawingStuff)

        for i in range(self.numDrawingStuff):
            glBindVertexArray(self.drawingStuffVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.drawingStuffVBO[i])
            glBufferData(GL_ARRAY_BUFFER, self.drawingStuffVerticesList[i].nbytes, self.drawingStuffVerticesList[i], GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.drawingStuffEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.drawingStuffIndicesList[i].nbytes, self.drawingStuffIndicesList[i], GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.drawingStuffVerticesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(0))

            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.drawingStuffVerticesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(self.drawingStuffVerticesList[i].itemsize * 3))

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)        

        #self.debugMat = glGetFloatv(GL_MODELVIEW_MATRIX)
        #cullFaceMode =  glGetIntegerv(GL_CULL_FACE_MODE)

    def MakeFont(self, imguiFont, fontPath = None):
        if fontPath == None:
            self.smallFont = Font('../../Resource/Font/comic.ttf', 10)
            self.font = Font('../../Resource/Font/comic.ttf', 14)
            self.largeFont = Font('../../Resource/Font/comic.ttf', 21)            

            self.smallFont.MakeFontTextureWithGenList()
            self.font.MakeFontTextureWithGenList()
            self.largeFont.MakeFontTextureWithGenList()

        self.imguiFont = imguiFont

    def AddObject(self, object):
        self.objects.append(object)        
        
    def AddSpecificProgramArgs(self, *args):
        self.specificProgramArgs.append(args)

    def ClearSpecificProgramArgs(self):
        self.specificProgramArgs.clear()

    def WriteLog(self, text):
        self.logFile.write('[' + time.strftime('%Y.%m.%d : %H.%M.%S') + ']' + ' ')
        self.logFile.write(text)
        self.logFile.write('\n')

        self.logFile.flush()

    def UpdateAboutKeyInput(self):
        numObjects = len(self.objects)

        if gInputManager.GetKeyState(glfw.KEY_SPACE) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_SPACE)
            gInputManager.SetKeyState(glfw.KEY_SPACE, False)    

        elif gInputManager.GetKeyState(glfw.KEY_1) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_1)            
            gInputManager.SetKeyState(glfw.KEY_1, False)
        elif gInputManager.GetKeyState(glfw.KEY_2) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_2)
            gInputManager.SetKeyState(glfw.KEY_2, False)
        elif gInputManager.GetKeyState(glfw.KEY_3) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_3)
            gInputManager.SetKeyState(glfw.KEY_3, False)
        elif gInputManager.GetKeyState(glfw.KEY_4) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_4)
            gInputManager.SetKeyState(glfw.KEY_4, False)
        elif gInputManager.GetKeyState(glfw.KEY_5) == True:
            self.cameraSailingSpeed -= 0.1
            if self.cameraSailingSpeed < 0.1:
                self.cameraSailingSpeed = 0.1
            gInputManager.SetKeyState(glfw.KEY_5, False)
        elif gInputManager.GetKeyState(glfw.KEY_6) == True:
            self.cameraSailingSpeed += 0.1
            if self.cameraSailingSpeed > 1.0:
                self.cameraSailingSpeed = 1.0
            gInputManager.SetKeyState(glfw.KEY_6, False)

        elif gInputManager.GetKeyState(glfw.KEY_B) == True:
            self.debug = not self.debug
            self._InitializeLog()
            gInputManager.SetKeyState(glfw.KEY_B, False)        
        elif gInputManager.GetKeyState(glfw.KEY_F) == True:
            self.specificProgramInfo = not self.specificProgramInfo
            gInputManager.SetKeyState(glfw.KEY_F, False)        
        elif gInputManager.GetKeyState(glfw.KEY_I) == True:
            self.programInfo = not self.programInfo                
            gInputManager.SetKeyState(glfw.KEY_I, False)
        elif gInputManager.GetKeyState(glfw.KEY_L) == True:
            self.enableCameraSailing = not self.enableCameraSailing
            if self.enableCameraMove == False:
                self.enableCameraSailing = False
            gInputManager.SetKeyState(glfw.KEY_L, False)
        elif gInputManager.GetKeyState(glfw.KEY_P) == True:
            self.pause = not self.pause
            gInputManager.SetMouseEntered(False)
            gInputManager.SetKeyState(glfw.KEY_P, False)
        elif gInputManager.GetKeyState(glfw.KEY_R) == True:
            for i in range(numObjects):
                self.objects[i].Restart()
            gInputManager.SetKeyState(glfw.KEY_R, False)
        elif gInputManager.GetKeyState(glfw.KEY_V) == True:
            self.view3D = not self.view3D
            for i in range(numObjects):
                self.objects[i].Restart()
            gInputManager.SetKeyState(glfw.KEY_V, False)
        elif gInputManager.GetKeyState(glfw.KEY_X) == True:
            self.drawAxes = not self.drawAxes
            if self.view3D == False:
                self.drawAxes = False
            gInputManager.SetKeyState(glfw.KEY_X, False)

        if gInputManager.GetKeyState(glfw.KEY_LEFT) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_LEFT)
        if gInputManager.GetKeyState(glfw.KEY_RIGHT) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_RIGHT)  
        if gInputManager.GetKeyState(glfw.KEY_UP) == True:            
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_UP)
        if gInputManager.GetKeyState(glfw.KEY_DOWN) == True:
            for i in range(numObjects):
                self.objects[i].UpdateAboutKeyInput(glfw.KEY_DOWN)            

    def UpdateAboutMouseInput(self):
        numObjects = len(self.objects)       

        if gInputManager.GetMouseButtonClick(glfw.MOUSE_BUTTON_LEFT) == True:
            lastMousePosOnClick = gInputManager.GetLastMousePosOnClick()
            for i in range(numObjects):
                self.objects[i].UpdateAboutMouseInput(glfw.MOUSE_BUTTON_LEFT, lastMousePosOnClick)
            
    def Update(self, deltaTime):
        self.deltaTime = deltaTime

        #if gSceneManager.GetDebug() == True:
        #    self.WriteLog('deltaTime : {0}'.format(self.deltaTime))        

        if self.controlFPS == True:
            self.elapsedTime += self.deltaTime

            if self.elapsedTime < self.oneFrameTime:                
                return        
        
        self.enableRender = True        

        self.UpdateAboutKeyInput()

        self.UpdateAboutMouseInput()

        if self.view3D == True and self.enableCameraMove:
            self.SetCameraPos()            

        if self.pause == True:
            return

        numObjects = len(self.objects)

        for i in range(numObjects):
            if self.controlFPS == True:
                self.objects[i].Update(self.elapsedTime)
            else:
                self.objects[i].Update(deltaTime)        

        if self.dirty == False:
            return  

        self.view3DMat = self.camera.GetViewMat()
        self.coordAxesViewMat = self.camera.GetViewMat()
        
        self.dirty = False        

    def PostUpdate(self, deltaTime):
        if gInputManager.GetKeyState(glfw.KEY_8) == True:
            if self.controlFPS == True:
                self.FPS -= 5
                if self.FPS <= 0:
                    self.FPS = 1

                self.oneFrameTime = 1.0 / self.FPS
                self.elapsedTime = 0.0
                self.enableRender = False

            gInputManager.SetKeyState(glfw.KEY_8, False)

        if gInputManager.GetKeyState(glfw.KEY_9) == True:
            if self.controlFPS == True:
                self.FPS = int(self.FPS / 5) * 5 + 5
                if self.FPS > 100:
                    self.FPS = 100

                self.oneFrameTime = 1.0 / self.FPS
                self.elapsedTime = 0.0
                self.enableRender = False        

            gInputManager.SetKeyState(glfw.KEY_9, False)        

        if gInputManager.GetKeyState(glfw.KEY_0) == True:
            self.controlFPS = not self.controlFPS

            if self.controlFPS == True:
                self.elapsedTime = 0.0        
                self.enableRender = False

            gInputManager.SetKeyState(glfw.KEY_0, False)

        if self.enableRender == True:
            self.elapsedTime = 0.0
            self.enableRender = False
        
    def Draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(self.screenPos[0][0], self.screenPos[0][1], self.screenSize[0], self.screenSize[1])

        self._DrawObjects()

        glViewport(0, 0, self.displaySize[0], self.displaySize[1])

        self._DrawGUI()

    def Finish(self):
        if self.debug == True or self.startLog == True:
            self.WriteLog('LOG End')

    def _InitializeDrawingStuff(self):
        self.screenPos.clear()

        screenLbPosX = int((self.displaySize[0] - self.screenSize[0]) / 2.0)
        screenLbPosY = 20
        
        screenLbPos = [screenLbPosX, screenLbPosY]
        screenRtPos = []
        screenRtPos.append(screenLbPos[0] + self.screenSize[0])
        screenRtPos.append(screenLbPos[1] + self.screenSize[1])

        self.screenPos.append(screenLbPos)
        self.screenPos.append(screenRtPos)

        imguiPos = []
        imguiSize = []

        imguiInterval = 5

        imguiPos.append(imguiInterval)
        imguiPos.append(self.displaySize[1] - self.screenPos[1][1] + imguiInterval)

        imguiSize.append(int((self.displaySize[0] - self.screenSize[0]) / 2.0) - imguiInterval * 2)
        imguiSize.append(self.displaySize[1] - self.screenPos[0][1] - imguiInterval - imguiPos[1])

        self.imguiPos.append([imguiPos[0], imguiPos[1]])
        self.imguiSize.append([imguiSize[0], imguiSize[1]])

        imguiPos[0] = self.screenPos[1][0] + imguiInterval
        imguiPos[1] = self.displaySize[1] - self.screenPos[1][1] + imguiInterval

        imguiSize[0] = int((self.displaySize[0] - self.screenSize[0]) / 2.0) - imguiInterval * 2
        imguiSize[1] = self.displaySize[1] - self.screenPos[0][1] - imguiInterval - imguiPos[1]

        self.imguiPos.append([imguiPos[0], imguiPos[1]])
        self.imguiSize.append([imguiSize[0], imguiSize[1]])

        coordAxesVerticesData = [
            0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0,
            1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0,

            0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0,
            0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0,

            0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0,
            0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0
            ]

        coordAxesIndicesData = [
            0, 1,
            2, 3,
            4, 5
            ]

        self.coordAxesVertices = np.array(coordAxesVerticesData, dtype = np.float32)
        self.coordAxesIndices = np.array(coordAxesIndicesData, dtype = np.uint32)

        startPos = [self.screenPos[0][0] + 10, self.screenPos[1][1] - 10]
        interval = [3.0, 5.0, 200.0]
        sideLength = interval[0] * 2 + interval[1] * 2 + interval[2]

        squarePos = []
        squarePos.append(startPos)
        squarePos.append([startPos[0] + sideLength, startPos[1]])
        squarePos.append([startPos[0] + sideLength, startPos[1] - sideLength])
        squarePos.append([startPos[0], startPos[1] - sideLength])

        programInfoAreaVerticesData = [
            squarePos[0][0] + interval[0] + interval[1], squarePos[0][1], 9.0, 1.0, 1.0, 1.0, 1.0,
            squarePos[1][0] - interval[0] - interval[1], squarePos[1][1], 9.0, 1.0, 1.0, 1.0, 1.0,
            squarePos[0][0] + interval[0] + interval[1], squarePos[0][1] - interval[0], 9.0, 1.0, 1.0, 1.0, 1.0,
            squarePos[1][0] - interval[0] - interval[1], squarePos[1][1] - interval[0], 9.0, 1.0, 1.0, 1.0, 1.0,

            squarePos[1][0], squarePos[1][1] - interval[0] - interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[2][0], squarePos[2][1] + interval[0] + interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[1][0] - interval[0], squarePos[1][1] - interval[0] - interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[2][0] - interval[0], squarePos[2][1] + interval[0] + interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,

            squarePos[2][0] - interval[0] - interval[1], squarePos[2][1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[3][0] + interval[0] + interval[1], squarePos[3][1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[2][0] - interval[0] - interval[1], squarePos[2][1] + interval[0], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[3][0] + interval[0] + interval[1], squarePos[3][1] + interval[0], 9.0, 0.0, 0.0, 1.0, 0.8,

            squarePos[3][0], squarePos[3][1] + interval[0] + interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[0][0], squarePos[0][1] - interval[0] - interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[3][0] + interval[0], squarePos[3][1] + interval[0] + interval[1], 9.0, 0.0, 0.0, 1.0, 0.8,
            squarePos[0][0] + interval[0], squarePos[0][1] - interval[0] - interval[1], 9.0, 0.0, 0.0, 1.0, 0.8            
            ]
        
        programInfoAreaIndicesData = [
            0, 1,
            2, 3,

            4, 5,
            6, 7,

            8, 9,
            10, 11,

            12, 13,
            14, 15
            ]

        self.programInfoAreaVertices = np.array(programInfoAreaVerticesData, dtype = np.float32)
        self.programInfoAreaIndices = np.array(programInfoAreaIndicesData, dtype = np.uint32)

        self.drawingStuffVerticesList.append(self.coordAxesVertices)
        self.drawingStuffVerticesList.append(self.programInfoAreaVertices)

        self.drawingStuffIndicesList.append(self.coordAxesIndices)
        self.drawingStuffIndicesList.append(self.programInfoAreaIndices)        

    def _InitializeColors(self):
        self.colors['DefaultColor_0'] = [1.0, 1.0, 1.0]
        self.colors['DefaultColor_1'] = [0.0, 0.0, 0.0]
        self.colors['DefaultColor_2'] = [1.0, 0.0, 0.0]
        self.colors['DefaultColor_3'] = [0.0, 1.0, 0.0]
        self.colors['DefaultColor_4'] = [0.0, 0.0, 1.0]
        self.colors['DefaultColor_5'] = [0.8, 0.3, 0.5]
        self.colors['DefaultColor_6'] = [0.3, 0.8, 0.5]
        self.colors['DefaultColor_7'] = [0.2, 0.3, 0.98]

        self.colors['ObjectColor_0'] = [1.0, 0.0, 0.0]
        self.colors['ObjectColor_1'] = [0.0, 0.76, 0.0]
        self.colors['ObjectColor_2'] = [0.15, 0.18, 0.85]
        self.colors['ObjectColor_3'] = [0.9, 0.73, 0.0]
        self.colors['ObjectColor_4'] = [0.95, 0.0, 0.89]
        self.colors['ObjectColor_5'] = [0.0, 0.9, 0.91]
        self.colors['ObjectColor_6'] = [1.0, 0.56, 0.0]

    def _InitializeLog(self):
        if self.logFile != None:
            return

        curPath = os.getcwd()
        curPath = curPath.replace('\\', '/')
        curPath += "/log.txt"

        self.logFile = open(curPath, 'w')

        self.WriteLog('LOG Start')
        self.startLog = True

    def _Initialize(self):
        self._InitializeDrawingStuff()

        self._InitializeColors()

    def _DrawCoordAxes(self):
        if self.view3D == False or self.drawAxes == False:
            return

        coordAxesViewportSize = [40, 40]

        glViewport(self.screenPos[1][0] - coordAxesViewportSize[0] - 10, self.screenPos[1][1] - coordAxesViewportSize[1] - 10, coordAxesViewportSize[0], coordAxesViewportSize[1])

        self.coordAxesViewMat[3].x = 0.0
        self.coordAxesViewMat[3].y = 0.0
        self.coordAxesViewMat[3].z = -2.0

        self.shaders[Index.SHADER_DEFAULT].Use()
        
        self.shaders[Index.SHADER_DEFAULT].SetMat4('prjMat', self.perspectivePrjMat)
        self.shaders[Index.SHADER_DEFAULT].SetMat4('viewMat', self.coordAxesViewMat)

        glLineWidth(2.0)

        glBindVertexArray(self.drawingStuffVAO[0])
        glDrawElements(GL_LINES, len(self.drawingStuffIndicesList[0]), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)

        glViewport(0, 0, self.displaySize[0], self.displaySize[1])

    def _DrawObjects(self):
        numObjects = len(self.objects)

        if self.view3D == True:
            prjMat = self.perspectivePrjMat
            viewMat = self.view3DMat            
        else:
            prjMat = self.orthoPrjMat
            viewMat = self.view2DMat

        for i in range(len(self.shaders)):
            self.shaders[i].Use()            
            self.shaders[i].SetMat4('prjMat', prjMat)
            self.shaders[i].SetMat4('viewMat', viewMat)

        for i in range(numObjects):
            self.objects[i].Draw()

    def _DrawGUI(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

        glEnable(GL_BLEND)

        glDisable(GL_DEPTH_TEST)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.shaders[Index.SHADER_DEFAULT].Use()

        self.shaders[Index.SHADER_DEFAULT].SetMat4('modelMat', self.modelMat)

        self._DrawCoordAxes()

        self._DrawProgramInfoArea()        

        glUseProgram(0)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        glOrtho(0, self.displaySize[0], 0, self.displaySize[1], -10.0, 10.0)        

        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_TEXTURE_2D)

        glDisable(GL_CULL_FACE)

        self._DrawProgramInfo()

        self._DrawSpecificProgramInfo()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glPopAttrib()
       
    def _DrawProgramInfoArea(self):
        if self.programInfo == False:
            return

        self.shaders[Index.SHADER_DEFAULT].Use()

        self.shaders[Index.SHADER_DEFAULT].SetMat4('prjMat', self.GUIPrjMat)
        self.shaders[Index.SHADER_DEFAULT].SetMat4('viewMat', self.view2DMat)       
        
        glLineWidth(1.0)
                
        glBindVertexArray(self.drawingStuffVAO[1])
        glDrawElements(GL_LINES, len(self.drawingStuffIndicesList[1]), GL_UNSIGNED_INT, None)        

        glBindVertexArray(0)        
       
    def _DrawProgramInfo(self):
        if self.programInfo == False:
            return

        glPushMatrix()
        glLoadIdentity()

        font = self.smallFont
        
        texId = font.GetTexId()

        glBindTexture(GL_TEXTURE_2D, texId)
        
        color = self.GetColor('DefaultColor_', 6)
        glColor(color[0], color[1], color[2], 1.0)

        infoText = []
        infoTextIndex = 0
        infoFPSText = ". FPS"

        if self.controlFPS == True:
            infoFPSText += ".On(8, 9; 0)"
        else:
            infoFPSText += ".Off(0)"

        infoText.append(infoFPSText + ' : {0: 0.2f}'.format(0.0))
        
        if self.controlFPS == True:
            if self.elapsedTime != 0.0:
                infoText[infoTextIndex] = infoFPSText + " : {0: 0.2f} ({1})".format(1.0 / self.elapsedTime, self.FPS)
                #print('.FPS: {0: 0.2f} ({1})'.format(1.0 / self.elapsedTime, self.FPS))
        else:
            if self.deltaTime != 0.0:
                infoText[infoTextIndex] = infoFPSText + " : {0: 0.2f}".format(1.0 / self.deltaTime)
                #print('.FPS: {0: 0.2f}'.format(1.0 / deltaTime))            

        infoText.append('. ViewMode(V) : ')
        infoTextIndex += 1

        if self.view3D == True:
            infoText[infoTextIndex] += "3D"
        else:
            infoText[infoTextIndex] += "2D"

        infoText.append('.    DrawAxes(X) : ')
        infoTextIndex += 1

        if self.drawAxes == True:
            infoText[infoTextIndex] += "On"
        else:
            infoText[infoTextIndex] += "Off"        

        infoText.append('. Pause(P) : ')
        infoTextIndex += 1
        
        if self.pause == True:
            infoText[infoTextIndex] += "On"
        else:
            infoText[infoTextIndex] += "Off"

        infoText.append('. CameraMove(M.R) : ')
        infoTextIndex += 1
        
        if self.enableCameraMove == True:
            infoText[infoTextIndex] += "On"
        else:
            infoText[infoTextIndex] += "Off"

        infoText.append('.    SailingDir')
        infoTextIndex += 1

        if self.enableCameraSailing == True:
            infoText[infoTextIndex] += "(5, 6; L) : On ({0: 0.1f})".format(self.cameraSailingSpeed)
        else:
            infoText[infoTextIndex] += "(L) : Off"        

        infoText.append('. Debug(B) : ')
        infoTextIndex += 1
        
        if self.debug == True:
            infoText[infoTextIndex] += "On"
        else:
            infoText[infoTextIndex] += "Off"

        textPosX = self.screenPos[0][0] + 20
        textPosY = self.screenPos[1][1] - 25

        for i in range(self.numProgramInfoElement):
            glTranslate(textPosX, textPosY, 0.0)

            glListBase(font.GetListOffset())
            glCallLists([ord(c) for c in infoText[i]])        

            glPopMatrix()
            glPushMatrix()
            glLoadIdentity()

            if i == self.numProgramInfoElement - 2:                
                textPosY -= 105.0
            else:
                textPosY -= 15.0

        glPopMatrix()

    def _DrawSpecificProgramInfo(self):
        if self.specificProgramInfo == False:
            return
        
        glPushMatrix()
        glLoadIdentity()        

        color = []
        textPos = [0.0, 0.0]
        textIntervalY = 0.0
        font = None
        infoText = []
        numInfoTexts = 0

        for i in range(len(self.specificProgramArgs)):
            args = self.specificProgramArgs[i]

            color = args[Index.SPECIFIC_PROGRAM_INFO_COLOR]
            glColor(color[0], color[1], color[2], 1.0)

            textPos[0] = args[Index.SPECIFIC_PROGRAM_INFO_TEXT_POS][0]
            textPos[1] = args[Index.SPECIFIC_PROGRAM_INFO_TEXT_POS][1]
            textIntervalY = args[Index.SPECIFIC_PROGRAM_INFO_TEXT_INTERVAL]
            numInfoTexts = args[Index.SPECIFIC_PROGRAM_INFO_NUM_TEXTS]

            infoText = args[Index.SPECIFIC_PROGRAM_INFO_TEXT_START : ]

            if 'Large' == args[Index.SPECIFIC_PROGRAM_INFO_FONT_SIZE]:
                font = self.largeFont
            elif 'Medium' == args[Index.SPECIFIC_PROGRAM_INFO_FONT_SIZE]:
                font = self.font

            texId = font.GetTexId()
            glBindTexture(GL_TEXTURE_2D, texId)

            for i in range(numInfoTexts):
                glTranslate(textPos[0], textPos[1], 0.0)               

                glListBase(font.GetListOffset())
                glCallLists([ord(c) for c in infoText[i]])        

                glPopMatrix()
                glPushMatrix()
                glLoadIdentity()
            
                textPos[1] -= textIntervalY        

        glPopMatrix()

class InputManager:
    def __init__(self):
        self.mouseEntered = False

        self.mouseButtonClick = [False, False, False]
        self.lastMousePos = [-1, -1]
        self.lastMousePosOnClick = [-1, -1]

        self.keys = {}

    def GetMouseEntered(self):
        return self.mouseEntered

    def SetMouseEntered(self, value):
        self.mouseEntered = value

    def GetMouseButtonClick(self, key):
        return self.mouseButtonClick[key]

    def SetMouseButtonClick(self, key, value):
        self.mouseButtonClick[key] = value

    def GetLastMousePos(self):
        return self.lastMousePos

    def SetLastMousePos(self, value):
        self.lastMousePos = value    

    def GetLastMousePosOnClick(self):
        return self.lastMousePosOnClick

    def SetLastMousePosOnClick(self, value):
        self.lastMousePosOnClick = value

    def GetKeyState(self, key):        
        if key in self.keys.keys():            
            return self.keys[key]

    def SetKeyState(self, key, value):
        self.keys[key] = value

class Camera:
    def __init__(self, cameraPos = None):
        if cameraPos == None:
            self.cameraPos = glm.vec3(0.0, 0.0, 10.0)
        else:
            self.cameraPos = cameraPos
            
        self.cameraFront = glm.vec3(0.0, 0.0, -1.0)
        self.cameraUp = glm.vec3(0.0, 1.0, 0.0)
        self.cameraRight = glm.vec3(1.0, 0.0, 0.0)
        self.cameraWorldUp = glm.vec3(0.0, 1.0, 0.0)

        self.pitch = 0.0
        self.yaw = 180.0

        self.mouseSensitivity = 0.1

        self.UpdateCameraVectors()

    def GetPos(self):
        return self.cameraPos

    def SetPos(self, cameraPos):
        self.cameraPos = cameraPos

    def GetViewMat(self):
        return glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)    

    def ProcessMouseMovement(self, xOffset, yOffset, constrainPitch = True):
        xOffset *= self.mouseSensitivity
        yOffset *= self.mouseSensitivity

        self.yaw += xOffset
        self.pitch += yOffset

        if constrainPitch == True:
            if self.pitch > 89.0:
                self.pitch = 89.0
            elif self.pitch < -89.0:
                self.pitch = -89.0

        self.UpdateCameraVectors()

    def ProcessKeyboard(self, direction, velocity):
        if direction == "FORWARD":
            self.cameraPos += self.cameraFront * velocity
        elif direction == "BACKWARD":
            self.cameraPos -= self.cameraFront * velocity
        elif direction == "LEFT":
            self.cameraPos += self.cameraRight * velocity
        elif direction == "RIGHT":
            self.cameraPos -= self.cameraRight * velocity
        elif direction == "UPWARD":
            self.cameraPos += self.cameraUp * velocity
        elif direction == "DOWNWARD":
            self.cameraPos -= self.cameraUp * velocity

    def UpdateCameraVectors(self):
        self.cameraFront.x = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        self.cameraFront.y = math.sin(glm.radians(self.pitch))
        self.cameraFront.z = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))

        self.cameraFront = glm.normalize(self.cameraFront)

        self.cameraRight = glm.normalize(glm.cross(self.cameraWorldUp, self.cameraFront))
        self.cameraUp = glm.normalize(glm.cross(self.cameraFront, self.cameraRight))

class ShaderFactory:
    def __init__(self):
        self.vertexShaderCode = {}
        self.fragmentShaderCode = {}

        self._Initialize()

    def CreateShader(self, vertexShaderCodeIndex, fragmentShaderCodeIndex):
        return Shader(self.vertexShaderCode[vertexShaderCodeIndex], self.fragmentShaderCode[fragmentShaderCodeIndex])

    def _Initialize(self):
        vertexDefaultShaderCode = """

        # version 330 core

        layout(location = 0) in vec3 aPos;
        layout(location = 1) in vec4 aColor;

        out vec4 color;

        uniform mat4 prjMat;
        uniform mat4 viewMat;
        uniform mat4 modelMat;

        void main()
        {
            gl_Position = prjMat * viewMat * modelMat * vec4(aPos, 1.0);

            color = aColor;
        }

        """

        fragmentDefaultShaderCode = """

        # version 330 core

        in vec4 color;

        out vec4 fragColor;        

        void main()
        {
            fragColor = color;            
        }

        """

        fragmentSimpleUseUniformColorShaderCode = """

        # version 330 core

        in vec4 color;

        out vec4 fragColor;

        uniform vec4 uniformColor;
        uniform bool useUniformColor;

        void main()
        {
            if (useUniformColor)
            {
                fragColor = uniformColor;
            }
            else
            {
                fragColor = color;
            }
        }


        """

        self.vertexShaderCode[Index.SHADER_CODE_DEFAULT] = vertexDefaultShaderCode
        
        self.fragmentShaderCode[Index.SHADER_CODE_DEFAULT] = fragmentDefaultShaderCode
        self.fragmentShaderCode[Index.SHADER_FRAGMENT_CODE_SIMPLE_USE_UNIFORMCOLOR] = fragmentSimpleUseUniformColorShaderCode

class Shader:
    def __init__(self, vertexShaderCode, fragmentShaderCode):
        self.program = None

        self._Initialize(vertexShaderCode, fragmentShaderCode)        

    def Use(self):
        glUseProgram(self.program)

    def SetBool(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        
        glUniform1i(loc, value)

    def SetFloat(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        
        glUniform1f(loc, value)

    def SetVec2(self, name, x, y):
        loc = glGetUniformLocation(self.program, name)
        
        glUniform2f(loc, x, y)

    def SetVec3(self, name, x, y, z):
        loc = glGetUniformLocation(self.program, name)
        
        glUniform3f(loc, x, y, z)

    def SetVec4(self, name, x, y, z, w):
        loc = glGetUniformLocation(self.program, name)
        
        glUniform4f(loc, x, y, z, w)

    def SetMat4(self, name, value):
        loc = glGetUniformLocation(self.program, name)

        value = np.array(value, dtype = np.float32)
        glUniformMatrix4fv(loc, 1, GL_TRUE, value)

    def _Initialize(self, vertexShaderCode, fragmentShaderCode):
        vertexShader = compileShader(vertexShaderCode, GL_VERTEX_SHADER)
        fragmentShader = compileShader(fragmentShaderCode, GL_FRAGMENT_SHADER)

        self.program = compileProgram(vertexShader, fragmentShader)

class Font:
    def __init__(self, fontPath, size):
        self.face = ft.Face(fontPath)
        self.face.set_char_size(size << 6)

        self.charsSize = (6, 16)
        self.charsAdvanceX = []

        self.maxCharHeight = 0
        self.charStartOffset = 32
        self.listOffset = -1
        self.texId = -1

        numChars = self.charsSize[0] * self.charsSize[1]

        self.charsAdvanceX = [0 for i in range(numChars)]

        advanceX, ascender, descender = 0, 0, 0
        charEndIndex = self.charStartOffset + numChars

        for c in range(self.charStartOffset, charEndIndex):
            self.face.load_char(chr(c), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT)

            self.charsAdvanceX[c - self.charStartOffset] = self.face.glyph.advance.x >> 6

            advanceX = max(advanceX, self.face.glyph.advance.x >> 6)
            ascender = max(ascender, self.face.glyph.metrics.horiBearingY >> 6)
            descender = max(descender, (self.face.glyph.metrics.height >> 6) - (self.face.glyph.metrics.horiBearingY >> 6))

        self.maxCharHeight = ascender + descender
        maxTotalAdvanceX = advanceX * self.charsSize[1]
        maxTotalHeight = self.maxCharHeight * self.charsSize[0]

        exponent = 0
        bitmapDataSize = [0, 0]

        while maxTotalAdvanceX > math.pow(2, exponent):
            exponent += 1
        bitmapDataSize[1] = int(math.pow(2, exponent))

        exponent = 0

        while maxTotalHeight > math.pow(2, exponent):
            exponent += 1
        bitmapDataSize[0] = int(math.pow(2, exponent))

        self.bitmapData = np.zeros((bitmapDataSize[0], bitmapDataSize[1]), dtype = np.ubyte)

        x, y, charIndex = 0, 0, 0

        for r in range(self.charsSize[0]):
            for c in range(self.charsSize[1]):
                self.face.load_char(chr(self.charStartOffset + r * self.charsSize[1] + c), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT)

                charIndex = r * self.charsSize[1] + c

                bitmap = self.face.glyph.bitmap
                x += self.face.glyph.bitmap_left
                y = r * self.maxCharHeight + ascender - self.face.glyph.bitmap_top

                self.bitmapData[y : y + bitmap.rows, x : x + bitmap.width].flat = bitmap.buffer

                x += self.charsAdvanceX[charIndex] - self.face.glyph.bitmap_left

            x = 0

    def GetTexId(self):
        return self.texId

    def GetListOffset(self):
        return self.listOffset

    def MakeFontTextureWithGenList(self):
        self.texId = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texId)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        self.bitmapData = np.flipud(self.bitmapData)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, self.bitmapData.shape[1], self.bitmapData.shape[0], 0,
                     GL_ALPHA, GL_UNSIGNED_BYTE, self.bitmapData)

        dx = 0.0
        dy = self.maxCharHeight / float(self.bitmapData.shape[0])

        listStartIndex = glGenLists(self.charsSize[0] * self.charsSize[1])
        self.listOffset = listStartIndex - self.charStartOffset

        for r in range(self.charsSize[0]):
            for c in range(self.charsSize[1]):
                glNewList(listStartIndex + r * self.charsSize[1] + c, GL_COMPILE)

                charIndex = r * self.charsSize[1] + c

                advanceX = self.charsAdvanceX[charIndex]
                dAdvanceX = advanceX / float(self.bitmapData.shape[1])

                glBegin(GL_QUADS)
                glTexCoord2f(dx, 1.0 - r * dy), glVertex3f(0.0, 0.0, 0.0)
                glTexCoord2f(dx + dAdvanceX, 1.0 - r * dy), glVertex3f(advanceX, 0.0, 0.0)
                glTexCoord2f(dx + dAdvanceX, 1.0 - (r + 1) * dy), glVertex3f(advanceX, -self.maxCharHeight, 0.0)
                glTexCoord2f(dx, 1.0 - (r + 1) * dy), glVertex3f(0.0, -self.maxCharHeight, 0.0)
                glEnd()

                glTranslate(advanceX, 0.0, 0.0)

                glEndList()

                dx += dAdvanceX

            glTranslatef(0.0, -self.maxCharHeight, 0.0)
            dx = 0.0

class Model:
    def __init__(self, modelPath, normalLineScale):
        self.vertices = []
        self.indices = []
        self.verticesExceptNoUse = []

        self.normals = []
        self.normalLineVertices = []
        self.normalLineIndices = []

        self.normalLineScale = normalLineScale

        self.numVertices = 0
        self.numVerticesExceptNoUse = 0
        self.numFaces = 0

        self._Initialize(modelPath)

    def GetVertices(self):
        return self.vertices

    def GetVerticesExceptNoUse(self):
        return self.verticesExceptNoUse

    def GetIndices(self):
        return self.indices

    def GetNormalLineVertices(self):
        return self.normalLineVertices

    def GetNormalLineIndices(self):
        return self.normalLineIndices

    def GetNumVertices(self):
        return self.numVertices

    def GetNumVerticesExceptNoUse(self):
        return self.numVerticesExceptNoUse

    def _Initialize(self, modelPath):
        with open(modelPath, mode = 'r') as fin:
            for line in fin:
                sl = line.split()

                if len(sl) == 0:
                    continue
                elif sl[0] in ['#']:
                    continue
                elif sl[0] == 'v':
                    for v in sl[1 : len(sl)]:
                        self.vertices.append(float(v))
                elif sl[0] == 'f':
                    for s in sl[1 : len(sl)]:
                        il = s.split('/')
                        self.indices.append(int(il[0]) - 1)

        self.numVertices = int(len(self.vertices) / 3)
        self.numFaces = int(len(self.indices) / 3)

        self.normals = np.zeros(len(self.vertices), dtype = np.float32)

        for i in range(self.numFaces):
            vertexAIndex = self.indices[i * 3 + 0]
            vertexBIndex = self.indices[i * 3 + 1]
            vertexCIndex = self.indices[i * 3 + 2]

            vecA = glm.vec3(self.vertices[vertexAIndex * 3 + 0], self.vertices[vertexAIndex * 3 + 1], self.vertices[vertexAIndex * 3 + 2])
            vecB = glm.vec3(self.vertices[vertexBIndex * 3 + 0], self.vertices[vertexBIndex * 3 + 1], self.vertices[vertexBIndex * 3 + 2])
            vecC = glm.vec3(self.vertices[vertexCIndex * 3 + 0], self.vertices[vertexCIndex * 3 + 1], self.vertices[vertexCIndex * 3 + 2])

            vecAB = vecB - vecA
            vecAC = vecC - vecA

            faceNormal = glm.normalize(glm.cross(vecAB, vecAC))

            self.normals[vertexAIndex * 3 + 0] += faceNormal.x
            self.normals[vertexAIndex * 3 + 1] += faceNormal.y
            self.normals[vertexAIndex * 3 + 2] += faceNormal.z

            self.normals[vertexBIndex * 3 + 0] += faceNormal.x
            self.normals[vertexBIndex * 3 + 1] += faceNormal.y
            self.normals[vertexCIndex * 3 + 2] += faceNormal.z

            self.normals[vertexCIndex * 3 + 0] += faceNormal.x
            self.normals[vertexCIndex * 3 + 1] += faceNormal.y
            self.normals[vertexCIndex * 3 + 2] += faceNormal.z

        useVertices = np.zeros(self.numVertices, dtype = np.bool8)

        for i in range(len(self.indices)):
            index = self.indices[i]
            useVertices[index] = True

        for i in range(self.numVertices):
            if useVertices[i] == True:
                vertexNormal = glm.vec3(self.normals[i * 3 + 0], self.normals[i * 3 + 1], self.normals[i * 3 + 2])
                vertexNormal = glm.normalize(vertexNormal)

                self.normals[i * 3 + 0] = vertexNormal.x
                self.normals[i * 3 + 1] = vertexNormal.y
                self.normals[i * 3 + 2] = vertexNormal.z

        for i in range(self.numVertices):
            if useVertices[i] == True:
                self.verticesExceptNoUse.append(self.vertices[i * 3 + 0])
                self.verticesExceptNoUse.append(self.vertices[i * 3 + 1])
                self.verticesExceptNoUse.append(self.vertices[i * 3 + 2])
                
        self.numVerticesExceptNoUse = int(len(self.verticesExceptNoUse) / 3)

        for i in range(self.numVertices):
            if useVertices[i] == True:
                self.normalLineVertices.append(self.vertices[i * 3 + 0])
                self.normalLineVertices.append(self.vertices[i * 3 + 1])
                self.normalLineVertices.append(self.vertices[i * 3 + 2])

                self.normalLineVertices.append(self.vertices[i * 3 + 0] + self.normals[i * 3 + 0] * self.normalLineScale)
                self.normalLineVertices.append(self.vertices[i * 3 + 1] + self.normals[i * 3 + 1] * self.normalLineScale)
                self.normalLineVertices.append(self.vertices[i * 3 + 2] + self.normals[i * 3 + 2] * self.normalLineScale)
        
                self.normalLineIndices.append(i * 2 + 0)
                self.normalLineIndices.append(i * 2 + 1)
        

gSceneManager = SceneManager(True)
gInputManager = InputManager()

gShaderFactory = ShaderFactory()


class TestProgram:
    def __init__(self, programName, programNamePos):
        self.programName = programName
        self.programNamePos = programNamePos

        self.selectedObjectKey = "None"
        self.objectsDataDict = {}

        self.selectedModelKey = "None"
        self.models = []
        self.modelsDataDict = {}
        
        self.selectedTestExampleKey = "None"
        self.testExamplesDict = {}        

        self.GUIObjectsVerticesList = []
        self.GUIObjectsIndicesList = []

        self.imguiHierarchy = {}
        self.imguiInspector = {}

        self.rotDegree = 0.0
        self.rotSpeed = 20.0        
        
        self.GUIModelMat = glm.mat4()

        self.imguiTabItemFlags = imgui.TAB_ITEM_SET_SELECTED        
        
        self.numVertexComponentsInModel = 3
        self.numVertexComponents = 7
        self.numVertexComponentsWithTexCoord = 9        
        
        self.numObjects = 0

        self.objectsVAO = None
        self.objectsVBO = None
        self.objectsEBO = None

        self.numModels = 0

        self.modelsVAO = None
        self.modelsVBO = None
        self.modelsEBO = None

        self.modelsVerticesExceptNoUseVAO = None
        self.modelsVerticesExceptNoUseVBO = None

        self.modelsNormalVAO = None
        self.modelsNormalVBO = None
        self.modelsNormalEBO = None
        
        self.numGUIObjects = 0

        self.GUIObjectsVAO = None
        self.GUIObjectsVBO = None
        self.GUIObjectsEBO = None

        self._Initialize()       
        
    def GetModels(self):
        return self.models

    def GetModelsDataDict(self):
        return self.modelsDataDict

    def RegistTestExample(self, key, testExampleFunc):
        self.testExamplesDict[key] = testExampleFunc
        self.imguiInspector['TestExample'][key] = False

    def Restart(self):
        self._Initialize()        

    def UpdateAboutKeyInput(self, key, value = True):
        pass

    def UpdateAboutMouseInput(self, button, pos):
        pass            

    def Update(self, deltaTime):
        if gSceneManager.GetView3D() != True:
            return

        self.rotDegree += deltaTime * self.rotSpeed

        if self.rotDegree > 360.0:
            self.rotDegree -= 360.0

        self._UpdateNewFrameImgui(deltaTime)

    def Draw(self):
        if gSceneManager.GetView3D() != True:
            return

        self._DrawObjects()
        
        self._DrawModels()

        displaySize = gSceneManager.GetDisplaySize()                
            
        glViewport(0, 0, displaySize[0], displaySize[1])    
        
        shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)
        
        shader.Use()
        shader.SetMat4('prjMat', gSceneManager.GetGUIPrjMat())
        shader.SetMat4('viewMat', gSceneManager.GetView2DMat())

        self._DrawGUI()

    def _Initialize(self):
        gSceneManager.SetView3D(True)

        self.rotDegree = 0.0
        self.drawingModelMat = glm.mat4()        
        
        self._InitializeObjects()

        self._InitializeModels()
        
        self._InitializeGUIObjects()

    def _InitializeCube(self):
        cubeVerticesData = [            
            # Front
            -0.5, -0.5, 0.5, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0,
            0.5, -0.5, 0.5, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0,
            0.5, 0.5, 0.5, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0,
            -0.5, 0.5, 0.5, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0,

            # Back
            0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0,
            -0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0,
            -0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0,
            0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0,

            # Left
            -0.5, -0.5, -0.5, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0,
            -0.5, -0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0,
            -0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
            -0.5, 0.5, -0.5, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0,

            # Right
            0.5, -0.5, 0.5, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0,
            0.5, -0.5, -0.5, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0,
            0.5, 0.5, -0.5, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0,
            0.5, 0.5, 0.5, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0,

            # Top
            -0.5, 0.5, 0.5, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.5, 0.5, 0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.5, 0.5, -0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            -0.5, 0.5, -0.5, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0,

            # Bottom
            -0.5, -0.5, -0.5, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0,
            0.5, -0.5, -0.5, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0,
            0.5, -0.5, 0.5, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0,
            -0.5, -0.5, 0.5, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0
            ]

        cubeIndicesData = [
            0, 1, 2, 2, 3, 0,
            4, 5, 6, 6, 7, 4,
            8, 9, 10, 10, 11, 8,
            12, 13, 14, 14, 15, 12,
            16, 17, 18, 18, 19, 16,
            20, 21, 22, 22, 23, 20
            ]

        return cubeVerticesData, cubeIndicesData

    def _InitializeObjects(self):
        self.objectsDataDict.clear()

        if self.numObjects > 0:
            glDeleteVertexArrays(self.numObjects, self.objectsVAO)
            glDeleteBuffers(self.numObjects, self.objectsVBO)
            glDeleteBuffers(self.numObjects, self.objectsEBO)

        self.numObjects = 0

        objectIndex = 0

        cubeDataDict = {}

        cubeVerticesData, cubeIndicesData = self._InitializeCube()

        self.numObjects += 1

        cubeDataDict['Index'] = objectIndex
        cubeDataDict['Vertices'] = np.array(cubeVerticesData, dtype = np.float32)
        cubeDataDict['Indices'] = np.array(cubeIndicesData, dtype = np.uint32)
        cubeDataDict['Position'] = [0.0, 0.0, 0.0]
        cubeDataDict['Rotation'] = [0.0, 0.0, 0.0]
        cubeDataDict['Scale'] = 2.0
        
        self.objectsDataDict['Cube'] = cubeDataDict

        self.numObjects += 1

        self.objectsVAO = glGenVertexArrays(self.numObjects)
        self.objectsVBO = glGenBuffers(self.numObjects)
        self.objectsEBO = glGenBuffers(self.numObjects)

        for key, value in self.objectsDataDict.items():
            objectDataDict = value

            i = objectDataDict['Index']
            vertices = objectDataDict['Vertices']
            indices = objectDataDict['Indices']

            glBindVertexArray(self.objectsVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.objectsVBO[i])
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * self.numVertexComponentsWithTexCoord, ctypes.c_void_p(0))

            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, vertices.itemsize * self.numVertexComponentsWithTexCoord, ctypes.c_void_p(vertices.itemsize * 3))

            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, vertices.itemsize * self.numVertexComponentsWithTexCoord, ctypes.c_void_p(vertices.itemsize * 7))

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def _InitializeModels(self):
        self.models.clear()
        self.modelsDataDict.clear()

        if self.numModels > 0:
            glDeleteVertexArrays(self.numModels, self.modelsVAO)
            glDeleteBuffers(self.numModels, self.modelsVBO)
            glDeleteBuffers(self.numModels, self.modelsEBO)

            glDeleteVertexArrays(self.numModels, self.modelsVerticesExceptNoUseVAO)
            glDeleteBuffers(self.numModels, self.modelsVerticesExceptNoUseVBO)

            glDeleteVertexArrays(self.numModels, self.modelsNormalVAO)
            glDeleteBuffers(self.numModels, self.modelsNormalVBO)
            glDeleteBuffers(self.numModels, self.modelsNormalEBO)

        self.numModels = 0

        if self.selectedTestExampleKey != "None":
            self.testExamplesDict[self.selectedTestExampleKey](self)
            self.numModels = len(self.models)
        else:
            modelKeys = []

            modelKeys.append('StanfordBunny')
            self.models.append(Model('../../Resource/Object/stanford-bunny.obj', 0.001))
            
            self.numModels = len(self.models)

            for i in range(self.numModels):
                modelDataDict = {}

                modelDataDict['Index'] = i
                modelDataDict['Vertices'] = np.array(self.models[i].GetVertices(), dtype = np.float32)
                modelDataDict['Indices'] = np.array(self.models[i].GetIndices(), dtype = np.uint32)
                modelDataDict['VerticesExceptNoUse'] = np.array(self.models[i].GetVerticesExceptNoUse(), dtype = np.float32)
                modelDataDict['NormalVertices'] = np.array(self.models[i].GetNormalLineVertices(), dtype = np.float32)
                modelDataDict['NormalIndices'] = np.array(self.models[i].GetNormalLineIndices(), dtype = np.uint32)
                modelDataDict['Position'] = [0.0, 0.0, 0.0]
                modelDataDict['Rotation'] = [0.0, 0.0, 0.0]
                modelDataDict['Scale'] = 1.0

                self.modelsDataDict[modelKeys[i]] = modelDataDict
            
            self.modelsDataDict['StanfordBunny']['Position'] = [0.5, -2.0, 6.0]
            self.modelsDataDict['StanfordBunny']['Rotation'] = [0.0, 0.0, 0.0]
            self.modelsDataDict['StanfordBunny']['Scale'] = 20.0
            
            self.numModels += 1

        self.modelsVAO = glGenVertexArrays(self.numModels)
        self.modelsVBO = glGenBuffers(self.numModels)
        self.modelsEBO = glGenBuffers(self.numModels)

        self.modelsVerticesExceptNoUseVAO = glGenVertexArrays(self.numModels)
        self.modelsVerticesExceptNoUseVBO = glGenBuffers(self.numModels)

        self.modelsNormalVAO = glGenVertexArrays(self.numModels)
        self.modelsNormalVBO = glGenBuffers(self.numModels)
        self.modelsNormalEBO = glGenBuffers(self.numModels)

        for key, value in self.modelsDataDict.items():
            modelDataDict = value

            i = modelDataDict['Index']
            vertices = modelDataDict['Vertices']
            indices = modelDataDict['Indices']
            verticesExceptNoUse = modelDataDict['VerticesExceptNoUse']
            normalVertices = modelDataDict['NormalVertices']
            normalIndices = modelDataDict['NormalIndices']

            glBindVertexArray(self.modelsVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.modelsVBO[i])
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.modelsEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * self.numVertexComponentsInModel, ctypes.c_void_p(0))

            glBindVertexArray(self.modelsVerticesExceptNoUseVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.modelsVerticesExceptNoUseVBO[i])
            glBufferData(GL_ARRAY_BUFFER, verticesExceptNoUse.nbytes, verticesExceptNoUse, GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, verticesExceptNoUse.itemsize * self.numVertexComponentsInModel, ctypes.c_void_p(0))

            glBindVertexArray(self.modelsNormalVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.modelsNormalVBO[i])
            glBufferData(GL_ARRAY_BUFFER, normalVertices.nbytes, normalVertices, GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.modelsNormalEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, normalIndices.nbytes, normalIndices, GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, normalVertices.itemsize * self.numVertexComponentsInModel, ctypes.c_void_p(0))            

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    
    def _InitializeGUIObjects(self):
        gSceneManager.ClearSpecificProgramArgs()

        self.GUIObjectsVerticesList.clear()
        self.GUIObjectsVerticesList.clear()

        if self.numGUIObjects > 0:
            glDeleteVertexArrays(self.numGUIObjects, self.GUIObjectsVAO)
            glDeleteBuffers(self.numGUIObjects, self.GUIObjectsVBO)
            glDeleteBuffers(self.numGUIObjects, self.GUIObjectsEBO)

        self.numGUIObjects = 0

        self.imguiHierarchy = {
            'TEST.A' : {'A.1' : 'A.1', 'A.2' : 'A.2', 'A.3' : 'A.3'},
            'TEST.B' : {'B.1' : 'B.1', 'B.1.1' : {'B.1.1' : 'B.1.1'}, 'B.1.1.1' : {'B.1.1.1' : {'B.1.1.1' : 'B.1.1.1', 'B.1.1.2' : 'B.1.1.2'}}},
            'TEST.C' : {'C.1' : 'C.1', 'C.1.1' : {'C.1.1' : 'C.1.1', 'C.1.2' : 'C.1.2'}, 'C.2' : 'C.2', 'C.3' : 'C.3'}
            }

        self.imguiInspector = {
            'Object' : {},
            'Model' : {},            
            'RenderElement' : {'Vertex' : False, 'Edge' : True, 'Face' : True, 'Normal' : False},
            'RenderViewType' : {'BackFace' : True, 'Lighting' : False},
            'TestExample' : {},
            'TestThing' : {}
            }

        self.selectedObjectKey = "None"

        for key in self.objectsDataDict.keys():
            self.imguiInspector['Object'][key] = False

        self.selectedModelKey = "None"

        for key in self.modelsDataDict.keys():
            self.imguiInspector['Model'][key] = False

        for key in self.testExamplesDict.keys():
            self.imguiInspector['TestExample'][key] = False

        if self.selectedTestExampleKey != "None":
            self.imguiInspector['TestExample'][self.selectedTestExampleKey] = True

        self.imguiTabItemFlags = imgui.TAB_ITEM_SET_SELECTED

        displaySize = gSceneManager.GetDisplaySize()
        screenPos = gSceneManager.GetScreenPos()        

        backgroundVerticesData = [
            0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[0][0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[0][0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,

            screenPos[1][0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[1][0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,

            0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], screenPos[0][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, screenPos[0][1], 5.0, 1.0, 0.0, 0.0, 0.5,

            0.0, screenPos[1][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], screenPos[1][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5
            ]

        backgroundIndicesData = [
            0, 1, 2, 2, 3, 0,
            4, 5, 6, 6, 7, 4,
            8, 9, 10, 10, 11, 8,
            12, 13, 14, 14, 15, 12
            ]

        self.GUIObjectsVerticesList.append(np.array(backgroundVerticesData, dtype = np.float32))
        self.GUIObjectsIndicesList.append(np.array(backgroundIndicesData, dtype = np.uint32))

        self.numGUIObjects += 1

        backgroundLineVerticesData = [
            0.0, screenPos[0][1], 8.0, 1.0, 1.0, 1.0, 1.0,
            displaySize[0], screenPos[0][1], 8.0, 1.0, 1.0, 1.0, 1.0,

            0.0, screenPos[1][1], 8.0, 1.0, 1.0, 1.0, 1.0,
            displaySize[0], screenPos[1][1], 8.0, 1.0, 1.0, 1.0, 1.0,

            screenPos[0][0], 0.0, 8.0, 1.0, 1.0, 1.0, 1.0,
            screenPos[0][0], displaySize[1], 8.0, 1.0, 1.0, 1.0, 1.0,

            screenPos[1][0], 0.0, 8.0, 1.0, 1.0, 1.0, 1.0,
            screenPos[1][0], displaySize[1], 8.0, 1.0, 1.0, 1.0, 1.0
            ]

        backgroundLineIndicesData = [
            0, 1,
            2, 3,
            4, 5,
            6, 7
            ]

        self.GUIObjectsVerticesList.append(np.array(backgroundLineVerticesData, dtype = np.float32))
        self.GUIObjectsIndicesList.append(np.array(backgroundLineIndicesData, dtype = np.uint32))

        self.numGUIObjects += 1        
        
        self.GUIObjectsVAO = glGenVertexArrays(self.numGUIObjects)
        self.GUIObjectsVBO = glGenBuffers(self.numGUIObjects)
        self.GUIObjectsEBO = glGenBuffers(self.numGUIObjects)

        for i in range(self.numGUIObjects):
            glBindVertexArray(self.GUIObjectsVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.GUIObjectsVBO[i])
            glBufferData(GL_ARRAY_BUFFER, self.GUIObjectsVerticesList[i].nbytes, self.GUIObjectsVerticesList[i], GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.GUIObjectsEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.GUIObjectsIndicesList[i].nbytes, self.GUIObjectsIndicesList[i], GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.GUIObjectsVerticesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(0))

            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.GUIObjectsVerticesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(self.GUIObjectsVerticesList[i].itemsize * 3))

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        gSceneManager.AddSpecificProgramArgs(gSceneManager.GetColor('DefaultColor_', 7), self.programNamePos, 0, 1, 'Medium', '# ' + self.programName)

    def _ImguiTextPreOrderRecursively(self, hierarchyDict, key, value, numSpace = 0):
        if isinstance(value, dict) == True:
            for sKey, sValue in hierarchyDict[key].items():
                if isinstance(sValue, dict) == True:
                    self._ImguiTextPreOrderRecursively(hierarchyDict[key], sKey, sValue, numSpace + 1)
                else:
                    sValueText = "".ljust(numSpace * 5) + str(sValue)
                    imgui.text(sValueText)
        else:
            valueText = "".ljust(numSpace * 5) + str(value)
            imgui.text(valueText)

    def _UpdateNewFrameImguiHierarchy(self, deletaTime):
        imguiSize = gSceneManager.GetImguiSize(Index.IMGUI_WINDOW_HIERARCHY)
        imguiPos = gSceneManager.GetImguiPos(Index.IMGUI_WINDOW_HIERARCHY)

        imguiFont = gSceneManager.GetImguiFont()

        imgui.set_window_position_labeled('Hierarchy', imguiPos[0], imguiPos[1], imgui.ONCE)
        imgui.set_window_size_named('Hierarchy', imguiSize[0], imguiSize[1], imgui.ONCE)

        imgui.push_font(imguiFont)

        with imgui.begin('Hierarchy', False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE):
            with imgui.begin_tab_bar('HierarchyTabBar'):
                if imgui.begin_tab_item('Hierarchy').selected:
                    for key, value in self.imguiHierarchy.items():
                        if imgui.tree_node(key):
                            self._ImguiTextPreOrderRecursively(self.imguiHierarchy, key, value)
                            imgui.tree_pop()
                    imgui.end_tab_item()

        imgui.pop_font()
        
    def _UpdateNewFrameImguiInspector(self, deltaTime):
        imguiSize = gSceneManager.GetImguiSize(Index.IMGUI_WINDOW_INSPECTOR)
        imguiPos = gSceneManager.GetImguiPos(Index.IMGUI_WINDOW_INSPECTOR)

        imguiFont = gSceneManager.GetImguiFont()        

        imgui.set_window_position_labeled('Inspector', imguiPos[0], imguiPos[1], imgui.ONCE)
        imgui.set_window_size_named('Inspector', imguiSize[0], imguiSize[1], imgui.ONCE)

        imgui.push_font(imguiFont)

        with imgui.begin('Inspector', False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE):
            with imgui.begin_tab_bar('InspectorTabBar'):
                if imgui.begin_tab_item('Object').selected:
                    if imgui.tree_node('Object', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        for key, value in self.imguiInspector['Object'].items():
                            clicked, value = imgui.checkbox(key, value)
                            self.imguiInspector['Object'][key] = value
                            if clicked == True:
                                if value == True:
                                    self.selectedObjectKey = key
                                else:
                                    self.selectedObjectKey = "None"
                        imgui.tree_pop()
                    if self.selectedObjectKey != "None":
                        if imgui.tree_node('Transformation (' + self.selectedObjectKey + ')', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                            values = self.objectsDataDict[self.selectedObjectKey]['Position']
                            _, values = imgui.slider_float3('Position', *values, min_value = -20.0, max_value = 20.0, format = '%0.2f')
                            self.objectsDataDict[self.selectedObjectKey]['Position'] = values

                            values = self.objectsDataDict[self.selectedObjectKey]['Rotation']
                            _, values = imgui.slider_float3('Rotation', *values, min_value = 0.0, max_value = 360.0, format = '%0.2f')
                            self.objectsDataDict[self.selectedObjectKey]['Rotation'] = values

                            value = self.objectsDataDict[self.selectedObjectKey]['Scale']
                            _, value = imgui.slider_float(' ', value, min_value = 0.01, max_value = 100.0, format = '%0.2f')
                            self.objectsDataDict[self.selectedObjectKey]['Scale'] = value
                            value = self.objectsDataDict[self.selectedObjectKey]['Scale']
                            _, value = imgui.input_float('Scale', value, step = 0.01, format = '%0.2f')
                            self.objectsDataDict[self.selectedObjectKey]['Scale'] = value
                            imgui.tree_pop()
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Model', flags = self.imguiTabItemFlags).selected:
                    if imgui.tree_node('Model', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        for key, value in self.imguiInspector['Model'].items():
                            clicked, value = imgui.checkbox(key, value)
                            self.imguiInspector['Model'][key] = value
                            if clicked == True:
                                if value == True:
                                    self.selectedModelKey = key
                                else:
                                    self.selectedModelKey = "None"
                        imgui.tree_pop()
                    if self.selectedModelKey != "None":
                        if imgui.tree_node('Transformation (' + self.selectedModelKey + ')', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                            values = self.modelsDataDict[self.selectedModelKey]['Position']
                            _, values = imgui.slider_float3('Position', *values, min_value = -20.0, max_value = 20.0, format = '%0.2f')
                            self.modelsDataDict[self.selectedModelKey]['Position'] = values

                            values = self.modelsDataDict[self.selectedModelKey]['Rotation']
                            _, values = imgui.slider_float3('Rotation', *values, min_value = 0.0, max_value = 360.0, format = '%0.2f')
                            self.modelsDataDict[self.selectedModelKey]['Rotation'] = values

                            value = self.modelsDataDict[self.selectedModelKey]['Scale']
                            _, value = imgui.slider_float(' ', value, min_value = 0.01, max_value = 100.0, format = '%0.2f')
                            self.modelsDataDict[self.selectedModelKey]['Scale'] = value
                            value = self.modelsDataDict[self.selectedModelKey]['Scale']
                            _, value = imgui.input_float('Scale', value, step = 0.01, format = '%0.2f')
                            self.modelsDataDict[self.selectedModelKey]['Scale'] = value
                            imgui.tree_pop()
                    self.imguiTabItemFlags = 0
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Render').selected:
                    if imgui.tree_node('Elememt', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        for key, value in self.imguiInspector['RenderElement'].items():
                            _, value = imgui.checkbox(key, value)
                            self.imguiInspector['RenderElement'][key] = value
                        imgui.tree_pop()
                    if imgui.tree_node('ViewType', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        for key, value in self.imguiInspector['RenderViewType'].items():
                            _, value = imgui.checkbox(key, value)
                            self.imguiInspector['RenderViewType'][key] = value
                        imgui.tree_pop()
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Test').selected:
                    if imgui.tree_node('Example', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        restart = False
                        for key, value in self.imguiInspector['TestExample'].items():
                            clicked, value = imgui.checkbox(key, value)
                            self.imguiInspector['TestExample'][key] = value
                            if clicked == True:
                                if value == True:
                                    self.selectedTestExampleKey = key
                                else:
                                    self.selectedTestExampleKey = "None"
                                restart = True

                        if restart == True:
                            self.Restart()
                        imgui.tree_pop()
                    imgui.separator()
                    imgui.text('Test Features')                    
                    imgui.end_tab_item()                    
        
        imgui.pop_font()

    def _UpdateNewFrameImgui(self, deltaTime):
        imgui.new_frame()

        self._UpdateNewFrameImguiHierarchy(deltaTime)

        self._UpdateNewFrameImguiInspector(deltaTime)

    def _DrawObjects(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for key, value in self.imguiInspector['Object'].items():
            if value == True:
                objectDataDict = self.objectsDataDict[key]

                i = objectDataDict['Index']
                indices = objectDataDict['Indices']
                position = objectDataDict['Position']
                rotation = objectDataDict['Rotation']
                scale = objectDataDict['Scale']

                transMat = glm.translate(glm.vec3(position[0], position[1], position[2]))

                #rotXMat = glm.rotate(glm.radians(rotation[0]), glm.vec3(1.0, 0.0, 0.0))
                #rotYMat = glm.rotate(glm.radians(rotation[1]), glm.vec3(0.0, 1.0, 0.0))
                #rotZMat = glm.rotate(glm.radians(rotation[2]), glm.vec3(0.0, 0.0, 1.0))
        
                rotXMat = glm.rotate(glm.radians(self.rotDegree), glm.vec3(1.0, 0.0, 0.0))
                rotYMat = glm.rotate(glm.radians(self.rotDegree), glm.vec3(0.0, 1.0, 0.0))
                rotZMat = glm.rotate(glm.radians(self.rotDegree), glm.vec3(0.0, 0.0, 1.0))

                #rotMat = glm.mat4()
                rotMat = rotZMat * rotYMat * rotXMat                
       
                scaleMat = glm.scale(glm.vec3(scale, scale, scale))

                modelMat = transMat * rotMat * scaleMat

                shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)

                shader.Use()
                shader.SetMat4('modelMat', modelMat)         

                glBindVertexArray(self.objectsVAO[i])
                glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)

        glPopAttrib()
        
    def _DrawModels(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_POINT_BIT | GL_LINE_BIT | GL_POLYGON_BIT)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for key, value in self.imguiInspector['Model'].items():
            if value == True:
                modelDataDict = self.modelsDataDict[key]

                i = modelDataDict['Index']                
                indices = modelDataDict['Indices']
                verticesExceptNoUse = modelDataDict['VerticesExceptNoUse']
                normalIndices = modelDataDict['NormalIndices']
                position = modelDataDict['Position']
                rotation = modelDataDict['Rotation']
                scale = modelDataDict['Scale']

                transMat = glm.translate(glm.vec3(position[0], position[1], position[2]))

                rotXMat = glm.rotate(glm.radians(rotation[0]), glm.vec3(1.0, 0.0, 0.0))
                rotYMat = glm.rotate(glm.radians(rotation[1]), glm.vec3(0.0, 1.0, 0.0))
                rotZMat = glm.rotate(glm.radians(rotation[2]), glm.vec3(0.0, 0.0, 1.0))
                
                #rotMat = glm.mat4()
                rotMat = rotZMat * rotYMat * rotXMat

                scaleMat = glm.scale(glm.vec3(scale, scale, scale))

                modelMat = transMat * rotMat * scaleMat

                shader = gSceneManager.GetShader(Index.SHADER_SIMPLE_USE_UNIFORMCOLOR)
        
                shader.Use()
                shader.SetMat4('modelMat', modelMat)        
                shader.SetBool('useUniformColor', True)        

                if self.imguiInspector['RenderElement']['Face'] == True:
                    glCullFace(GL_BACK)

                    shader.SetVec4('uniformColor', 1.0, 0.0, 0.0, 1.0)
                    glPolygonMode(GL_FRONT, GL_FILL)

                    glBindVertexArray(self.modelsVAO[i])
                    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

                if self.imguiInspector['RenderViewType']['BackFace'] == True:
                    glCullFace(GL_FRONT)

                    shader.SetVec4('uniformColor', 0.0, 1.0, 0.0, 1.0)
                    glPolygonMode(GL_BACK, GL_FILL)

                    glBindVertexArray(self.modelsVAO[i])
                    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

                if self.imguiInspector['RenderElement']['Edge'] == True:
                    glDisable(GL_CULL_FACE)

                    glEnable(GL_POLYGON_OFFSET_LINE)
                    #glPolygonOffset(self.imguiTest['factor'], self.imguiTest['units'])
                    glPolygonOffset(-0.5, 0.0)

                    shader.SetVec4('uniformColor', 1.0, 1.0, 1.0, 1.0)
                    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

                    glLineWidth(1.0)

                    glBindVertexArray(self.modelsVAO[i])
                    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

                if self.imguiInspector['RenderElement']['Vertex'] == True:
                    glEnable(GL_POINT_SMOOTH)
                    glPointSize(5.0)

                    shader.SetVec4('uniformColor', 0.0, 0.0, 1.0, 1.0)

                    glBindVertexArray(self.modelsVerticesExceptNoUseVAO[i])
                    glDrawArrays(GL_POINTS, 0, self.models[i].GetNumVerticesExceptNoUse())

                if self.imguiInspector['RenderElement']['Normal'] == True:
                    shader.SetVec4('uniformColor', 1.0, 1.0, 0.0, 1.0)

                    glLineWidth(1.0)

                    glBindVertexArray(self.modelsNormalVAO[i])
                    glDrawElements(GL_LINES, len(normalIndices), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)

        glPopAttrib()

    def _DrawGUI(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

        glDisable(GL_DEPTH_TEST)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ZERO)

        shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)

        shader.Use()
        shader.SetMat4('modelMat', self.GUIModelMat)
        shader.SetBool('useUniformColor', False)

        GUIObjectsIndex = 0
        
        glBindVertexArray(self.GUIObjectsVAO[GUIObjectsIndex])
        glDrawElements(GL_TRIANGLES, len(self.GUIObjectsIndicesList[GUIObjectsIndex]), GL_UNSIGNED_INT, None)        
        
        GUIObjectsIndex += 1

        glLineWidth(2.0)

        glBindVertexArray(self.GUIObjectsVAO[GUIObjectsIndex])
        glDrawElements(GL_LINES, len(self.GUIObjectsIndicesList[GUIObjectsIndex]), GL_UNSIGNED_INT, None)
        
        glBindVertexArray(0)

        glPopAttrib()


class FlockingSimulationIndex:
    OBJECT_BOID = 0
    OBJECT_BOID_PERCEPTION_CIRCLE = 1
    OBJECT_BOID_FORCE_DIRECTION = 2

    OBJECT_SHAPE_TRIANGLE = 0
    OBJECT_SHAPE_RECTANGLE = 1
    OBJECT_SHAPE_CIRCLE = 2
    OBJECT_SHAPE_FORCE_DIRECTION = 3

    GUI_OBJECT_BACKGROUND = 0
    GUI_OBJECT_BACKGROUND_LINE = 1

class Boid:
    perceptionRadius = {'Separation' : 25, 'Alignment' : 50, 'Cohesion' : 50}
    forceScale = {'Separation' : 1.0, 'Alignment' : 1.0, 'Cohesion' : 1.0}
    maxSpeed = 100.0
    maxForce = 50.0

    @staticmethod
    def GetPerceptionRadiusByBehaviorRule(behaviorRuleKey):
        return Boid.perceptionRadius[behaviorRuleKey]

    @staticmethod
    def SetPerceptionRadiusByBehaviorRule(behaviorRuleKey, perceptionRadius):
        Boid.perceptionRadius[behaviorRuleKey] = perceptionRadius

    @staticmethod
    def GetForceScaleByBehaviorRule(behaviorRuleKey):
        return Boid.forceScale[behaviorRuleKey]

    @staticmethod
    def SetForceScaleByBehaviorRule(behaviorRuleKey, forceScale):
        Boid.forceScale[behaviorRuleKey] = forceScale

    @staticmethod
    def GetMaxSpeed():
        return Boid.maxSpeed

    @staticmethod
    def SetMaxSpeed(maxSpeed):
        Boid.maxSpeed = maxSpeed

    @staticmethod
    def GetMaxForce():
        return Boid.maxForce

    @staticmethod
    def SetMaxForce(maxForce):
        Boid.maxForce = maxForce

    @staticmethod
    def GetNumVerticesByShape(objectShape = FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE):
        if objectShape == FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE:
            return 3
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_RECTANGLE:
            return 4
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE:
            return 36
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_FORCE_DIRECTION:
            return 4

    @staticmethod
    def GetNumIndicesByShape(objectShape = FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE):
        if objectShape == FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE:
            return 3
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_RECTANGLE:
            return 4
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE:
            return Boid.GetNumVerticesByShape(FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE) * 2
        elif objectShape == FlockingSimulationIndex.OBJECT_SHAPE_FORCE_DIRECTION:
            return 2

    def __init__(self, pos = None):
        self.vertices = []
        self.indices = []

        self.initialVertices = []

        self.headingAngleInRadians = 0.0
        self.initHeadingDir = glm.vec3(0.0, 1.0, 0.0)

        self.radius = 3.0

        self.behaviorRuleForce = {}
        
        self.acceleration = glm.vec3()
        self.velocity = glm.vec3()
        self.velocityScale = 100.0
        self.position = glm.vec3()

        self.numVertexComponents = 7

        self._Initialize(pos)

    def GetVertices(self):
        return self.vertices

    def GetIndices(self):
        return self.indices

    def GetVelocity(self):
        return self.velocity

    def GetPosition(self):
        return self.position

    def GetForceByBehaviorRule(self, behaviorRuleKey):
        return self.behaviorRuleForce[behaviorRuleKey]

    def SetColor(self, color):
        for i in range(Boid.GetNumVerticesByShape(FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE)):
            self.vertices[i * self.numVertexComponents + 3] = color[0]
            self.vertices[i * self.numVertexComponents + 4] = color[1]
            self.vertices[i * self.numVertexComponents + 5] = color[2]
            self.vertices[i * self.numVertexComponents + 6] = color[3]        

    def Flock(self, boids):
        self.behaviorRuleForce['Separation'] = self._Separation(boids)
        self.behaviorRuleForce['Alignment'] = self._Alignment(boids)
        self.behaviorRuleForce['Cohesion'] = self._Cohesion(boids)

        self.behaviorRuleForce['Separation'] *= Boid.GetForceScaleByBehaviorRule('Separation')
        self.behaviorRuleForce['Alignment'] *= Boid.GetForceScaleByBehaviorRule('Alignment')
        self.behaviorRuleForce['Cohesion'] *= Boid.GetForceScaleByBehaviorRule('Cohesion')

        self.acceleration += self.behaviorRuleForce['Separation']
        self.acceleration += self.behaviorRuleForce['Alignment']
        self.acceleration += self.behaviorRuleForce['Cohesion']

    def Update(self, deltaTime):
        self.velocity += self.acceleration * deltaTime

        if glm.length(self.velocity) > Boid.GetMaxSpeed():
            self.velocity = glm.normalize(self.velocity)
            self.velocity *= Boid.GetMaxSpeed()

        self.position += self.velocity * deltaTime

        self.acceleration *= 0.0

        transMat = glm.translate(glm.vec3(self.position.x, self.position.y, 0.0))

        normalVel = glm.normalize(self.velocity)
        self.headingAngleInRadians = glm.acos(glm.dot(normalVel, self.initHeadingDir))

        crossVec = glm.cross(self.initHeadingDir, normalVel)

        if crossVec.z < 0.0:
            self.headingAngleInRadians *= -1.0

        rotMat = glm.rotate(self.headingAngleInRadians, glm.vec3(0.0, 0.0, 1.0))        

        scaleMat = glm.mat4()

        modelMat = transMat * rotMat * scaleMat

        for i in range(Boid.GetNumVerticesByShape(FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE)):
            vertex = glm.vec3()

            vertex.x = self.initialVertices[i * self.numVertexComponents + 0]
            vertex.y = self.initialVertices[i * self.numVertexComponents + 1]
            vertex.z = self.initialVertices[i * self.numVertexComponents + 2]

            vertex = modelMat * vertex

            self.vertices[i * self.numVertexComponents + 0] = vertex.x
            self.vertices[i * self.numVertexComponents + 1] = vertex.y
            self.vertices[i * self.numVertexComponents + 2] = vertex.z

        self._CheckOffScreen()

    def _Initialize(self, pos):
        verticesData = [
            -self.radius, -self.radius * 2, 0.0, 1.0, 1.0, 1.0, 0.8,
            self.radius, -self.radius * 2, 0.0, 1.0, 1.0, 1.0, 0.8,
            0.0, self.radius * 2, 0.0, 1.0, 1.0, 1.0, 0.8
            ]

        indicesData = [
            0, 1, 2
            ]

        self.vertices = np.array(verticesData, dtype = np.float32)
        self.indices = np.array(indicesData, dtype = np.uint32)

        self.initialVertices = np.array(verticesData, dtype = np.float32)

        screenSize = gSceneManager.GetScreenSize()

        self.velocity = glm.vec3(random.random() - 0.5, random.random() - 0.5, 0.0)
        self.velocity = glm.normalize(self.velocity) * self.velocityScale

        if pos != None:
            self.position = glm.vec3(pos.x, pos.y, 0.0)
        else:
            self.position = glm.vec3(random.random() * screenSize[0], random.random() * screenSize[1], 0.0)

        self.behaviorRuleForce = {'Separtion' : 0.0, 'Alignment' : 0.0, 'Cohesion' : 0.0}

    def _CheckOffScreen(self):
        screenSize = gSceneManager.GetScreenSize()

        if self.position.x > screenSize[0] + 2 * self.radius:
            self.position.x = 2 * -self.radius
        elif self.position.x < 2 * -self.radius:
            self.position.x = screenSize[0] + 2 * self.radius

        if self.position.y > screenSize[1] + 2 * self.radius:
            self.position.y = 2 * -self.radius
        elif self.position.y < 2 * -self.radius:
            self.position.y = screenSize[1] + 2 * self.radius

    def _Separation(self, boids):
        perceptionRadius = Boid.GetPerceptionRadiusByBehaviorRule('Separation')
        steeringForce = glm.vec3()
        groupBoidsCnt = 0

        for i in range(len(boids)):
            if self != boids[i]:
                dis = glm.length(self.position - boids[i].GetPosition())

                if dis < perceptionRadius:
                    diffVec = self.position - boids[i].GetPosition()

                    if dis == 0.0:
                        dis = 0.001

                    diffVec /= dis

                    steeringForce += diffVec
                    groupBoidsCnt += 1

        if groupBoidsCnt > 0:
            steeringForce = glm.normalize(steeringForce)
            steeringForce *= Boid.GetMaxSpeed()
            steeringForce -= self.velocity

            if glm.length(steeringForce) > Boid.GetMaxForce():
                steeringForce = glm.normalize(steeringForce)
                steeringForce *= Boid.GetMaxForce()

        return steeringForce

    def _Alignment(self, boids):
        perceptionRadius = Boid.GetPerceptionRadiusByBehaviorRule('Alignment')
        steeringForce = glm.vec3()
        groupBoidsCnt = 0

        for i in range(len(boids)):
            if self != boids[i]:
                dis = glm.length(self.position - boids[i].GetPosition())

                if dis < perceptionRadius:
                    steeringForce += boids[i].GetVelocity()
                    groupBoidsCnt += 1

        if groupBoidsCnt > 0:
            steeringForce = glm.normalize(steeringForce)
            steeringForce *= Boid.GetMaxSpeed()
            steeringForce -= self.velocity

            if glm.length(steeringForce) > Boid.GetMaxForce():
                steeringForce = glm.normalize(steeringForce)
                steeringForce *= Boid.GetMaxForce()

        return steeringForce

    def _Cohesion(self, boids):
        perceptionRadius = Boid.GetPerceptionRadiusByBehaviorRule('Cohesion')
        steeringForce = glm.vec3()
        groupBoidsCnt = 0

        for i in range(len(boids)):
            if self != boids[i]:
                dis = glm.length(self.position - boids[i].GetPosition())

                if dis < perceptionRadius:
                    steeringForce += boids[i].GetPosition()
                    groupBoidsCnt += 1

        if groupBoidsCnt > 0:
            steeringForce /= groupBoidsCnt
            steeringForce -= self.position

            steeringForce = glm.normalize(steeringForce)
            steeringForce *= Boid.GetMaxSpeed()
            steeringForce -= self.velocity

            if glm.length(steeringForce) > Boid.GetMaxForce():
                steeringForce = glm.normalize(steeringForce)
                steeringForce *= Boid.GetMaxForce()

        return steeringForce

class FlockingSimulation:
    def __init__(self, programName, programNamePos):
        self.programName = programName
        self.programNamePos = programNamePos

        self.objectsVerticesList = []
        self.objectsIndicesList = []

        self.initBoidCircleVertices = []
        self.initBoidCircleIndices = []

        self.GUIObjectsVerticesList = []
        self.GUIObjectsIndicesList = []        

        self.selectedBehaviorRuleKey = "Separation"

        self.imguiInspector = {}

        self.boids = []
        self.maxNumBoids = 500
        self.initNumBoids = 200

        self.selectedBoidsIndex = []
        self.maxNumSelectedBoids = 10
        self.allowableAngleErrorInDegrees = 1

        self.forceDirScale = 30.0

        self.imguiTabItemFlags = imgui.TAB_ITEM_SET_SELECTED
        
        self.numVertexComponents = 7
        self.numVertexComponentsWithoutColor = 3

        self.numObjects = 0

        self.objectsVAO = None
        self.objectsVBO = None
        self.objectsEBO = None

        self.numGUIObjects = 0

        self.GUIObjectsVAO = None
        self.GUIObjectsVBO = None
        self.GUIObjectsEBO = None

        self._Initialize()

    def Restart(self):
        self._Initialize()

    def UpdateAboutKeyInput(self, key, value = True):
        pass

    def UpdateAboutMouseInput(self, button, pos):
        if button == glfw.MOUSE_BUTTON_LEFT:            
            displaySize = gSceneManager.GetDisplaySize()
            screenPos = gSceneManager.GetScreenPos()

            mousePos = gInputManager.GetLastMousePos()
            modifiedMousePos = glm.vec3()

            if mousePos[0] < screenPos[0][0] or screenPos[1][0] < mousePos[0]:
                return

            if mousePos[1] < screenPos[0][1] or screenPos[1][1] < mousePos[1]:
                return

            modifiedMousePos.x = mousePos[0] - screenPos[0][0]
            modifiedMousePos.y = displaySize[1] - mousePos[1] - screenPos[0][1]

            if self.imguiInspector['ControlAddBoid']:
                if self.maxNumBoids > len(self.boids):
                    self.boids.append(Boid(modifiedMousePos))
            else:
                gInputManager.SetMouseButtonClick(glfw.MOUSE_BUTTON_LEFT, False)

                self._SelectBoid(modifiedMousePos)

    def Update(self, deltaTime):
        if gSceneManager.GetView3D() == True:
            return

        for i in range(len(self.boids)):
            self.boids[i].Flock(self.boids)

        for i in range(len(self.boids)):
            self.boids[i].Update(deltaTime)

        self._UpdateNewFrameImgui(deltaTime)

    def Draw(self):
        if gSceneManager.GetView3D() == True:
            return

        self._DrawObjects()

        displaySize = gSceneManager.GetDisplaySize()

        glViewport(0, 0, displaySize[0], displaySize[1])

        shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)

        shader.Use()

        shader.SetMat4('prjMat', gSceneManager.GetGUIPrjMat())
        shader.SetMat4('viewMat', gSceneManager.GetView2DMat())

        self._DrawGUIObjects()

    def _InitializePerceptionCircle(self):
        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE

        deltaAngle = 360.0 / Boid.GetNumVerticesByShape(shapeType)

        initBoidCircleVerticesData = []
        initBoidCircleIndicesData = []

        for i in range(Boid.GetNumVerticesByShape(shapeType)):
            initBoidCircleVerticesData.append(math.cos(glm.radians(i * deltaAngle)))
            initBoidCircleVerticesData.append(math.sin(glm.radians(i * deltaAngle)))
            initBoidCircleVerticesData.append(0.0)

            initBoidCircleIndicesData.append(i)
            initBoidCircleIndicesData.append((i + 1) % Boid.GetNumVerticesByShape(shapeType))

        self.initBoidCircleVertices = np.array(initBoidCircleVerticesData, dtype = np.float32)
        self.initBoidCircleIndices = np.array(initBoidCircleIndicesData, dtype = np.uint32)

    def _InitializeObjects(self):
        self.objectsVerticesList.clear()
        self.objectsIndicesList.clear()

        if self.numObjects > 0 :
            glDeleteVertexArrays(self.numObjects, self.objectsVAO)
            glDeleteBuffers(self.numObjects, self.objectsVBO)
            glDeleteBuffers(self.numObjects, self.objectsEBO)

        self.numObjects = 0

        self.boids.clear()
        self.selectedBoidsIndex.clear()

        for i in range(self.initNumBoids):
            self.boids.append(Boid())

        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE

        boidsVerticesSize = self.maxNumBoids * Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponents
        boidsIndicesSize = self.maxNumBoids * Boid.GetNumIndicesByShape(shapeType)

        boidsVertices = np.zeros(boidsVerticesSize, dtype = np.float32)
        boidsIndices = np.zeros(boidsIndicesSize, dtype = np.uint32)
        
        self.numObjects += 1

        self.objectsVerticesList.append(boidsVertices)
        self.objectsIndicesList.append(boidsIndices)

        self._InitializePerceptionCircle()

        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE

        boidCirclesVerticesSize = self.maxNumSelectedBoids * Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponentsWithoutColor
        boidCirclesIndicesSize = self.maxNumSelectedBoids * Boid.GetNumVerticesByShape(shapeType)

        boidCirclesVertices = np.zeros(boidCirclesVerticesSize, dtype = np.float32)
        boidCirclesIndices = np.zeros(boidCirclesIndicesSize, dtype = np.uint32)

        self.numObjects += 1

        self.objectsVerticesList.append(boidCirclesVertices)
        self.objectsIndicesList.append(boidCirclesIndices)

        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_FORCE_DIRECTION

        forceDirsVerticesSize = self.maxNumSelectedBoids * Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponentsWithoutColor
        forceDirsIndicesSize = self.maxNumSelectedBoids * Boid.GetNumIndicesByShape(shapeType)

        forceDirsVertices = np.zeros(forceDirsVerticesSize, dtype = np.float32)
        forceDirsIndices = np.zeros(forceDirsIndicesSize, dtype = np.uint32)

        self.numObjects += 1

        self.objectsVerticesList.append(forceDirsVertices)
        self.objectsIndicesList.append(forceDirsIndices)

        self.objectsVAO = glGenVertexArrays(self.numObjects)
        self.objectsVBO = glGenBuffers(self.numObjects)
        self.objectsEBO = glGenBuffers(self.numObjects)

        numVertexComponents = 0

        for i in range(self.numObjects):
            if i == FlockingSimulationIndex.OBJECT_BOID:
                numVertexComponents = self.numVertexComponents
            elif i == FlockingSimulationIndex.OBJECT_BOID_PERCEPTION_CIRCLE:
                numVertexComponents = self.numVertexComponentsWithoutColor
            elif i == FlockingSimulationIndex.OBJECT_BOID_FORCE_DIRECTION:
                numVertexComponents = self.numVertexComponentsWithoutColor

            glBindVertexArray(self.objectsVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.objectsVBO[i])
            glBufferData(GL_ARRAY_BUFFER, self.objectsVerticesList[i].nbytes, self.objectsVerticesList[i], GL_DYNAMIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.objectsIndicesList[i].nbytes, self.objectsIndicesList[i], GL_DYNAMIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.objectsVerticesList[i].itemsize * numVertexComponents, ctypes.c_void_p(0))

            if i == FlockingSimulationIndex.OBJECT_BOID:
                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.objectsVerticesList[i].itemsize * numVertexComponents, ctypes.c_void_p(self.objectsVerticesList[i].itemsize * 3))

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def _InitializeGUIObjects(self):
        gSceneManager.ClearSpecificProgramArgs()

        self.GUIObjectsVerticesList.clear()
        self.GUIObjectsIndicesList.clear()

        if self.numGUIObjects > 0:
            glDeleteVertexArrays(self.numGUIObjects, self.GUIObjectsVAO)
            glDeleteBuffers(self.numGUIObjects, self.GUIObjectsVBO)
            glDeleteBuffers(self.numGUIObjects, self.GUIObjectsEBO)

        self.numGUIObjects = 0

        self.imguiInspector = {
            'ControlAddBoid' : False,
            'ControlShowPerceptionRadius' : False,
            'ControlShowForceDirection' : False,
            'ControlBehaviorRule' : {'Separation' : True, 'Alignment' : False, 'Cohesion' : False}
            }

        self.selectedBehaviorRuleKey = "Separation"        

        Boid.SetPerceptionRadiusByBehaviorRule('Separation', 25)
        Boid.SetPerceptionRadiusByBehaviorRule('Alignment', 50)
        Boid.SetPerceptionRadiusByBehaviorRule('Cohesion', 50)

        Boid.SetForceScaleByBehaviorRule('Separation', 1.0)
        Boid.SetForceScaleByBehaviorRule('Alignment', 1.0)
        Boid.SetForceScaleByBehaviorRule('Cohesion', 1.0)

        Boid.SetMaxSpeed(100.0)
        Boid.SetMaxForce(50.0)

        self.imguiTabItemFlags = imgui.TAB_ITEM_SET_SELECTED

        displaySize = gSceneManager.GetDisplaySize()
        screenPos = gSceneManager.GetScreenPos()

        backgroundVerticesData = [
            0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[0][0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[0][0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,

            screenPos[1][0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            screenPos[1][0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,

            0.0, 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], 0.0, 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], screenPos[0][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, screenPos[0][1], 5.0, 1.0, 0.0, 0.0, 0.5,

            0.0, screenPos[1][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], screenPos[1][1], 5.0, 1.0, 0.0, 0.0, 0.5,
            displaySize[0], displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5,
            0.0, displaySize[1], 5.0, 1.0, 0.0, 0.0, 0.5
            ]

        backgroundIndicesData = [
            0, 1, 2, 2, 3, 0,
            4, 5, 6, 6, 7, 4,
            8, 9, 10, 10, 11, 8,
            12, 13, 14, 14, 15, 12
            ]

        self.GUIObjectsVerticesList.append(np.array(backgroundVerticesData, dtype = np.float32))
        self.GUIObjectsIndicesList.append(np.array(backgroundIndicesData, dtype = np.uint32))

        self.numGUIObjects += 1

        backgroundLineVerticesData = [
            0.0, screenPos[0][1], 8.0, 1.0, 1.0, 1.0, 1.0,
            displaySize[0], screenPos[0][1], 8.0, 1.0, 1.0, 1.0, 1.0,

            0.0, screenPos[1][1], 8.0, 1.0, 1.0, 1.0, 1.0,
            displaySize[0], screenPos[1][1], 8.0, 1.0, 1.0, 1.0, 1.0,

            screenPos[0][0], 0.0, 8.0, 1.0, 1.0, 1.0, 1.0,
            screenPos[0][0], displaySize[1], 8.0, 1.0, 1.0, 1.0, 1.0,

            screenPos[1][0], 0.0, 8.0, 1.0, 1.0, 1.0, 1.0,
            screenPos[1][0], displaySize[1], 8.0, 1.0, 1.0, 1.0, 1.0
            ]

        backgroundLineIndicesData = [
            0, 1,
            2, 3, 
            4, 5, 
            6, 7
            ]

        self.GUIObjectsVerticesList.append(np.array(backgroundLineVerticesData, dtype = np.float32))
        self.GUIObjectsIndicesList.append(np.array(backgroundLineIndicesData, dtype = np.uint32))

        self.numGUIObjects += 1

        self.GUIObjectsVAO = glGenVertexArrays(self.numGUIObjects)
        self.GUIObjectsVBO = glGenBuffers(self.numGUIObjects)
        self.GUIObjectsEBO = glGenBuffers(self.numGUIObjects)

        for i in range(self.numGUIObjects):
            glBindVertexArray(self.GUIObjectsVAO[i])

            glBindBuffer(GL_ARRAY_BUFFER, self.GUIObjectsVBO[i])
            glBufferData(GL_ARRAY_BUFFER, self.GUIObjectsVerticesList[i].nbytes, self.GUIObjectsVerticesList[i], GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.GUIObjectsEBO[i])
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.GUIObjectsIndicesList[i].nbytes, self.GUIObjectsIndicesList[i], GL_STATIC_DRAW)

            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.GUIObjectsVerticesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(0))

            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, self.GUIObjectsIndicesList[i].itemsize * self.numVertexComponents, ctypes.c_void_p(self.GUIObjectsVerticesList[i].itemsize * 3))

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        gSceneManager.AddSpecificProgramArgs(gSceneManager.GetColor('DefaultColor_', 7), self.programNamePos, 0, 1, 'Medium', '# ' + self.programName)

    def _Initialize(self):
        gSceneManager.SetView3D(False)

        self._InitializeObjects()

        self._InitializeGUIObjects()

    def _SelectBoid(self, modifiedMousePos):
        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE

        for i in range(len(self.boids)):
            boidVertices = self.boids[i].GetVertices()
            boidVec = []
            totalAngleForInnerCheck = 0.0

            for j in range(Boid.GetNumVerticesByShape(shapeType)):
                diffX = boidVertices[j * self.numVertexComponents + 0] - modifiedMousePos.x
                diffY = boidVertices[j * self.numVertexComponents + 1] - modifiedMousePos.y
                boidVec.append(glm.vec3(diffX, diffY, 0.0))

            for j in range(Boid.GetNumVerticesByShape(shapeType)):
                fVec = glm.normalize(boidVec[j])
                sVec = glm.normalize(boidVec[(j + 1) % Boid.GetNumVerticesByShape(shapeType)])

                totalAngleForInnerCheck += glm.degrees(glm.acos(glm.dot(fVec, sVec)))

            if totalAngleForInnerCheck >= 360.0 - self.allowableAngleErrorInDegrees:
                for j in range(len(self.selectedBoidsIndex) - 1, -1, -1):
                    if self.selectedBoidsIndex[j] == i:
                        self.boids[i].SetColor([1.0, 1.0, 1.0, 0.8])
                        self.selectedBoidsIndex.pop(j)
                        return

                if self.maxNumSelectedBoids > len(self.selectedBoidsIndex):
                    self.boids[i].SetColor([1.0, 0.0, 0.0, 0.8])
                    self.selectedBoidsIndex.append(i)
                    return

    def _UpdateNewFrameImguiHierarchy(self, deltaTime):
        imguiSize = gSceneManager.GetImguiSize(Index.IMGUI_WINDOW_HIERARCHY)
        imguiPos = gSceneManager.GetImguiPos(Index.IMGUI_WINDOW_HIERARCHY)

        imguiFont = gSceneManager.GetImguiFont()

        imgui.set_window_position_labeled('Hierarchy', imguiPos[0], imguiPos[1], imgui.ONCE)
        imgui.set_window_size_named('Hierarchy', imguiSize[0], imguiSize[1], imgui.ONCE)

        imgui.push_font(imguiFont)

        with imgui.begin('Hierarchy', False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE):
            with imgui.begin_tab_bar('HierarchyTabBar'):
                if imgui.begin_tab_item('Hierarchy').selected:
                    imgui.text('Hierarchy Features')
                    imgui.end_tab_item()

        imgui.pop_font()

    def _UpdateNewFrameImguiInspector(self, deltaTime):
        imguiSize = gSceneManager.GetImguiSize(Index.IMGUI_WINDOW_INSPECTOR)
        imguiPos = gSceneManager.GetImguiPos(Index.IMGUI_WINDOW_INSPECTOR)

        imguiFont = gSceneManager.GetImguiFont()

        imgui.set_window_position_labeled('Inspector', imguiPos[0], imguiPos[1], imgui.ONCE)
        imgui.set_window_size_named('Inspector', imguiSize[0], imguiSize[1], imgui.ONCE)

        imgui.push_font(imguiFont)

        with imgui.begin('Inspector', False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE):
            with imgui.begin_tab_bar('InspectorTabBar'):
                if imgui.begin_tab_item('Control').selected:
                    imgui.text('# Boids : {0} / {1}'.format(len(self.boids), self.maxNumBoids))
                    imgui.text('# Selected Boids : {0} / {1}'.format(len(self.selectedBoidsIndex), self.maxNumSelectedBoids))
                    _, value = imgui.checkbox('AddBoid', self.imguiInspector['ControlAddBoid'])
                    self.imguiInspector['ControlAddBoid'] = value
                    imgui.separator()
                    _, value = imgui.checkbox('ShowPerceptionRadius', self.imguiInspector['ControlShowPerceptionRadius'])
                    self.imguiInspector['ControlShowPerceptionRadius'] = value
                    _, value = imgui.checkbox('ShowForceDirection', self.imguiInspector['ControlShowForceDirection'])
                    self.imguiInspector['ControlShowForceDirection'] = value
                    if imgui.tree_node('BehaviorRule', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                        for key, value in self.imguiInspector['ControlBehaviorRule'].items():
                            if imgui.radio_button(key, value):
                                if value == False:
                                    self.imguiInspector['ControlBehaviorRule'][key] = not value
                                    self.selectedBehaviorRuleKey = key
                        for key, value in self.imguiInspector['ControlBehaviorRule'].items():
                            if key != self.selectedBehaviorRuleKey:
                                self.imguiInspector['ControlBehaviorRule'][key] = False
                        if imgui.tree_node('BehaviorRuleFactor (' + self.selectedBehaviorRuleKey + ')', flags = imgui.TREE_NODE_DEFAULT_OPEN):
                            value = Boid.GetPerceptionRadiusByBehaviorRule(self.selectedBehaviorRuleKey)
                            _, value = imgui.slider_float('PR', value, min_value = 0, max_value = 500, format = '%0.0f')
                            Boid.SetPerceptionRadiusByBehaviorRule(self.selectedBehaviorRuleKey, value)

                            value = Boid.GetForceScaleByBehaviorRule(self.selectedBehaviorRuleKey)
                            _, value = imgui.slider_float('FS', value, min_value = 0.0, max_value = 10.0, format = '%0.1f')
                            Boid.SetForceScaleByBehaviorRule(self.selectedBehaviorRuleKey, value)
                            imgui.tree_pop()
                        imgui.tree_pop()
                    imgui.separator()
                    value = Boid.GetMaxSpeed()
                    _, value = imgui.slider_float('MaxSpeed', value, min_value = 0.1, max_value = 1000.0, format = '%0.1f')
                    Boid.SetMaxSpeed(value)
                    value = Boid.GetMaxForce()
                    _, value = imgui.slider_float('MaxForce', value, min_value = 0.1, max_value = 1000.0, format = '%0.1f')
                    Boid.SetMaxForce(value)
                    imgui.separator()
                    imgui.text('Control Features')
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Test').selected:
                    imgui.text('Test Features')
                    imgui.end_tab_item()

        imgui.pop_font()

    def _UpdateNewFrameImgui(self, deltaTime):
        imgui.new_frame()

        self._UpdateNewFrameImguiHierarchy(deltaTime)

        self._UpdateNewFrameImguiInspector(deltaTime)

    def _DrawBoids(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_POLYGON_BIT | GL_LINE_BIT)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        objectType = FlockingSimulationIndex.OBJECT_BOID
        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_TRIANGLE

        boidVerticesSize = Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponents
        boidIndicesSize = Boid.GetNumIndicesByShape(shapeType)

        self.objectsVerticesList[objectType][ : ] = 0.0
        self.objectsIndicesList[objectType][ : ] = 0

        for i in range(len(self.boids)):
            vOffset = i * boidVerticesSize
            iOffset = i * boidIndicesSize
            viOffset = i * Boid.GetNumVerticesByShape(shapeType)

            self.objectsVerticesList[objectType][vOffset : vOffset + boidVerticesSize] = self.boids[i].GetVertices()
            self.objectsIndicesList[objectType][iOffset : iOffset + boidIndicesSize] = self.boids[i].GetIndices() + viOffset

        glBindBuffer(GL_ARRAY_BUFFER, self.objectsVBO[objectType])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.objectsVerticesList[objectType].nbytes, self.objectsVerticesList[objectType])

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[objectType])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.objectsIndicesList[objectType].nbytes, self.objectsIndicesList[objectType])

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)

        shader.Use()

        tempModelMat = glm.mat4()
        shader.SetMat4('modelMat', tempModelMat)

        glLineWidth(1.0)

        glBindVertexArray(self.objectsVAO[objectType])
        glDrawElements(GL_TRIANGLES, len(self.objectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        glPopAttrib()

    def _DrawPerceptionCircles(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        objectType = FlockingSimulationIndex.OBJECT_BOID_PERCEPTION_CIRCLE
        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_CIRCLE

        boidCircleVerticesSize = Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponentsWithoutColor
        boidCircleIndicesSize = Boid.GetNumIndicesByShape(shapeType)

        self.objectsVerticesList[objectType][ : ] = 0.0
        self.objectsIndicesList[objectType][ : ] = 0

        for i in range(len(self.selectedBoidsIndex)):
            boid = self.boids[self.selectedBoidsIndex[i]]

            vOffset = i * boidCircleVerticesSize
            iOffset = i * boidCircleIndicesSize
            viOffset = i * Boid.GetNumVerticesByShape(shapeType)

            self.objectsVerticesList[objectType][vOffset : vOffset + boidCircleVerticesSize] = self.initBoidCircleVertices
            self.objectsIndicesList[objectType][iOffset : iOffset + boidCircleIndicesSize] = self.initBoidCircleIndices + viOffset

            pos = boid.GetPosition()

            transMat = glm.translate(glm.vec3(pos.x, pos.y, 0.0))

            rotMat = glm.mat4()

            scale = Boid.GetPerceptionRadiusByBehaviorRule(self.selectedBehaviorRuleKey)

            scaleMat = glm.scale(glm.vec3(scale, scale, 1.0))

            perceptionModelMat = transMat * rotMat * scaleMat

            for j in range(Boid.GetNumVerticesByShape(shapeType)):
                vertex = glm.vec3()

                vertex.x = self.initBoidCircleVertices[j * self.numVertexComponentsWithoutColor + 0]
                vertex.y = self.initBoidCircleVertices[j * self.numVertexComponentsWithoutColor + 1]
                vertex.z = self.initBoidCircleVertices[j * self.numVertexComponentsWithoutColor + 2]

                vertex = perceptionModelMat * vertex

                self.objectsVerticesList[objectType][i * boidCircleVerticesSize + j * self.numVertexComponentsWithoutColor + 0] = vertex.x
                self.objectsVerticesList[objectType][i * boidCircleVerticesSize + j * self.numVertexComponentsWithoutColor + 1] = vertex.y
                self.objectsVerticesList[objectType][i * boidCircleVerticesSize + j * self.numVertexComponentsWithoutColor + 2] = vertex.z

        glBindBuffer(GL_ARRAY_BUFFER, self.objectsVBO[objectType])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.objectsVerticesList[objectType].nbytes, self.objectsVerticesList[objectType])

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[objectType])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.objectsIndicesList[objectType].nbytes, self.objectsIndicesList[objectType])

        shader = gSceneManager.GetShader(Index.SHADER_SIMPLE_USE_UNIFORMCOLOR)

        shader.Use()

        tempModelMat = glm.mat4()
        shader.SetMat4('modelMat', tempModelMat)

        shader.SetBool('useUniformColor', True)

        if self.selectedBehaviorRuleKey == "Separation":
            shader.SetVec4('uniformColor', 1.0, 0.0, 1.0, 0.5)
        elif self.selectedBehaviorRuleKey == "Alignment":
            shader.SetVec4('uniformColor', 0.0, 1.0, 0.0, 0.5)
        elif self.selectedBehaviorRuleKey == "Cohesion":
            shader.SetVec4('uniformColor', 1.0, 1.0, 0.0, 0.5)

        glLineWidth(2.0)

        glBindVertexArray(self.objectsVAO[objectType])
        glDrawElements(GL_LINES, len(self.objectsIndicesList[objectType]), GL_UNSIGNED_INT, None)
        
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        glPopAttrib()

    def _DrawForceDirections(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        shader = gSceneManager.GetShader(Index.SHADER_SIMPLE_USE_UNIFORMCOLOR)

        shader.Use()

        tempModelMat = glm.mat4()
        shader.SetMat4('modelMat', tempModelMat)

        shader.SetBool('useUniformColor', True)

        glLineWidth(2.0)

        objectType = FlockingSimulationIndex.OBJECT_BOID_FORCE_DIRECTION
        shapeType = FlockingSimulationIndex.OBJECT_SHAPE_FORCE_DIRECTION

        glBindVertexArray(self.objectsVAO[objectType])

        forceDirVerticesSize = Boid.GetNumVerticesByShape(shapeType) * self.numVertexComponentsWithoutColor
        forceDirIndicesSize = Boid.GetNumIndicesByShape(shapeType)

        initForceDirIndices = np.array([0, 1], dtype = np.uint32)

        self.objectsVerticesList[objectType][ : ] = 0.0
        self.objectsIndicesList[objectType][ : ] = 0

        for i in range(len(self.selectedBoidsIndex)):
            boid = self.boids[self.selectedBoidsIndex[i]]

            forces = []
            forces.append(boid.GetForceByBehaviorRule('Separation'))
            forces.append(boid.GetForceByBehaviorRule('Alignment'))
            forces.append(boid.GetForceByBehaviorRule('Cohesion'))

            pos = boid.GetPosition()

            self.objectsVerticesList[objectType][i * forceDirVerticesSize + 0 * self.numVertexComponentsWithoutColor + 0] = pos.x
            self.objectsVerticesList[objectType][i * forceDirVerticesSize + 0 * self.numVertexComponentsWithoutColor + 1] = pos.y
            self.objectsVerticesList[objectType][i * forceDirVerticesSize + 0 * self.numVertexComponentsWithoutColor + 2] = pos.z

            for j in range(len(forces)):
                forces[j] = glm.normalize(forces[j])

                self.objectsVerticesList[objectType][i * forceDirVerticesSize + (j + 1) * self.numVertexComponentsWithoutColor + 0] = pos.x + (forces[j].x * self.forceDirScale)
                self.objectsVerticesList[objectType][i * forceDirVerticesSize + (j + 1) * self.numVertexComponentsWithoutColor + 1] = pos.y + (forces[j].y * self.forceDirScale)
                self.objectsVerticesList[objectType][i * forceDirVerticesSize + (j + 1) * self.numVertexComponentsWithoutColor + 2] = pos.z + (forces[j].z * self.forceDirScale)

            iOffset = i * forceDirIndicesSize
            viOffset = i * Boid.GetNumVerticesByShape(shapeType)

            self.objectsIndicesList[objectType][iOffset : iOffset + forceDirIndicesSize] = initForceDirIndices + viOffset

        glBindBuffer(GL_ARRAY_BUFFER, self.objectsVBO[objectType])
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.objectsVerticesList[objectType].nbytes, self.objectsVerticesList[objectType])

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[objectType])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.objectsIndicesList[objectType].nbytes, self.objectsIndicesList[objectType])

        shader.SetVec4('uniformColor', 1.0, 0.0, 1.0, 0.5)
        glDrawElements(GL_LINES, len(self.objectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        initForceDirIndices = np.array([0, 2], dtype = np.uint32)

        self.objectsIndicesList[objectType][ : ] = 0

        for i in range(len(self.selectedBoidsIndex)):
            iOffset = i * forceDirIndicesSize
            viOffset = i * Boid.GetNumVerticesByShape(shapeType)

            self.objectsIndicesList[objectType][iOffset : iOffset + forceDirIndicesSize] = initForceDirIndices + viOffset

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[objectType])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.objectsIndicesList[objectType].nbytes, self.objectsIndicesList[objectType])

        shader.SetVec4('uniformColor', 0.0, 1.0, 0.0, 0.5)
        glDrawElements(GL_LINES, len(self.objectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        initForceDirIndices = np.array([0, 3], dtype = np.uint32)

        self.objectsIndicesList[objectType][ : ] = 0

        for i in range(len(self.selectedBoidsIndex)):
            iOffset = i * forceDirIndicesSize
            viOffset = i * Boid.GetNumVerticesByShape(shapeType)

            self.objectsIndicesList[objectType][iOffset : iOffset + forceDirIndicesSize] = initForceDirIndices + viOffset

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.objectsEBO[objectType])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.objectsIndicesList[objectType].nbytes, self.objectsIndicesList[objectType])

        shader.SetVec4('uniformColor', 1.0, 1.0, 0.0, 0.5)
        glDrawElements(GL_LINES, len(self.objectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        glPopAttrib()

    def _DrawObjects(self):
        self._DrawBoids()

        if len(self.selectedBoidsIndex) > 0:
            if self.imguiInspector['ControlShowPerceptionRadius'] == True:
                self._DrawPerceptionCircles()

            if self.imguiInspector['ControlShowForceDirection'] == True:
                self._DrawForceDirections()

    def _DrawGUIObjects(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

        glDisable(GL_DEPTH_TEST)

        glEnable(GL_BLEND)

        glBlendFunc(GL_SRC_ALPHA, GL_ZERO)

        shader = gSceneManager.GetShader(Index.SHADER_DEFAULT)

        shader.Use()

        tempModelMat = glm.mat4()
        shader.SetMat4('modelMat', tempModelMat)

        objectType = FlockingSimulationIndex.GUI_OBJECT_BACKGROUND        

        glBindVertexArray(self.GUIObjectsVAO[objectType])
        glDrawElements(GL_TRIANGLES, len(self.GUIObjectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        objectType = FlockingSimulationIndex.GUI_OBJECT_BACKGROUND_LINE
        
        glLineWidth(2.0)

        glBindVertexArray(self.GUIObjectsVAO[objectType])
        glDrawElements(GL_LINES, len(self.GUIObjectsIndicesList[objectType]), GL_UNSIGNED_INT, None)

        glBindVertexArray(0)

        glPopAttrib()


def HandleWindowSizeCallback(glfwWindow, width, height):
    glViewport(0, 0, width, height)    

def HandleKeyCallback(glfwWindow, key, scanCode, action, modes):
    if action == glfw.PRESS:
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(glfwWindow, glfw.TRUE)
        elif key == glfw.KEY_SPACE:
            gInputManager.SetKeyState(glfw.KEY_SPACE, True)

        if key == glfw.KEY_1:
            gInputManager.SetKeyState(glfw.KEY_1, True)
        elif key == glfw.KEY_2:
            gInputManager.SetKeyState(glfw.KEY_2, True)
        elif key == glfw.KEY_3:
            gInputManager.SetKeyState(glfw.KEY_3, True)
        elif key == glfw.KEY_4:
            gInputManager.SetKeyState(glfw.KEY_4, True)
        elif key == glfw.KEY_5:
            gInputManager.SetKeyState(glfw.KEY_5, True)
        elif key == glfw.KEY_6:
            gInputManager.SetKeyState(glfw.KEY_6, True)
        elif key == glfw.KEY_8:
            gInputManager.SetKeyState(glfw.KEY_8, True)
        elif key == glfw.KEY_9:
            gInputManager.SetKeyState(glfw.KEY_9, True)
        elif key == glfw.KEY_0:
            gInputManager.SetKeyState(glfw.KEY_0, True)

        if key == glfw.KEY_B:
            gInputManager.SetKeyState(glfw.KEY_B, True)        
        elif key == glfw.KEY_F:
            gInputManager.SetKeyState(glfw.KEY_F, True)        
        elif key == glfw.KEY_I:
            gInputManager.SetKeyState(glfw.KEY_I, True) 
        elif key == glfw.KEY_L:
            gInputManager.SetKeyState(glfw.KEY_L, True)
        elif key == glfw.KEY_P:
            gInputManager.SetKeyState(glfw.KEY_P, True)            
        elif key == glfw.KEY_R:
            gInputManager.SetKeyState(glfw.KEY_R, True)        
        elif key == glfw.KEY_V:
            gInputManager.SetKeyState(glfw.KEY_V, True)
        elif key == glfw.KEY_X:
            gInputManager.SetKeyState(glfw.KEY_X, True)

        if key == glfw.KEY_W:
            gInputManager.SetKeyState(glfw.KEY_W, True)
        elif key == glfw.KEY_S:
            gInputManager.SetKeyState(glfw.KEY_S, True)
        elif key == glfw.KEY_A:
            gInputManager.SetKeyState(glfw.KEY_A, True)
        elif key == glfw.KEY_D:
            gInputManager.SetKeyState(glfw.KEY_D, True)
        elif key == glfw.KEY_Q:
            gInputManager.SetKeyState(glfw.KEY_Q, True)
        elif key == glfw.KEY_E:
            gInputManager.SetKeyState(glfw.KEY_E, True)

        if key == glfw.KEY_LEFT:
            gInputManager.SetKeyState(glfw.KEY_LEFT, True)
        elif key == glfw.KEY_RIGHT:
            gInputManager.SetKeyState(glfw.KEY_RIGHT, True)
        elif key == glfw.KEY_UP:
            gInputManager.SetKeyState(glfw.KEY_UP, True)
        elif key == glfw.KEY_DOWN:
            gInputManager.SetKeyState(glfw.KEY_DOWN, True)

    if action == glfw.RELEASE:
        if key == glfw.KEY_W:
            gInputManager.SetKeyState(glfw.KEY_W, False)
        elif key == glfw.KEY_S:
            gInputManager.SetKeyState(glfw.KEY_S, False)
        elif key == glfw.KEY_A:
            gInputManager.SetKeyState(glfw.KEY_A, False)
        elif key == glfw.KEY_D:
            gInputManager.SetKeyState(glfw.KEY_D, False)
        elif key == glfw.KEY_Q:
            gInputManager.SetKeyState(glfw.KEY_Q, False)
        elif key == glfw.KEY_E:
            gInputManager.SetKeyState(glfw.KEY_E, False)

        if key == glfw.KEY_LEFT:
            gInputManager.SetKeyState(glfw.KEY_LEFT, False)
        elif key == glfw.KEY_RIGHT:
            gInputManager.SetKeyState(glfw.KEY_RIGHT, False)
        elif key == glfw.KEY_UP:
            gInputManager.SetKeyState(glfw.KEY_UP, False)
        elif key == glfw.KEY_DOWN:
            gInputManager.SetKeyState(glfw.KEY_DOWN, False)

def HandleMouseButtonCallback(glfwWindow, button, action, mod):
    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:            
            gInputManager.SetMouseButtonClick(glfw.MOUSE_BUTTON_LEFT, True)
            gInputManager.SetLastMousePosOnClick(glfw.get_cursor_pos(glfwWindow))            
        elif action == glfw.RELEASE:
            gInputManager.SetMouseButtonClick(glfw.MOUSE_BUTTON_LEFT, False)

    if button == glfw.MOUSE_BUTTON_RIGHT:
        if action == glfw.PRESS:
            gInputManager.SetMouseButtonClick(glfw.MOUSE_BUTTON_RIGHT, True)            

            screenPos = gSceneManager.GetScreenPos()
            mousePos = glfw.get_cursor_pos(glfwWindow)

            gInputManager.SetLastMousePosOnClick(mousePos)

            if gSceneManager.GetView3D() == False:
                return

            if mousePos[0] < screenPos[0][0] or screenPos[1][0] < mousePos[0]:
                gSceneManager.SetEnableCameraMove(False)
            elif mousePos[1] < screenPos[0][1] or screenPos[1][1] < mousePos[1]:
                gSceneManager.SetEnableCameraMove(False)
            else:
                gSceneManager.SetEnableCameraMove(True)
                gInputManager.SetLastMousePos(mousePos)

        elif action == glfw.RELEASE:
            gSceneManager.SetEnableCameraMove(False)
            gInputManager.SetMouseButtonClick(glfw.MOUSE_BUTTON_RIGHT, False)            

def HandleCursorPosCallback(glfwWindow, xPos, yPos):
    screenPos = gSceneManager.GetScreenPos()

    if xPos < screenPos[0][0] or screenPos[1][0] < xPos:
        gInputManager.SetMouseEntered(False)
    elif yPos < screenPos[0][1] or screenPos[1][1] < yPos:
        gInputManager.SetMouseEntered(False)
    else:
        gInputManager.SetMouseEntered(True)

    if gSceneManager.GetEnableCameraMove() == True:
        lastPos = gInputManager.GetLastMousePos()
        xOffset = lastPos[0] - xPos
        yOffset = lastPos[1] - yPos

        gInputManager.SetLastMousePos([xPos, yPos])

        camera = gSceneManager.GetCamera()

        if gSceneManager.GetView3D() == True:
            camera.ProcessMouseMovement(xOffset, yOffset)

        displaySize = gSceneManager.GetDisplaySize()   
    
        mouseCheckInterval = 20

        if xPos < 0:
            glfw.set_cursor_pos(glfwWindow, displaySize[0] - mouseCheckInterval, yPos)
            gInputManager.SetLastMousePos(glfw.get_cursor_pos(glfwWindow))
        elif xPos > displaySize[0]:
            glfw.set_cursor_pos(glfwWindow, mouseCheckInterval, yPos)
            gInputManager.SetLastMousePos(glfw.get_cursor_pos(glfwWindow))

        if yPos < 0:
            glfw.set_cursor_pos(glfwWindow, xPos, displaySize[1] - mouseCheckInterval)
            gInputManager.SetLastMousePos(glfw.get_cursor_pos(glfwWindow))
        elif yPos > displaySize[1]:
            glfw.set_cursor_pos(glfwWindow, xPos, mouseCheckInterval)
            gInputManager.SetLastMousePos(glfw.get_cursor_pos(glfwWindow))

        gSceneManager.SetDirty(True)

        if gSceneManager.GetDebug() == True:
            gSceneManager.WriteLog('MousePos : {0}'.format([xPos, yPos]))
            gSceneManager.WriteLog('LastMousePos : {0}'.format(gInputManager.GetLastMousePos()))
        
    else:
        gInputManager.SetLastMousePos([xPos, yPos])

    #print('LastMousePosOnClick : {0}'.format(gInputManager.GetLastMousePosOnClick()))
    #print('LastMousePos : {0}'.format(gInputManager.GetLastMousePos()))

def InitializeGLFW(projectName, sequence):
    displaySize = gSceneManager.GetDisplaySize()

    if not glfw.init():
        return

    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

    windowTitle = projectName + '.' + sequence

    glfwWindow = glfw.create_window(displaySize[0], displaySize[1], windowTitle, None, None)

    if not glfwWindow:
        glfw.terminate()
        return

    videoMode = glfw.get_video_mode(glfw.get_primary_monitor())

    windowWidth = videoMode.size.width
    windowHeight = videoMode.size.height
    windowPosX = int(windowWidth / 2 - displaySize[0] / 2) - 267
    windowPosY = int(windowHeight / 2 - displaySize[1] / 2) - 60

    glfw.set_window_pos(glfwWindow, windowPosX, windowPosY)

    glfw.show_window(glfwWindow)    

    glfw.make_context_current(glfwWindow)

    glfw.set_window_size_callback(glfwWindow, HandleWindowSizeCallback)

    glfw.set_key_callback(glfwWindow, HandleKeyCallback) 

    glfw.set_mouse_button_callback(glfwWindow, HandleMouseButtonCallback)
    
    glfw.set_cursor_pos_callback(glfwWindow, HandleCursorPosCallback)

    return glfwWindow

def TestExampleCircularArrangement(testProgram):    
    models = testProgram.GetModels()
    modelsDataDict = testProgram.GetModelsDataDict()
    modelKeys = []

    modelKeys.append('Armadillo')
    models.append(Model('../../Resource/Object/armadillo.obj', 1.0))
        
    modelKeys.append('Spot')
    models.append(Model('../../Resource/Object/spot.obj', 0.01))
        
    modelKeys.append('StanfordBunny')
    models.append(Model('../../Resource/Object/stanford-bunny.obj', 0.001))
        
    modelKeys.append('Teapot')
    models.append(Model('../../Resource/Object/teapot.obj', 0.05))
        
    modelKeys.append('XYZDragon')
    models.append(Model('../../Resource/Object/xyzrgb_dragon.obj', 1.0))

    numModels = len(models)

    for i in range(numModels):
        modelDataDict = {}

        modelDataDict['Index'] = i
        modelDataDict['Vertices'] = np.array(models[i].GetVertices(), dtype = np.float32)
        modelDataDict['Indices'] = np.array(models[i].GetIndices(), dtype = np.uint32)
        modelDataDict['VerticesExceptNoUse'] = np.array(models[i].GetVerticesExceptNoUse(), dtype = np.float32)
        modelDataDict['NormalVertices'] = np.array(models[i].GetNormalLineVertices(), dtype = np.float32)
        modelDataDict['NormalIndices'] = np.array(models[i].GetNormalLineIndices(), dtype = np.uint32)
        modelDataDict['Position'] = [0.0, 0.0, 0.0]
        modelDataDict['Rotation'] = [0.0, 0.0, 0.0]
        modelDataDict['Scale'] = 1.0

        modelsDataDict[modelKeys[i]] = modelDataDict

    modelsDataDict['Armadillo']['Position'] = [-2.0, 0.0, 5.5]
    modelsDataDict['Armadillo']['Rotation'] = [0.0, 190.5, 0.0]
    modelsDataDict['Armadillo']['Scale'] = 0.02

    modelsDataDict['Spot']['Position'] = [3.5, 0.0, 5.0]
    modelsDataDict['Spot']['Rotation'] = [0.0, 170.5, 0.0]
    modelsDataDict['Spot']['Scale'] = 2.0

    modelsDataDict['StanfordBunny']['Position'] = [1.3, 0.0, -9.5]
    modelsDataDict['StanfordBunny']['Rotation'] = [0.0, 30.5, 0.0]
    modelsDataDict['StanfordBunny']['Scale'] = 20.0

    modelsDataDict['Teapot']['Position'] = [6.5, 0.0, -3.0]
    modelsDataDict['Teapot']['Rotation'] = [0.0, 185.0, 16.0]
    modelsDataDict['Teapot']['Scale'] = 0.7

    modelsDataDict['XYZDragon']['Position'] = [-7.4, 0.0, -5.0]
    modelsDataDict['XYZDragon']['Rotation'] = [31.5, 330.5, 0.0]
    modelsDataDict['XYZDragon']['Scale'] = 0.03

def TestExamplePlaceAll(testProgram):
    models = testProgram.GetModels()
    modelsDataDict = testProgram.GetModelsDataDict()
    modelKeys = []

    modelKeys.append('Armadillo')
    models.append(Model('../../Resource/Object/armadillo.obj', 1.0))
        
    modelKeys.append('Cheburashka')
    models.append(Model('../../Resource/Object/cheburashka.obj', 0.01))
        
    modelKeys.append('Ogre')
    models.append(Model('../../Resource/Object/Ogre.obj', 0.5))
        
    modelKeys.append('Homer')
    models.append(Model('../../Resource/Object/homer.obj', 0.01))

    modelKeys.append('XYZDragon')
    models.append(Model('../../Resource/Object/xyzrgb_dragon.obj', 1.0))

    modelKeys.append('Horse')
    models.append(Model('../../Resource/Object/horse.obj', 0.001))

    modelKeys.append('Spot')
    models.append(Model('../../Resource/Object/spot.obj', 0.01))
        
    modelKeys.append('StanfordBunny')
    models.append(Model('../../Resource/Object/stanford-bunny.obj', 0.001))

    modelKeys.append('Igea')
    models.append(Model('../../Resource/Object/igea.obj', 0.001))

    modelKeys.append('MaxPlanck')
    models.append(Model('../../Resource/Object/max-planck.obj', 5.0))

    modelKeys.append('Nefertiti')
    models.append(Model('../../Resource/Object/nefertiti.obj', 5.0))        

    modelKeys.append('Suzanne')
    models.append(Model('../../Resource/Object/suzanne.obj', 0.1))

    numModels = len(models)

    for i in range(numModels):
        modelDataDict = {}

        modelDataDict['Index'] = i
        modelDataDict['Vertices'] = np.array(models[i].GetVertices(), dtype = np.float32)
        modelDataDict['Indices'] = np.array(models[i].GetIndices(), dtype = np.uint32)
        modelDataDict['VerticesExceptNoUse'] = np.array(models[i].GetVerticesExceptNoUse(), dtype = np.float32)
        modelDataDict['NormalVertices'] = np.array(models[i].GetNormalLineVertices(), dtype = np.float32)
        modelDataDict['NormalIndices'] = np.array(models[i].GetNormalLineIndices(), dtype = np.uint32)
        modelDataDict['Position'] = [0.0, 0.0, 0.0]
        modelDataDict['Rotation'] = [0.0, 0.0, 0.0]
        modelDataDict['Scale'] = 1.0

        modelsDataDict[modelKeys[i]] = modelDataDict

    modelsDataDict['Armadillo']['Position'] = [-3.0, 0.0, 6.0]
    modelsDataDict['Armadillo']['Rotation'] = [0.0, 190.5, 0.0]
    modelsDataDict['Armadillo']['Scale'] = 0.02

    modelsDataDict['Cheburashka']['Position'] = [-0.85, 0.0, 6.5]
    modelsDataDict['Cheburashka']['Rotation'] = [0.0, 350.0, 0.0]
    modelsDataDict['Cheburashka']['Scale'] = 2.5

    modelsDataDict['Ogre']['Position'] = [2.5, 0.0, 8.5]
    modelsDataDict['Ogre']['Rotation'] = [0.0, 335.5, 0.0]
    modelsDataDict['Ogre']['Scale'] = 0.07

    modelsDataDict['Homer']['Position'] = [4.0, 0.0, 7.8]
    modelsDataDict['Homer']['Rotation'] = [0.0, 335.0, 7.5]
    modelsDataDict['Homer']['Scale'] = 2.2

    modelsDataDict['XYZDragon']['Position'] = [-4.0, 0.0, -3.0]
    modelsDataDict['XYZDragon']['Rotation'] = [31.5, 330.5, 0.0]
    modelsDataDict['XYZDragon']['Scale'] = 0.03

    modelsDataDict['Horse']['Position'] = [1.75, 0.0, 0.5]
    modelsDataDict['Horse']['Rotation'] = [275.0, 150.0, 0.0]
    modelsDataDict['Horse']['Scale'] = 20.0

    modelsDataDict['Spot']['Position'] = [5.2, 0.0, 2.5]
    modelsDataDict['Spot']['Rotation'] = [0.0, 156.5, 0.0]
    modelsDataDict['Spot']['Scale'] = 2.0

    modelsDataDict['StanfordBunny']['Position'] = [8.0, 0.0, 4.35]
    modelsDataDict['StanfordBunny']['Rotation'] = [0.0, 30.5, 0.0]
    modelsDataDict['StanfordBunny']['Scale'] = 15.0

    modelsDataDict['Igea']['Position'] = [-1.0, 0.0, -10.0]
    modelsDataDict['Igea']['Rotation'] = [0.0, 0.0, 0.0]
    modelsDataDict['Igea']['Scale'] = 40.0

    modelsDataDict['MaxPlanck']['Position'] = [4.35, 0.0, -6.95]
    modelsDataDict['MaxPlanck']['Rotation'] = [0.0, 172.0, 0.0]
    modelsDataDict['MaxPlanck']['Scale'] = 0.01

    modelsDataDict['Nefertiti']['Position'] = [10.0, 0.0, -6.5]
    modelsDataDict['Nefertiti']['Rotation'] = [270.0, 328.5, 0.0]
    modelsDataDict['Nefertiti']['Scale'] = 0.01

    modelsDataDict['Suzanne']['Position'] = [13.0, 0.0, -2.5]
    modelsDataDict['Suzanne']['Rotation'] = [0.0, 321.0, 0.0]
    modelsDataDict['Suzanne']['Scale'] = 1.5

def Main():    
    projectName = "Flocking Simulation"
    programName = "FlockingSimulation"
    programNamePos = [1130, 17]

    glfwWindow = InitializeGLFW(projectName, 'P01')

    imgui.create_context()
    imguiRenderer = GlfwRenderer(glfwWindow, False)

    io = imgui.get_io()
    imguiNewFont = io.fonts.add_font_from_file_ttf('../../Resource/Font/comic.ttf', 14)
    imguiRenderer.refresh_font_texture()  
    
    shaders = []

    shaders.append(gShaderFactory.CreateShader(Index.SHADER_CODE_DEFAULT, Index.SHADER_CODE_DEFAULT))
    shaders.append(gShaderFactory.CreateShader(Index.SHADER_CODE_DEFAULT, Index.SHADER_FRAGMENT_CODE_SIMPLE_USE_UNIFORMCOLOR))

    #testProgram = TestProgram(programName, programNamePos)

    #testProgram.RegistTestExample('CircularArrangement', TestExampleCircularArrangement)
    #testProgram.RegistTestExample('PlaceAll', TestExamplePlaceAll)

    gSceneManager.InitializeOpenGL(shaders)
    gSceneManager.SetCamera(Camera())
    gSceneManager.MakeFont(imguiNewFont)
    gSceneManager.AddObject(FlockingSimulation(programName, programNamePos))
    
    lastElapsedTime = glfw.get_time()
    deltaTime = 0.0

    while glfw.window_should_close(glfwWindow) == False:
        glfw.poll_events()        
        imguiRenderer.process_inputs()

        gSceneManager.Update(deltaTime)        

        gSceneManager.Draw()

        imgui.render()
        imguiRenderer.render(imgui.get_draw_data())

        glfw.swap_buffers(glfwWindow)

        gSceneManager.PostUpdate(deltaTime)        

        deltaTime = glfw.get_time() - lastElapsedTime
        lastElapsedTime = glfw.get_time()

    gSceneManager.Finish()

    imguiRenderer.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    Main()   