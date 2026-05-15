/*
 * desktop.h - Minimal Desktop Environment Header
 */

#ifndef DESKTOP_H
#define DESKTOP_H

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/keysym.h>
#include <X11/Xproto.h>
#include <X11/extensions/Xinerama.h>
#include <X11/Xft/Xft.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/wait.h>

/* ── Configuration ────────────────────────────────────── */
#define FONT_NAME       "monospace:size=11"
#define COL_BG          "#1a1a2e"    /* root background  */
#define COL_FG          "#e0e0e0"    /* text / border    */
#define COL_BAR         "#16213e"    /* taskbar          */
#define COL_SEL         "#0f3460"    /* focused window   */

#define BAR_HEIGHT      24
#define BORDER_WIDTH    2
#define TASKBAR_BTN_W   140
#define MAX_TITLE       64

/* ── Structures ───────────────────────────────────────── */
typedef struct Client Client;
struct Client {
    Window  win;
    int     x, y;
    unsigned int w, h;
    char    title[MAX_TITLE];
    Client *next;
};

typedef struct {
    Client *head;
    int     count;
} ClientList;

typedef struct {
    Window   win;
    XftDraw *xft;
} Taskbar;

/* ── Function prototypes ──────────────────────────────── */
void setup(void);
void run(void);
void cleanup(void);
void die(const char *msg);

/* Event handlers */
void handle_map_request(XEvent *e);
void handle_unmap(XEvent *e);
void handle_destroy(XEvent *e);
void handle_configure(XEvent *e);
void handle_button_press(XEvent *e);
void handle_motion(XEvent *e);
void handle_key_press(XEvent *e);
void handle_expose(XEvent *e);
void handle_enter(XEvent *e);

/* Window management */
void focus_client(Client *c);
void cycle_focus(void);
void close_focused(void);
Client *find_client(Window w);
void remove_client(Client *c);
void get_window_title(Client *c);

/* Taskbar */
void draw_taskbar(void);
void taskbar_click(int x);

/* Keyboard */
void grab_keys(void);
void spawn_launcher(void);

/* Utilities */
void alloc_color(XftColor *col, const char *hex);
int  xerror(Display *d, XErrorEvent *e);

#endif /* DESKTOP_H */
