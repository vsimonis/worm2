import cv2
import numpy
import time


class CaptureManager( object ):
    def __init__( self, capture, previewWindowManager, 
                  shouldMirrorPreview, debugMode):
        self._capture = capture
        self._d = debugMode
        self._previewWindowManager = previewWindowManager
        self._shouldMirrorPreview = shouldMirrorPreview
        
        if self._d: 
            print '%s\t Mirror Preview: %s' % (time.ctime(time.time()),  str(self._shouldMirrorPreview))
        self._channel = 0
        self._enteredFrame = False
        self._frame = None
        self._imageFilename = None
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

        self._startTime = None
        self._framesElapsed = long(0)
        self._fpsEstimate = None



    @property
    def channel( self ):
        return self._channel


    @channel.setter
    def channel( self, value ):
        if self.channel != value:
            self._channel = value
            self._frame = None


    @property
    def frame( self ): 
        if self._enteredFrame and self._frame is None:
            _, self._frame = self._capture.retrieve( channel = self.channel )
        return self._frame


    @property
    def isWritingImage( self ):
        return self._imageFilename is not None

    @property
    def isWritingVideo( self ):
        return self._videoFilename is not None



    def enterFrame( self ):
        #Capture the next frame, if any
        #Check that previous frame is exited
        assert not self._enteredFrame, \
            'previous enterFrame() has no matching exitFrame()'


        if self._capture is not None:
            self._enteredFrame = self._capture.grab()


    def exitFrame( self ):
        #Draw to window
        #Write to files
        #Release the frame

        #Check whether grabbed frame is retrievable
        # The getter may retrieve and cache the frame

        if self.frame is None: ####IS THIS OK? _FRAME INST
            self._enteredFrame = False
            return

        #Update FPS estimate and related
        if self._framesElapsed == 0:
            self._startTime = time.time()
        else: 
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed / timeElapsed

        self._framesElapsed += 1


        #Draw to the window
        if self._previewWindowManager is not None: 
            if self._shouldMirrorPreview:
                mirroredFrame = numpy.fliplr(self._frame).copy()
                self._previewWindowManager.show(mirroredFrame)
            else: 
                self._previewWindowManager.show(self._frame)


        #Write image file
        if self.isWritingImage: 
            cv2.imwrite(self._imageFilename, self._frame)
            self._imageFilename = None


        #Write to video 
        self._writeVideoFrame()
            
        #Release
        self._frame = None
        self._enteredFrame = False

    def writeImage( self, filename ):
        self._imageFilename = filename


    def startWritingVideo( self, filename, encoding ):
                           #encoding = -1 ):  
                           #encoding = cv2.cv.CV_FOURCC('I', '4', '2', '0') ):
        self._videoFilename = filename
        self._videoEncoding = encoding
        

    def stopWritingVideo ( self ):
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None
        

    def _writeVideoFrame( self ):
        if not self.isWritingVideo:
            return

        if self._videoWriter is None:
            fps = self._capture.get( cv2.cv.CV_CAP_PROP_FPS ) 

            if fps <= 0.0:
                if self._framesElapsed < 20: 
                    # wait for more frames to get good estimate
                    return
                else: 
                    fps = self._fpsEstimate

            print 'fps: %d' % fps
            size = ( int( self._capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH) ),
                     int( self._capture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT) ) )
            print 'size: %d %d' % (size[0] , size[1] )
            

            self._videoWriter = cv2.VideoWriter( self._videoFilename, 
                                                 self._videoEncoding, fps, size )
            
        self._videoWriter.write(self._frame)






class WindowManager ( object ):
    
    def __init__( self, windowName, keypressCallback = None):
        self.keypressCallback = keypressCallback
        self._windowName = windowName
        self._isWindowCreated = False



    @property
    def isWindowCreated ( self ):
        return self._isWindowCreated

    def createWindow ( self ):
        cv2.namedWindow( self._windowName )
        self._isWindowCreated = True 

    def show ( self, frame ):
        cv2.imshow( self._windowName, frame )
    
        
    def destroyWindow ( self ):
        cv2.destroyWindow( self._windowName ) 
        self._isWindowCreated = False


    def processEvents ( self ):
        keycode = cv2.waitKey( 1 )
        
        if self.keypressCallback is not None and keycode != -1:
            #Discard non-ASCII info encoded by GTK
            keycode &= 0xFF
            self.keypressCallback(keycode)

        
