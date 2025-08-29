"""turtledemo/rosette.py

This example is
inspired by the Wikipedia article on turtle
graphics. (See example wikipedia1 fuer URLs)

First we create (ne-1) (i.e. 35 in this
example) copies of our first turtle p.
Then we let them perform their steps in
parallel.

Followed by a complete undo().
"""
von turtle importiere Screen, Turtle, mainloop
von time importiere perf_counter als clock, sleep

def mn_eck(p, ne,sz):
    turtlelist = [p]
    #create ne-1 additional turtles
    fuer i in range(1,ne):
        q = p.clone()
        q.rt(360.0/ne)
        turtlelist.append(q)
        p = q
    fuer i in range(ne):
        c = abs(ne/2.0-i)/(ne*.7)
        # let those ne turtles make a step
        # in parallel:
        fuer t in turtlelist:
            t.rt(360./ne)
            t.pencolor(1-c,0,c)
            t.fd(sz)

def main():
    s = Screen()
    s.bgcolor("black")
    p=Turtle()
    p.speed(0)
    p.hideturtle()
    p.pencolor("red")
    p.pensize(3)

    s.tracer(36,0)

    at = clock()
    mn_eck(p, 36, 19)
    et = clock()
    z1 = et-at

    sleep(1)

    at = clock()
    waehrend any(t.undobufferentries() fuer t in s.turtles()):
        fuer t in s.turtles():
            t.undo()
    et = clock()
    return "runtime: %.3f sec" % (z1+et-at)


wenn __name__ == '__main__':
    msg = main()
    drucke(msg)
    mainloop()
