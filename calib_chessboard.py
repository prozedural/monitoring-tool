from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter, A4




def create_chessboard(r, c, size):
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
    used_w  = 2*rows*sq - sq
    used_h  = 2*cols*sq - sq

    #setze x0, y0 auf Basis der genutzen Breite/Höhe und zentriere sie
    x0 = int((w - used_w)/2)
    y0 = int((h - used_h)/2)
    

    if used_w > w or used_h > h:
        return 'verkleinere Schachbrettmuster'

    else:
        print('Schachbrettmuster passt in das Format')

        filedir  = 'pattern/'
        filename = 'chessboard'
        fileinfo = '_' + str(rows) +'x'+ str(cols) + '_' + str(sq) + 'mm'
        filetype = '.pdf'
        file = filedir + filename + fileinfo + filetype
        print('Speichere Datei als', file)


        c = canvas.Canvas(file, (w*mm, h*mm))
        c.translate(mm,mm)

        c.drawString(5*mm, 5*mm, 'Ansicht @ 100%: Zeilen: ' + str(rows) + ', Spalten: ' + str(cols) +', Quadrat: ' + str(sq) + 'mm')

        #base color
        c.setFillColorRGB(0,0,0)



        #draw outer squares
        dx = 0
        dy = 0
        for i in range(rows):
            for j in range(cols):
                c.rect((x0+dx)*mm, (y0+dy)*mm, sq*mm, sq*mm,  stroke=0, fill=1)
                dy += 2*sq
            dy = 0
            dx += 2*sq


        #draw inner squares
        dx = sq
        dy = sq
        for i in range(rows-1):
            for j in range(cols-1):
                c.rect((x0+dx)*mm, (y0+dy)*mm, sq*mm, sq*mm, stroke=0, fill=1)
                dy += 2*sq
            dy = sq
            dx += 2*sq


        c.showPage()
        c.save()