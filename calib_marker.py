from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter, A4




def create_marker(r, c, size):

    #x0,y0 unten links
    w, h = (297, 210)
    sq = size
    rows = r
    cols = c

    #ordne die höhere Anzahl (Spalte o. Zeile) der längeren Seite (Format) zu
    if cols > rows:
        w, h = h, w
    else:
        pass

    #genutze Breite/Höhe auf Basis der verwendenten Spalten/Zeilen
    used_w  = 2*rows*sq - 2*sq
    used_h  = 2*cols*sq - 2*sq

    #setze x0, y0 auf Basis der genutzen Breite/Höhe und zentriere sie
    x0 = int((w - used_w)/2)
    y0 = int((h - used_h)/2)
    

    if used_w > w or used_h > h:
        return 'verkleinere Marker'

    else:
        print('Marker passt in das Format')

        #Bereite Speichern vor
        filedir  = 'pattern/'
        filename = 'marker'
        fileinfo = '_' + str(rows) +'x'+ str(cols) + '_' + str(sq) + 'mm'
        filetype = '.pdf'
        file = filedir + filename + fileinfo + filetype
        print('Speichere Datei als', file)

        #Bereite Format vor
        c = canvas.Canvas(file, (w*mm, h*mm))
        c.translate(mm,mm)

        c.drawString(5*mm, 5*mm, 'Ansicht @ 100%: Zeilen: ' + str(rows) + ', Spalten: ' + str(cols) +', Durchmesser: ' + str(sq) + 'mm')

        #Füllfarbe
        c.setFillColorRGB(0,0,0)

        
        dx = 0
        dy = 0
        
        
        for i in range(rows):
            dx = 0
            for j in range(cols):
                c.circle((x0+dx)*mm, y0*mm, int(sq/2)*mm, stroke=0, fill=1)
                dx += 2*sq
            y0 += 2*sq


        c.showPage()
        c.save()