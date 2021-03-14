#this class generate the buttons for the drum pad

class button():
    def __init__(self, color, x,y,width,height):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    

    def draw(self,win,outline=None):
        #Call this method to draw the button on the screen
        if outline:
            pygame.draw.rect(win, outline, (self.x-2,self.y-2,self.width+4,self.height+4),0)
            
        pygame.draw.rect(win, self.color, (self.x,self.y,self.width,self.height),0)
        
    

    def isOver(self, pos):
        #Pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                return True
            
        return False


button=button(green,0,0,20,20)

button.draw()
        