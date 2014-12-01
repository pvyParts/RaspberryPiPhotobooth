#!/usr/bin/env python

#**
# HD Photobooth with print capabilities
# Code originaly from https://github.com/contractorwolf/RaspberryPiPhotobooth
#**

from time import sleep

import os
import os.path
import subprocess as sub
import datetime
import pygame
import pygbutton
import glob
import sys
import io
import requests

from sonypy import Discoverer, Camera
fps = 0; #frames per second
photos_taken = 0
index = 0
width = 1920
height = 1080
continue_loop = True

image_name = ""
delay_time = .001
flash_time = .1
last_image_taken = ""
waiting_on_download = False #if this is true, look for last_image_taken 

current_image = 0
in_process = False
image_count = 0;
object_list = [] #list of preloaded images
change_ticks = 0
last_image_number = 0
last_preview = {}

taking_photos = False
photo_count = 1
photos = {"1","2","3","4"}
photo_timer = 0
camera_avail = False

try:
    discoverer = Discoverer()
    cameras = discoverer.discover()
    cam = cameras[0]
    #cam.get_available_api_list()
    cam.start_rec_mode()
    #set_shoot_mode('still')
    cam.start_liveview()
    stream = cam.stream_liveview('http://192.168.122.1:8080/liveview/liveviewstream')
    camera_avail = True
except:
    print "no cam man!"
    
#***************FUNCTIONS******************

def APressed(channel):
    print("A button pressed: " + str(index))
    TakePicture()
    
def BPressed(channel):
    print("B button pressed: " + str(index))    
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000
    

    LastPicture()
    
def CPressed(channel):
    print("C button pressed: " + str(index))   
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000

    PrevPicture()

def DPressed(channel):
    print("D button pressed: " + str(index))    
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000
    
    NextPicture()


def RenderOverlay():
    #drow title and buttons
    
    #app name
    screen.blit(pygame.font.SysFont("freeserif",30,bold=0).render(app_name, 1, white),((width-350),10))

    #button
    take_pic_button.draw(screen)

    #button
    quit_button.draw(screen)

    pygame.display.update()

def LoadImageToObjectList(image_name):
    #load image by filename to the list of image objects for fast switching
    
    global object_list
    global image_count
    global last_image_number
    
    print "LoadImageToObjectList: " + image_name
    print "before load: " + str(pygame.time.get_ticks())
    load = pygame.image.load(image_name).convert_alpha()
    print "loaded: " + str(pygame.time.get_ticks())
    scale = pygame.transform.scale(load,(width,height))
    print "scaled: " + str(pygame.time.get_ticks())
    print "before append"
    object_list.append(scale)


    last_image_number = image_count
    
    image_count = image_count + 1

    
    print "after append" + str(pygame.time.get_ticks())
    print "added to object_list: " + str(len(object_list))
    print "end of LoadImageToObjectList"
    
    pygame.display.update()

    print "sent to google drive: " + image_name

    
def LoadImageObjectToScreen(image):
    #load the image object from the list to the screen
    
    print "begin LoadImageObjectToScreen"
    
    print "before load: " + str(pygame.time.get_ticks())
    screen.blit(image,(0,0))
    print "added to screen: " + str(pygame.time.get_ticks())
    pygame.display.update()
    
    print "end LoadImageObjectToScreen"
    


def DrawMetrics():
    #draws program metrics to the screen, to time how fast updating is going
    #print pygame.time.get_ticks()
    #print index
    fps = float(index)/float(pygame.time.get_ticks()/1000)

    #text background layer, overwritten on every frame
    screen.blit(backgroundSurface,(5,(height-20)))

    #add fps text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("{0:.2f}".format(fps) + " frames per second", 1, white),(10,(height-20)))

    #add index text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("index: " + str(index), 1, white),(300,(height-20)))

    #add photos taken text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("photos taken: " + str(photos_taken), 1, white),(450,(height-20)))# + ":" + str(take_a_picture)
                                                                                            
    pygame.display.update()

def DrawPreview():
    # draws the preview image from the camera onto the screen
    global last_preview
    
    try:
        frame = stream.next()
        img = io.BytesIO(frame)
        image = pygame.image.load(img).convert_alpha()

        #position lower right preview image
        screen.blit(image,((width-640),(height - 424)))
        pygame.display.update()
        last_preview = image#stores last to make transitions look less choppy 
        
    except:
        print "no new picture"
        
def PrevPicture():
    #draws the prev picture in the list from the object list
    global current_image
    global in_process
    print "PrevPicture"

    if not in_process:
        in_process = True
        current_image = current_image - 1
        if current_image < 0:
            current_image = (len(object_list)-1)

        DrawCenterMessage("LOADING PREV IMAGE: " + str(current_image),550,70,((width/2)-220),((height)-100))
        LoadImageObjectToScreen(object_list[current_image])
        #RenderOverlay()
        in_process = False

    print "end PrevPicture"

def NextPicture():
    #draws the prev picture in the list from the object list
    global current_image
    global in_process
    print "NextPicture"

    if not in_process:
        in_process = True
        current_image = current_image + 1
        if current_image > (len(object_list)-1):
            current_image = 0
            
        DrawCenterMessage("LOADING NEXT IMAGE: " + str(current_image),550,70,((width/2)-220),((height)-100))
        LoadImageObjectToScreen(object_list[current_image])
        if camera_avail:
            screen.blit(last_preview,((width-320),(height - 240)))
        
        #RenderOverlay()
        in_process = False

    print "end NextPicture"

def LastPicture():
    #draws the last picture in the list to the screen
    global current_image
    global in_process

    print "LastPicture"

    if not in_process:
        in_process = True
        DrawCenterMessage("LOADING LAST TAKEN: " +str(last_image_number),600,70,((width/2)-220),((height)-100))
        LoadImageObjectToScreen(object_list[last_image_number])
        #RenderOverlay()
        in_process = False
    
    print "end LastPicture"


def DrawCenterMessage(message,width,height,x,y):
    #displays notification messages onto the screen

    backgroundCenterSurface = pygame.Surface((width,height))#size
    backgroundCenterSurface.fill(black)

    screen.blit(backgroundCenterSurface,(x,y))#position
    screen.blit(pygame.font.SysFont("freeserif",40,bold=1).render(message, 1, white),(x+10,y+10))
    pygame.display.update()
    

def LoadNewImage():
    # after new image has been downloaded from the camera
    # it must be loaded into the object list and displayed on the screen
    global waiting_on_download
    global image_count
    global last_image_number
    global current_image

    DrawCenterMessage("TRANFERRING PICTURE",550,70,((width/2)-220),((height/2)-2))

    print "start LoadNewImage: " + str(pygame.time.get_ticks())
    capture = pygame.transform.scale(pygame.image.load(last_image_taken).convert_alpha(),(width,height))
    print "capture transformed: " + str(pygame.time.get_ticks())

    DrawCenterMessage("LOADING IMAGE",550,70,((width/2)-220),((height/2)-2))
    
    screen.blit(capture,(0,0))
    object_list.append(capture)

    last_image_number = image_count
    current_image = last_image_number
    image_count = image_count + 1

    print "capture added to screen: " + str(pygame.time.get_ticks())

    #-------------------------------------------------------------
    # ONLY UNCOMMENT THE NEXT LINE OF CODE IF YOU HAVE CONFIGURED 
    # upload.py TO WORK WITH YOUR GOOGLE DRIVE ACCOUNT
    #os.system("sudo python upload.py " + last_image_taken)
    #-------------------------------------------------------------
    
    waiting_on_download = False
        

def TakePicture():
    # executes the gphoto2 command to take a photo and download it from the camera
    global change_ticks
    global take_a_picture
    global photos_taken
    global last_image_taken
    global waiting_on_download

    take_a_picture = False
    
    print "taking picture"

    #DrawCenterMessage("SMILE :)",400,70,((width/2)-220),((height/2)-2))

    #starts looking for the saved downloading image name
    waiting_on_download = True
    imageURL = cam.act_take_picture()[0]
    print os.path.basename(imageURL)
    
    r = requests.get(imageURL, stream=True)
    if r.status_code == 200:
        with open('Pictures/'+os.path.basename(imageURL), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    
    photos_taken = photos_taken + 1
    last_image_taken = 'Pictures/'+os.path.basename(imageURL)
    
    change_ticks = pygame.time.get_ticks() + 5000 #sets a 30 second timeout before the slideshow continues
    

#***************END FUNCTIONS******************

# drops other possible connections to the camera
# on every restart just to be safe

#os.system("sudo pkill gvfs")
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

app_name = "Photobooth"

print app_name + " started"

sleep(2)

white = pygame.Color(255,255,255)
black = pygame.Color(0,0,0)

pygame.init()
infoOb = pygame.display.Info()
pygame.display.set_caption(app_name)

screen = pygame.display.set_mode((infoOb.current_w,infoOb.current_h),pygame.FULLSCREEN)#FULLSCREEN
height = pygame.display.get_surface().get_height()
width = pygame.display.get_surface().get_width()

#button
take_pic_button = pygbutton.PygButton(((width/2),50,(width/2),30), "take pic")

#button
quit_button = pygbutton.PygButton((0,50,(width/2),30), "quit")


#bottom level, to cover previous frames
backgroundSurface = pygame.Surface(((width-650),28))
backgroundSurface.fill(black)

#bottom level, to cover previous frames
backgroundCenterSurface = pygame.Surface((400,70))#size
backgroundCenterSurface.fill(black)

get_preview_command = "http://192.168.122.1:8080/liveview/liveviewstream"

DrawPreview()

file_list = glob.glob("pictures/*.jpg")

print "files in folder: " + str(len(file_list))

index = 1
for file in file_list:
    print file
    DrawCenterMessage("LOADING: " + str(index + 1) + "/" +str(len(file_list)),500,70,((width/2)-220),((height)-100))
    #REMOVE THIS RESTRICTION AFTER TESTING
    if index < 20: #REMOVE LATER<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        LoadImageToObjectList(file)
        NextPicture()    
    index = index+1

print "START LOOP"
sleep(2)

while(continue_loop):

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print "quiting..."
            continue_loop = False

        if 'click' in take_pic_button.handleEvent(event) and camera_avail:
            #TakePicture()
            photo_timer = pygame.time.get_ticks() + 5000
            taking_photos = True
            
        if 'click' in quit_button.handleEvent(event):
            print "quiting..."
            continue_loop = False

    if waiting_on_download and os.path.isfile(last_image_taken):
        print "found file: " + last_image_taken
        LoadNewImage()

    if change_ticks  < pygame.time.get_ticks():
        print "Change"
        NextPicture()
        change_ticks = pygame.time.get_ticks() + 5000 #10 seconds and then flip to the next image

    if taking_photos:
        time = abs(((photo_timer-pygame.time.get_ticks())+1000)/1000)
        if time > 0:
            DrawCenterMessage(str(photo_count) + " of 4" + "   Smile!   " + str(time) + " ",600,70,((width/2)-220),((height)-100))
        else:
            DrawCenterMessage(str(photo_count) + " of 4" + "   Smile!   ",600,70,((width/2)-220),((height)-100))

        if photo_timer < pygame.time.get_ticks():
            print "taking photo %s" % photo_count
            photo_timer = pygame.time.get_ticks() + 5000
            TakePicture()
            photo_count += 1
            
        if photo_count > 4:
            photo_count = 1
            taking_photos = False
            # TODO asemble photos and show and output to printer

    #preview
    if camera_avail:
        DrawPreview()
        
    #DrawMetrics()
    RenderOverlay()
    index = index +1
    sleep(delay_time)

print "process complete"
pygame.quit()
#GPIO.cleanup()
