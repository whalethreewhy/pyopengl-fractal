import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
from OpenGL.GL.shaders import *
from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np
import glm
import time
import sys

#aa = os.path.dirname(sys.executable)
#os.system(f"start cmd /K cd {aa}\\Scripts" )
#print('Enter:\npip install numpy PyGLM pygame PyOpenGL')
#input()
width,height = 1280,720
display = (width,height)

Running = True
pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
pygame.display.set_caption("Mandelbrot")
base_plotX = np.array([-225,75],dtype='float32')
base_plotY = np.array([-100,100],dtype='float32')

plotX , plotY = base_plotX, base_plotY


class Graph:
	def __init__(self,width,height):
		self.p_array = np.asarray([[x,y] for x in range(width) for y in range(height)],dtype='float32').flatten()
		self.offset = np.array([0,0],dtype='float32')
		self.num_points = int(len(self.p_array)/2)
		self.scale = 1
		self.update = True
		self.zoom = 1
		self.speed = 0.01
	
	def checkUpdate(self):
		if self.update:
			self.update = False
			return True

	def changeScale(self,change):
		if self.scale+change <= 0:
			if change <0:
				self.scale *= 0.1
			else:
				self.scale /= 0.1
		else:
			self.scale +=change
		self.update = True

def genShader():
	VERTEX_SHADER = """
		#version 330 core
		layout (location = 0) in vec2 point;
		uniform vec3 colorMap[16] = vec3[16](
			vec3(66.0f, 30.0f, 15.0f),
			vec3(25.0f, 7.0f, 26.0f),
			vec3(9.0f, 1.0f, 47.0f),
			vec3(4.0f, 4.0f, 73.0f),
			vec3(0.0f, 7.0f, 100.0f),
			vec3(12.0f, 44.0f, 138.0f),
			vec3(24.0f, 82.0f, 177.0f),
			vec3(57.0f, 125.0f, 209.0f),
			vec3(134.0f, 181.0f, 229.0f),
			vec3(211.0f, 236.0f, 248.0f),
			vec3(241.0f, 233.0f, 191.0f),
			vec3(248.0f, 201.0f, 95.0f),
			vec3(255.0f, 170.0f, 0.0f),
			vec3(204.0f, 128.0f, 0.0f),
			vec3(153.0f, 87.0f, 0.0f),
			vec3(106.0f, 52.0f, 3.0f)			
		);
		uniform mat4 projection;
		uniform vec2 plotX;
		uniform vec2 plotY;
	
		uniform vec2 scale;
		uniform float iter;
		out vec3 color;
		
		struct Complex {
			float r;
			float i;
		};

		float absComplex(Complex z){
			return (z.r * z.r + z.i * z.i);
		}

		Complex addComplex(Complex x, Complex y) {
			return Complex(x.r + y.r, x.i + y.i);
		}

		Complex multComplex(Complex x, Complex y) {
			return Complex(x.r*y.r - x.i*y.i, x.r*y.i + x.i*y.r);
		}

		void main() {
			float a = plotX.r+(scale.x*point.x);
			float b = plotY.r+(scale.y*point.y);
			Complex c = Complex(a/100.0f,b/100.0f);

			Complex z = Complex(0.0f,0.0f);
			float n = 0.0f;
			while ((absComplex(z) <= 4.0f) && (n < iter)) {
				z = addComplex(multComplex(z,z),c);
				n = n + 1.0f;
			}

			if (n < iter){
				color = colorMap[int(n-1) % 16]/255.0f;
			}
			else{
				color = vec3(0.0f,0.0f,0.0f);
			}
			gl_Position = projection*vec4(point.xy,0.0f,1.0f);;
		}
	"""
	FRAGMENT_SHADER = """
		#version 330 core
		in vec3 color;
		out vec4 outColor;

		void main() {

			if (color.rgb == 0.0f){
				discard;
			}

			outColor = vec4(color,1.0f);
		}
	"""  
	shader = OpenGL.GL.shaders.compileProgram(
											OpenGL.GL.shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
											OpenGL.GL.shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER),
											validate=False
											)

	return shader

def genbuffer(VAO,verts):
	verts = verts.flatten()
	glBindVertexArray(VAO)
	glBindBuffer(GL_ARRAY_BUFFER,1)
	glBufferData(GL_ARRAY_BUFFER,len(verts)*4,verts,GL_STATIC_DRAW)
	glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
	glBindBuffer(GL_ARRAY_BUFFER,0)
	glBindVertexArray(0)

def draw(VAO,vert_count):
	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
	
	glBindVertexArray(VAO)
	glEnableVertexAttribArray(0)
	glDrawArrays(GL_POINTS, 0,vert_count)
	glBindVertexArray(0)
	glDisableVertexAttribArray(0)
	#glUseProgram(0)

"""SETUP"""
SHADER = genShader()
glUseProgram(SHADER)
orth_loc = glGetUniformLocation(SHADER, "projection")
glUniformMatrix4fv(orth_loc, 1, GL_FALSE, np.array(glm.ortho(0.0, width, height, 0.0, -1000.0, 1000.0)))


scale_loc = glGetUniformLocation(SHADER, "scale")
glUniform2f(scale_loc, (plotX[1]-plotX[0])/width,(plotY[1]-plotY[0])/height)


plotX_loc = glGetUniformLocation(SHADER, "plotX")
plotY_loc = glGetUniformLocation(SHADER, "plotY")
glUniform2f(plotX_loc, plotX[0],plotX[1])
glUniform2f(plotY_loc, plotY[0],plotY[1])

iter_loc = glGetUniformLocation(SHADER, "iter")
glUniform1f(iter_loc,50)


VAO = glGenVertexArrays(1)
GRAPH = Graph(width,height)
clock = pygame.time.Clock()
genbuffer(VAO,GRAPH.p_array)
oldmovement = None
""""""
while Running:

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			Running = False
		
		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 4:
				GRAPH.changeScale(0.1)
			if event.button == 5:
				GRAPH.changeScale(-0.1)

	if pygame.mouse.get_pressed()[0] == 1:
		movement = pygame.mouse.get_pos()
		if oldmovement == None:
			oldmovement = movement
		else:
			#print(movement[0]-oldmovement[0],movement[1]-oldmovement[1])
			base_plotX -= (movement[0]-oldmovement[0]) * GRAPH.zoom
			base_plotY -= (movement[1]-oldmovement[1])* GRAPH.zoom
			plotX = base_plotX*GRAPH.zoom - (np.sum(base_plotX)/2 * (GRAPH.zoom-1))
			plotY = base_plotY*GRAPH.zoom - (np.sum(base_plotY)/2 * (GRAPH.zoom-1))
				
			
			GRAPH.update = True
			oldmovement = pygame.mouse.get_pos()
	else:
		oldmovement = None


	if pygame.key.get_pressed()[pygame.K_UP]:
		GRAPH.speed += 0.01
		GRAPH.zoom /= (GRAPH.zoom+1)**GRAPH.speed
		print(f'[ZOOM] {GRAPH.zoom}')
		
		plotX = base_plotX*GRAPH.zoom - (np.sum(base_plotX)/2 * (GRAPH.zoom-1))
		plotY = base_plotY*GRAPH.zoom - (np.sum(base_plotY)/2 * (GRAPH.zoom-1))
	

		GRAPH.update = True
		
	if pygame.key.get_pressed()[pygame.K_DOWN]:
		GRAPH.speed = max(1,GRAPH.speed - 0.01)
		GRAPH.zoom = min(2,GRAPH.zoom * (GRAPH.zoom+1)**GRAPH.speed)

		print(f'[ZOOM] {GRAPH.zoom}')

		plotX = base_plotX*GRAPH.zoom - (np.sum(base_plotX)/2 * (GRAPH.zoom-1))
		plotY = base_plotY*GRAPH.zoom - (np.sum(base_plotY)/2 * (GRAPH.zoom-1))

		
		GRAPH.update = True


	if GRAPH.checkUpdate():
		glUniform2f(scale_loc, (plotX[1]-plotX[0])/width,(plotY[1]-plotY[0])/height)
		glUniform2f(plotX_loc, plotX[0],plotX[1])
		glUniform2f(plotY_loc, plotY[0],plotY[1])
		glUniform1f(iter_loc,25*GRAPH.scale)
		draw(VAO,GRAPH.num_points)
		pygame.display.flip()

	
	clock.tick(75)
	
