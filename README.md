# Raspberry Pi steuert Heizungsanforderung

* don't forget to "chmod 755 heizung.py" so that the programm is executable

To run the program as a "deamon", I decided to use 
supervisor http://supervisord.org. The advantages are awesome: 

* supervisord will start the program automatically - also after reboot 
* take care of restart, if the script exited unexpected!

# Acknowledgment

Thanks to Erik Bartmann for his inspiring Book "Die elektronische Welt mit Raspberry Pi entdecken"
