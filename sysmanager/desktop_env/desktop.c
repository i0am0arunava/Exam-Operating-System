/*
 * desktop.c - Minimal Desktop Environment for Linux (X11)
 *
 * Provides: root window background, taskbar, window focus,
 * basic mouse-driven window moving, and a simple app launcher.
 *
 * Build: see Makefile (requires libX11, libXft, libXinerama)
 */

#include "desktop.h"

/* ── Globals ──────────────────────────────────────────── */
static Display    *dpy;
static Window      root;
static int         screen;
static unsigned int sw, sh;          /* screen width / height */
static GC          gc;
static XftDraw    *xft_draw;
static XftFont    *font;
static XftColor    col_fg, col_bg, col_bar, col_sel;

static ClientList  clients;
static Client     *focused = NULL;

static Taskbar     bar;
static int         running = 1;

/* ── Entry point ──────────────────────────────────────── */
int main(void) {
    setup();
    run();
    cleanup();
    return 0;
}

/* ── Setup ────────────────────────────────────────────── */
void setup(void) {
    dpy = XOpenDisplay(NULL);
    if (!dpy) die("Cannot open display");

    screen = DefaultScreen(dpy);
    root   = RootWindow(dpy, screen);
    sw     = DisplayWidth(dpy, screen);
    sh     = DisplayHeight(dpy, screen);

    /* Become the window manager — grab SubstructureRedirect on root */
    XSetErrorHandler(xerror);
    XSelectInput(dpy, root,
        SubstructureRedirectMask | SubstructureNotifyMask |
        ButtonPressMask | PointerMotionMask | PropertyChangeMask);
    XSync(dpy, False);

    /* Graphics context */
    gc = XCreateGC(dpy, root, 0, NULL);

    /* Fonts & colors via Xft */
    font = XftFontOpenName(dpy, screen, FONT_NAME);
    if (!font) die("Cannot load font");

    alloc_color(&col_fg,  COL_FG);
    alloc_color(&col_bg,  COL_BG);
    alloc_color(&col_bar, COL_BAR);
    alloc_color(&col_sel, COL_SEL);

    /* Set root background */
    XSetWindowBackground(dpy, root, col_bg.pixel);
    XClearWindow(dpy, root);

    /* Taskbar */
    bar.win = XCreateSimpleWindow(dpy, root,
                  0, sh - BAR_HEIGHT, sw, BAR_HEIGHT,
                  0, col_bar.pixel, col_bar.pixel);
    XSelectInput(dpy, bar.win, ExposureMask | ButtonPressMask);
    XMapWindow(dpy, bar.win);
    bar.xft = XftDrawCreate(dpy, bar.win,
                  DefaultVisual(dpy, screen),
                  DefaultColormap(dpy, screen));
    draw_taskbar();

    /* Grab Alt+F2 for launcher, Alt+F4 to close */
    grab_keys();

    XSync(dpy, False);
    fprintf(stderr, "desktop: started (%ux%u)\n", sw, sh);
}

/* ── Main event loop ──────────────────────────────────── */
void run(void) {
    XEvent ev;
    while (running) {
        XNextEvent(dpy, &ev);
        switch (ev.type) {
            case MapRequest:        handle_map_request(&ev);    break;
            case UnmapNotify:       handle_unmap(&ev);          break;
            case DestroyNotify:     handle_destroy(&ev);        break;
            case ConfigureRequest:  handle_configure(&ev);      break;
            case ButtonPress:       handle_button_press(&ev);   break;
            case MotionNotify:      handle_motion(&ev);         break;
            case KeyPress:          handle_key_press(&ev);      break;
            case Expose:            handle_expose(&ev);         break;
            case EnterNotify:       handle_enter(&ev);          break;
            default: break;
        }
    }
}

/* ── Window management ────────────────────────────────── */
void handle_map_request(XEvent *e) {
    XMapRequestEvent *ev = &e->xmaprequest;

    /* Ignore taskbar */
    if (ev->window == bar.win) return;

    Client *c = find_client(ev->window);
    if (!c) {
        c = calloc(1, sizeof(Client));
        if (!c) die("OOM");
        c->win = ev->window;

        /* Default geometry */
        XWindowAttributes wa;
        XGetWindowAttributes(dpy, ev->window, &wa);
        c->x = wa.x ? wa.x : 50;
        c->y = wa.y ? wa.y : 50;
        c->w = wa.width  ? wa.width  : 600;
        c->h = wa.height ? wa.height : 400;

        get_window_title(c);

        /* Add frame border */
        XSetWindowBorderWidth(dpy, ev->window, BORDER_WIDTH);
        XSetWindowBorder(dpy, ev->window, col_fg.pixel);

        XSelectInput(dpy, ev->window,
            EnterWindowMask | FocusChangeMask | PropertyChangeMask);

        /* Append to client list */
        c->next = NULL;
        if (!clients.head) {
            clients.head = c;
        } else {
            Client *t = clients.head;
            while (t->next) t = t->next;
            t->next = c;
        }
        clients.count++;
    }

    XMoveResizeWindow(dpy, c->win, c->x, c->y, c->w, c->h);
    XMapWindow(dpy, c->win);
    focus_client(c);
    draw_taskbar();
}

void handle_unmap(XEvent *e) {
    Client *c = find_client(e->xunmap.window);
    if (!c) return;
    if (focused == c) focused = NULL;
    remove_client(c);
    draw_taskbar();
}

void handle_destroy(XEvent *e) {
    Client *c = find_client(e->xdestroywindow.window);
    if (!c) return;
    if (focused == c) focused = NULL;
    remove_client(c);
    draw_taskbar();
}

void handle_configure(XEvent *e) {
    XConfigureRequestEvent *ev = &e->xconfigurerequest;
    XWindowChanges wc = {
        .x = ev->x, .y = ev->y,
        .width = ev->width, .height = ev->height,
        .border_width = BORDER_WIDTH,
        .sibling = ev->above, .stack_mode = ev->detail
    };
    XConfigureWindow(dpy, ev->window, ev->value_mask, &wc);

    Client *c = find_client(ev->window);
    if (c) {
        c->x = ev->x; c->y = ev->y;
        c->w = ev->width; c->h = ev->height;
    }
}

/* ── Mouse: move windows by dragging ─────────────────── */
static int drag_active = 0;
static int drag_ox, drag_oy;   /* click offset inside window */
static Client *drag_client = NULL;

void handle_button_press(XEvent *e) {
    XButtonEvent *ev = &e->xbutton;

    /* Taskbar click → raise window */
    if (ev->window == bar.win) {
        taskbar_click(ev->x);
        return;
    }

    Client *c = find_client(ev->window);
    if (!c) return;

    focus_client(c);
    XRaiseWindow(dpy, c->win);

    if (ev->button == Button1) {
        drag_active = 1;
        drag_client = c;
        drag_ox = ev->x;
        drag_oy = ev->y;
        XGrabPointer(dpy, c->win, True,
            PointerMotionMask | ButtonReleaseMask,
            GrabModeAsync, GrabModeAsync, None, None, CurrentTime);
    } else if (ev->button == Button3) {
        /* Right-click: close */
        XEvent ce;
        ce.xclient.type         = ClientMessage;
        ce.xclient.window       = c->win;
        ce.xclient.message_type = XInternAtom(dpy, "WM_PROTOCOLS", True);
        ce.xclient.format       = 32;
        ce.xclient.data.l[0]    = XInternAtom(dpy, "WM_DELETE_WINDOW", True);
        ce.xclient.data.l[1]    = CurrentTime;
        XSendEvent(dpy, c->win, False, NoEventMask, &ce);
    }
}

void handle_motion(XEvent *e) {
    if (!drag_active || !drag_client) return;
    XMotionEvent *ev = &e->xmotion;

    /* Flush to latest motion event */
    while (XCheckTypedEvent(dpy, MotionNotify, e))
        ev = &e->xmotion;

    drag_client->x = ev->x_root - drag_ox;
    drag_client->y = ev->y_root - drag_oy;

    /* Keep within screen */
    if (drag_client->y < 0) drag_client->y = 0;
    if (drag_client->y + (int)drag_client->h > (int)sh - BAR_HEIGHT)
        drag_client->y = sh - BAR_HEIGHT - drag_client->h;

    XMoveWindow(dpy, drag_client->win, drag_client->x, drag_client->y);

    if (e->type == ButtonRelease) {
        drag_active = 0;
        drag_client = NULL;
        XUngrabPointer(dpy, CurrentTime);
    }
}

/* ── Keyboard shortcuts ───────────────────────────────── */
void grab_keys(void) {
    /* Alt+F2: launcher, Alt+F4: close focused, Alt+Q: quit DE */
    XGrabKey(dpy, XKeysymToKeycode(dpy, XK_F2),  Mod1Mask, root, True, GrabModeAsync, GrabModeAsync);
    XGrabKey(dpy, XKeysymToKeycode(dpy, XK_F4),  Mod1Mask, root, True, GrabModeAsync, GrabModeAsync);
    XGrabKey(dpy, XKeysymToKeycode(dpy, XK_q),   Mod1Mask, root, True, GrabModeAsync, GrabModeAsync);
    XGrabKey(dpy, XKeysymToKeycode(dpy, XK_Tab), Mod1Mask, root, True, GrabModeAsync, GrabModeAsync);
}

void handle_key_press(XEvent *e) {
    XKeyEvent *ev = &e->xkey;
    KeySym sym = XLookupKeysym(ev, 0);

    if (ev->state & Mod1Mask) {
        if (sym == XK_F2)  spawn_launcher();
        if (sym == XK_F4)  close_focused();
        if (sym == XK_q)   running = 0;
        if (sym == XK_Tab) cycle_focus();
    }
}

void spawn_launcher(void) {
    /* Launch xterm as a simple app launcher */
    if (fork() == 0) {
        setsid();
        execlp("xterm", "xterm", NULL);
        execlp("xfce4-terminal", "xfce4-terminal", NULL);
        exit(1);
    }
}

void close_focused(void) {
    if (!focused) return;
    XEvent ce;
    ce.xclient.type         = ClientMessage;
    ce.xclient.window       = focused->win;
    ce.xclient.message_type = XInternAtom(dpy, "WM_PROTOCOLS", True);
    ce.xclient.format       = 32;
    ce.xclient.data.l[0]    = XInternAtom(dpy, "WM_DELETE_WINDOW", True);
    ce.xclient.data.l[1]    = CurrentTime;
    XSendEvent(dpy, focused->win, False, NoEventMask, &ce);
}

void cycle_focus(void) {
    if (!clients.head) return;
    if (!focused) { focus_client(clients.head); return; }

    Client *next = focused->next ? focused->next : clients.head;
    focus_client(next);
    XRaiseWindow(dpy, next->win);
}

/* ── Taskbar ──────────────────────────────────────────── */
void draw_taskbar(void) {
    XftDrawRect(bar.xft, &col_bar, 0, 0, sw, BAR_HEIGHT);

    /* Clock */
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    char clock_str[32];
    strftime(clock_str, sizeof(clock_str), "%H:%M  %a %d %b", tm);
    XftDrawStringUtf8(bar.xft, &col_fg, font,
        sw - 180, BAR_HEIGHT - 6,
        (const FcChar8 *)clock_str, strlen(clock_str));

    /* Window buttons */
    int x = 4;
    for (Client *c = clients.head; c; c = c->next) {
        int active = (c == focused);
        XftColor *bg = active ? &col_sel : &col_bg;
        XftDrawRect(bar.xft, bg, x, 2, TASKBAR_BTN_W, BAR_HEIGHT - 4);
        XftDrawStringUtf8(bar.xft, &col_fg, font,
            x + 4, BAR_HEIGHT - 6,
            (const FcChar8 *)c->title,
            strnlen(c->title, 20));
        x += TASKBAR_BTN_W + 2;
    }
}

void handle_expose(XEvent *e) {
    if (e->xexpose.window == bar.win && e->xexpose.count == 0)
        draw_taskbar();
}

void taskbar_click(int x) {
    int bx = 4;
    for (Client *c = clients.head; c; c = c->next) {
        if (x >= bx && x < bx + TASKBAR_BTN_W) {
            focus_client(c);
            XRaiseWindow(dpy, c->win);
            return;
        }
        bx += TASKBAR_BTN_W + 2;
    }
}

/* ── Focus ────────────────────────────────────────────── */
void focus_client(Client *c) {
    if (focused && focused != c)
        XSetWindowBorder(dpy, focused->win, col_fg.pixel);

    focused = c;
    if (!c) return;

    XSetWindowBorder(dpy, c->win, col_sel.pixel);
    XSetInputFocus(dpy, c->win, RevertToPointerRoot, CurrentTime);
    draw_taskbar();
}

void handle_enter(XEvent *e) {
    Client *c = find_client(e->xcrossing.window);
    if (c && c != focused) focus_client(c);
}

/* ── Helpers ──────────────────────────────────────────── */
Client *find_client(Window w) {
    for (Client *c = clients.head; c; c = c->next)
        if (c->win == w) return c;
    return NULL;
}

void remove_client(Client *c) {
    if (!c) return;
    if (clients.head == c) {
        clients.head = c->next;
    } else {
        for (Client *p = clients.head; p; p = p->next) {
            if (p->next == c) { p->next = c->next; break; }
        }
    }
    clients.count--;
    free(c);
}

void get_window_title(Client *c) {
    char *name = NULL;
    if (XFetchName(dpy, c->win, &name) && name) {
        strncpy(c->title, name, MAX_TITLE - 1);
        XFree(name);
    } else {
        snprintf(c->title, MAX_TITLE, "win-%lu", c->win);
    }
}

void alloc_color(XftColor *col, const char *hex) {
    if (!XftColorAllocName(dpy, DefaultVisual(dpy, screen),
                           DefaultColormap(dpy, screen), hex, col))
        die("Cannot allocate color");
}

int xerror(Display *d, XErrorEvent *e) {
    /* Ignore harmless errors */
    if (e->error_code == BadWindow ||
        (e->request_code == X_SetInputFocus && e->error_code == BadMatch) ||
        (e->request_code == X_PolyText8    && e->error_code == BadDrawable))
        return 0;
    char buf[256];
    XGetErrorText(d, e->error_code, buf, sizeof(buf));
    fprintf(stderr, "desktop: X error: %s\n", buf);
    return 0;
}

void die(const char *msg) {
    fprintf(stderr, "desktop: fatal: %s\n", msg);
    exit(1);
}

void cleanup(void) {
    Client *c = clients.head;
    while (c) {
        Client *next = c->next;
        free(c);
        c = next;
    }
    if (font)     XftFontClose(dpy, font);
    if (bar.xft)  XftDrawDestroy(bar.xft);
    if (xft_draw) XftDrawDestroy(xft_draw);
    XFreeGC(dpy, gc);
    XCloseDisplay(dpy);
}
